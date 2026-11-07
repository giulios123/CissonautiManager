"""Read models behind the admin views: who is present, and what needs a look."""

from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.booking import effective_status, occupies_seats
from app.domain.payments_review import (
    COLLECT_WAITING,
    REASON_LABELS,
    collect_group,
    review_reason,
)
from app.domain.presence import Presence, presences
from app.domain.report import (
    ActivityFacts,
    BookingFacts,
    EditionFacts,
    EditionReport,
    PaymentFacts,
    WaitlistFacts,
    edition_report,
)
from app.i18n import tr
from app.models import (
    Activity,
    Booking,
    Edition,
    Slot,
    WaitlistEntry,
    slot_sort_key,
)
from app.services import edition as edition_service
from app.services.payments import active_payments, paid_total
from app.services.seats import expire_overdue


@dataclass(frozen=True)
class Person:
    participant_id: int
    booking_id: int
    first_name: str
    last_name: str
    email: str
    status: str


@dataclass
class PresenceData:
    edition: Edition | None = None
    slots: list[Slot] = field(default_factory=list)
    rows: list[Presence] = field(default_factory=list)
    people: dict[int, Person] = field(default_factory=dict)


def load_presence(db: Session, now: datetime) -> PresenceData:
    """Presences of the active edition: only bookings that occupy seats, derived evenings included.

    Expired holds, requested cancellations and refunds are left out, as they are for seat counts.
    """
    edition = edition_service.get_active_edition(db)
    if edition is None:
        return PresenceData()
    expire_overdue(db, now)
    db.commit()
    people: dict[int, Person] = {}
    booked: list[tuple[int, date, str]] = []
    bookings = db.scalars(select(Booking).where(Booking.edition_id == edition.id)).all()
    for booking in bookings:
        status = effective_status(booking.status, booking.hold_expires_at, now)
        if not occupies_seats(status):
            continue
        participant = booking.participant
        people[participant.id] = Person(
            participant_id=participant.id,
            booking_id=booking.id,
            first_name=participant.first_name,
            last_name=participant.last_name,
            email=participant.email,
            status=status,
        )
        booked.extend((participant.id, s.date, s.period) for s in booking.slots)
    return PresenceData(
        edition=edition,
        slots=sorted(edition.slots, key=slot_sort_key),
        rows=presences(booked),
        people=people,
    )


@dataclass(frozen=True)
class ReviewRow:
    booking_id: int
    first_name: str
    last_name: str
    email: str
    personal_code: str
    status: str
    amount_due_cents: int
    paid_cents: int
    reason: str

    @property
    def balance_cents(self) -> int:
        return self.amount_due_cents - self.paid_cents

    @property
    def reason_label(self) -> str:
        return tr(REASON_LABELS[self.reason])


def review_rows(db: Session, now: datetime) -> list[ReviewRow]:
    """Bookings that need an admin's attention about money, most urgent kind of case first.

    A booking drops out of the list on its own once the problem is solved (balance settled,
    refund recorded), because the reason is recomputed on every read.
    """
    edition = edition_service.get_active_edition(db)
    if edition is None:
        return []
    expire_overdue(db, now)
    db.commit()
    rows: list[ReviewRow] = []
    for booking in db.scalars(select(Booking).where(Booking.edition_id == edition.id)):
        status = effective_status(booking.status, booking.hold_expires_at, now)
        paid = paid_total(booking)
        reason = review_reason(status, booking.amount_due_cents, paid)
        if reason is None:
            continue
        participant = booking.participant
        rows.append(
            ReviewRow(
                booking_id=booking.id,
                first_name=participant.first_name,
                last_name=participant.last_name,
                email=participant.email,
                personal_code=participant.personal_code,
                status=status,
                amount_due_cents=booking.amount_due_cents,
                paid_cents=paid,
                reason=reason,
            )
        )
    order = list(REASON_LABELS)
    rows.sort(key=lambda r: (order.index(r.reason), r.last_name.lower(), r.first_name.lower()))
    return rows


@dataclass(frozen=True)
class CollectRow:
    booking_id: int
    first_name: str
    last_name: str
    email: str
    personal_code: str
    status: str
    amount_due_cents: int
    paid_cents: int
    hold_expires_at: datetime

    @property
    def balance_cents(self) -> int:
        return self.amount_due_cents - self.paid_cents


def collect_rows(db: Session, now: datetime) -> list[CollectRow]:
    """Bookings with money still to come, to be ticked off against the bank account.

    Waiting ones first, the nearest deadline first; then confirmed ones with a balance; then
    expired ones, whose transfer may still arrive late. Each group is by surname.
    """
    edition = edition_service.get_active_edition(db)
    if edition is None:
        return []
    expire_overdue(db, now)
    db.commit()
    keyed: list[tuple[tuple, CollectRow]] = []
    bookings = db.scalars(
        select(Booking)
        .where(Booking.edition_id == edition.id)
        .options(selectinload(Booking.participant), selectinload(Booking.payments))
    )
    for booking in bookings:
        status = effective_status(booking.status, booking.hold_expires_at, now)
        paid = paid_total(booking)
        group = collect_group(status, booking.amount_due_cents, paid)
        if group is None:
            continue
        participant = booking.participant
        row = CollectRow(
            booking_id=booking.id,
            first_name=participant.first_name,
            last_name=participant.last_name,
            email=participant.email,
            personal_code=participant.personal_code,
            status=status,
            amount_due_cents=booking.amount_due_cents,
            paid_cents=paid,
            hold_expires_at=booking.hold_expires_at,
        )
        deadline = booking.hold_expires_at.timestamp() if group == COLLECT_WAITING else 0
        keyed.append(
            ((group, deadline, row.last_name.lower(), row.first_name.lower(), row.booking_id), row)
        )
    keyed.sort(key=lambda pair: pair[0])
    return [row for _, row in keyed]


@dataclass(frozen=True)
class MealRow:
    booking_id: int
    first_name: str
    last_name: str
    email: str
    day: date
    kind: str
    diet: str | None
    allergies: str | None


@dataclass
class MealData:
    days: list[date] = field(default_factory=list)
    rows: list[MealRow] = field(default_factory=list)


def load_meals(db: Session, now: datetime) -> MealData:
    """Meals of the active edition, only for bookings that occupy seats, with dietary needs.

    Allergies are health data: this is for the admin views only.
    """
    edition = edition_service.get_active_edition(db)
    if edition is None:
        return MealData()
    expire_overdue(db, now)
    db.commit()
    rows: list[MealRow] = []
    for booking in db.scalars(select(Booking).where(Booking.edition_id == edition.id)):
        if not occupies_seats(effective_status(booking.status, booking.hold_expires_at, now)):
            continue
        participant = booking.participant
        rows.extend(
            MealRow(
                booking_id=booking.id,
                first_name=participant.first_name,
                last_name=participant.last_name,
                email=participant.email,
                day=meal.date,
                kind=meal.kind,
                diet=booking.diet,
                allergies=booking.allergies,
            )
            for meal in booking.meals
        )
    rows.sort(key=lambda r: (r.day, r.kind != "lunch", r.last_name.lower(), r.first_name.lower()))
    return MealData(days=sorted({s.date for s in edition.slots}), rows=rows)


@dataclass(frozen=True)
class ContributionRow:
    id: int
    kind: str
    title: str
    description: str | None
    booking_id: int
    first_name: str
    last_name: str
    email: str
    status: str
    active: bool
    created_at: datetime


def contribution_rows(db: Session, now: datetime, kind: str | None = None) -> list[ContributionRow]:
    """Contributions of the active edition. Those of bookings that no longer occupy seats are
    kept and flagged: the proposal can still be useful."""
    edition = edition_service.get_active_edition(db)
    if edition is None:
        return []
    expire_overdue(db, now)
    db.commit()
    rows: list[ContributionRow] = []
    for booking in db.scalars(select(Booking).where(Booking.edition_id == edition.id)):
        status = effective_status(booking.status, booking.hold_expires_at, now)
        participant = booking.participant
        for contribution in booking.contributions:
            if kind and contribution.kind != kind:
                continue
            rows.append(
                ContributionRow(
                    id=contribution.id,
                    kind=contribution.kind,
                    title=contribution.title,
                    description=contribution.description,
                    booking_id=booking.id,
                    first_name=participant.first_name,
                    last_name=participant.last_name,
                    email=participant.email,
                    status=status,
                    active=occupies_seats(status),
                    created_at=contribution.created_at,
                )
            )
    rows.sort(key=lambda r: (not r.active, r.created_at, r.id))
    return rows


def activity_signup_days(db: Session, now: datetime) -> list[date]:
    """One day per sign-up to an activity, for bookings that occupy seats."""
    edition = edition_service.get_active_edition(db)
    if edition is None:
        return []
    days: list[date] = []
    for booking in db.scalars(select(Booking).where(Booking.edition_id == edition.id)):
        if occupies_seats(effective_status(booking.status, booking.hold_expires_at, now)):
            days.extend(activity.date for activity in booking.activities)
    return days


@dataclass
class ReportData:
    edition: Edition | None
    report: EditionReport


def load_report(db: Session, now: datetime) -> ReportData:
    """The numbers of the active edition, read the way the other admin views read them (expiry
    evaluated now, voided payments out), so that the report agrees with them."""
    edition = edition_service.get_active_edition(db)
    if edition is None:
        empty = EditionFacts((), 0, 0, 0, 0)
        return ReportData(None, edition_report(empty, [], [], [], []))
    expire_overdue(db, now)
    db.commit()
    bookings: list[BookingFacts] = []
    payments: list[PaymentFacts] = []
    # The report reads five collections of every booking: load them in bulk, not one by one.
    everything = (
        selectinload(Booking.payments),
        selectinload(Booking.slots),
        selectinload(Booking.meals),
        selectinload(Booking.activities),
        selectinload(Booking.contributions),
    )
    for booking in db.scalars(
        select(Booking).where(Booking.edition_id == edition.id).options(*everything)
    ):
        status = effective_status(booking.status, booking.hold_expires_at, now)
        bookings.append(
            BookingFacts(
                booking_id=booking.id,
                person_id=booking.participant_id,
                status=status,
                amount_due_cents=booking.amount_due_cents,
                paid_cents=paid_total(booking),
                refund_cents=booking.refund_cents or 0,
                slots=tuple((s.date, s.period) for s in booking.slots),
                meals=tuple((m.date, m.kind) for m in booking.meals),
                activity_ids=tuple(a.id for a in booking.activities),
                diet=booking.diet,
                has_allergies=bool((booking.allergies or "").strip()),
                contributions=tuple(c.kind for c in booking.contributions),
            )
        )
        payments.extend(PaymentFacts(p.channel, p.amount_cents) for p in active_payments(booking))
    activities = [
        ActivityFacts(a.id, a.title, a.date, a.period, a.price_cents, a.capacity, a.payment_mode)
        for a in db.scalars(select(Activity).where(Activity.edition_id == edition.id))
    ]
    waitlist = [
        WaitlistFacts(entry.close_reason, entry.promoted_as_plus_one)
        for entry in db.scalars(
            select(WaitlistEntry)
            .join(Slot, Slot.id == WaitlistEntry.slot_id)
            .where(Slot.edition_id == edition.id)
        )
    ]
    facts = EditionFacts(
        slots=tuple((s.date, s.period) for s in edition.slots),
        base_fee_cents=edition.base_fee_cents,
        per_day_fee_cents=edition.per_day_fee_cents,
        lunch_price_cents=edition.lunch_price_cents,
        dinner_price_cents=edition.dinner_price_cents,
        meal_terms={
            (m.date, m.kind): (
                m.price_cents
                if m.price_cents is not None
                else (
                    edition.lunch_price_cents if m.kind == "lunch" else edition.dinner_price_cents
                ),
                m.payment_mode,
            )
            for m in edition.meal_settings
        },
    )
    return ReportData(edition, edition_report(facts, bookings, activities, waitlist, payments))
