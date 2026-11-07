"""The edition report: the numbers an organizer wants at the end. Pure functions, no database.

The caller reads the facts (bookings with their effective status, payments without the voided
ones, waitlist entries) and this module only counts. Presence, meals and activities count the
bookings that occupy seats (confirmed and pending), kept apart so that the report shows who is
sure and who is still to pay. Money counts everything that was paid, refunded or is still owed.
"""

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date

from app.domain.booking import occupies_seats
from app.domain.collection import collectable
from app.domain.confirmation import POLICY_LEGACY_TOTAL, confirmation_due_cents
from app.domain.fees import compute_fee
from app.domain.meals import NO_DIET
from app.domain.presence import presences
from app.models import (
    CLOSE_BOOKED,
    CLOSE_CANCELLED,
    CLOSE_LEFT,
    CLOSE_PROMOTED,
    CLOSE_REMOVED,
    CONTRIBUTION_KINDS,
    DIETS,
    MEAL_DINNER,
    MEAL_LUNCH,
    PERIOD_AFTERNOON,
    PERIOD_EVENING,
    PERIOD_MORNING,
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    STATUS_REFUNDED,
)

ALL_STATUSES = (
    STATUS_CONFIRMED,
    STATUS_PENDING,
    STATUS_EXPIRED,
    STATUS_CANCEL_REQUESTED,
    STATUS_REFUNDED,
)
PERIODS = (PERIOD_MORNING, PERIOD_AFTERNOON, PERIOD_EVENING)


@dataclass(frozen=True)
class BookingFacts:
    booking_id: int
    person_id: int
    status: str  # the effective status: a pending booking past its deadline is already expired
    amount_due_cents: int
    paid_cents: int  # voided payments are not counted
    refund_cents: int  # 0 when nothing was refunded
    slots: tuple[tuple[date, str], ...]  # (day, period)
    meals: tuple[tuple[date, str], ...]  # (day, kind)
    activity_ids: tuple[int, ...]
    diet: str | None
    has_allergies: bool
    contributions: tuple[str, ...]  # kinds
    registration_fee_cents: int | None = None


@dataclass(frozen=True)
class ActivityFacts:
    id: int
    title: str
    day: date
    period: str
    price_cents: int
    capacity: int | None
    payment_mode: str = "organizer"


@dataclass(frozen=True)
class WaitlistFacts:
    close_reason: str | None  # None while the entry is still waiting
    plus_one: bool  # the person was a verified +1 when the seat was given to them


@dataclass(frozen=True)
class PaymentFacts:
    channel: str
    amount_cents: int  # voided payments are left out by the caller


@dataclass(frozen=True)
class EditionFacts:
    slots: tuple[tuple[date, str], ...]  # every slot of the edition, booked or not
    base_fee_cents: int
    per_day_fee_cents: int
    lunch_price_cents: int
    dinner_price_cents: int
    meal_terms: dict[tuple[date, str], tuple[int, str]] = field(default_factory=dict)
    confirmation_policy: str = POLICY_LEGACY_TOTAL


@dataclass(frozen=True)
class Split:
    """A count split by how sure the booking is."""

    confirmed: int = 0
    pending: int = 0
    # A field and not a property, so that it travels with the others when the report is sent.
    total: int = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "total", self.confirmed + self.pending)


@dataclass(frozen=True)
class EnrollmentSection:
    by_status: dict[str, int]
    people_with_seat: int


@dataclass(frozen=True)
class SlotPresence:
    day: date
    period: str
    present: Split
    derived: int  # of the evening presences, how many are derived from the whole day (D-009)


@dataclass(frozen=True)
class PresenceSection:
    slots: list[SlotPresence]
    peak: int
    average_per_daytime_slot: float
    person_days: Split


@dataclass(frozen=True)
class MealDay:
    day: date
    lunches: Split
    dinners: Split


@dataclass(frozen=True)
class MealsSection:
    days: list[MealDay]
    lunches: Split
    dinners: Split
    lunch_diets: dict[str, int]
    dinner_diets: dict[str, int]
    # Only the number: who they are and what they have stays in the meals view (health data).
    people_with_allergies: int


@dataclass(frozen=True)
class ActivityRow:
    id: int
    title: str
    day: date
    period: str
    price_cents: int
    capacity: int | None
    joined: Split
    expected_cents: int
    payment_mode: str = "organizer"


@dataclass(frozen=True)
class WaitlistSection:
    waiting: int
    promoted: int
    promoted_plus_one: int
    left: int
    removed: int
    cancelled: int
    booked: int


@dataclass(frozen=True)
class RevenueSection:
    due_cents: int
    due_fee_cents: int
    due_meals_cents: int
    due_activities_cents: int
    # What the parts do not explain: a price that changed after people signed up (D-017).
    due_difference_cents: int
    paid_cents: int
    paid_by_channel: dict[str, int]
    refunded_cents: int
    net_cents: int
    to_collect_cents: int
    to_confirm_cents: int | None
    credits_cents: int
    to_refund_cents: int


@dataclass(frozen=True)
class EditionReport:
    enrollment: EnrollmentSection
    presence: PresenceSection
    meals: MealsSection
    activities: list[ActivityRow]
    contributions: dict[str, int]
    waitlist: WaitlistSection
    revenue: RevenueSection
    days: list[date] = field(default_factory=list)


def _split(counter_confirmed: int, counter_pending: int) -> Split:
    return Split(confirmed=counter_confirmed, pending=counter_pending)


def _seated(bookings: Iterable[BookingFacts]) -> tuple[list[BookingFacts], list[BookingFacts]]:
    """Confirmed and pending bookings, apart."""
    seated = [b for b in bookings if occupies_seats(b.status)]
    return (
        [b for b in seated if b.status == STATUS_CONFIRMED],
        [b for b in seated if b.status == STATUS_PENDING],
    )


def _enrollment(bookings: Sequence[BookingFacts]) -> EnrollmentSection:
    counted = Counter(b.status for b in bookings)
    seated = {b.person_id for b in bookings if occupies_seats(b.status)}
    return EnrollmentSection(
        by_status={status: counted.get(status, 0) for status in ALL_STATUSES},
        people_with_seat=len(seated),
    )


def _presence(
    confirmed: Sequence[BookingFacts], pending: Sequence[BookingFacts], slots
) -> PresenceSection:
    def rows(group: Sequence[BookingFacts]):
        return presences((b.person_id, day, period) for b in group for day, period in b.slots)

    by_group = {"confirmed": rows(confirmed), "pending": rows(pending)}
    counts = {name: Counter((r.day, r.period) for r in found) for name, found in by_group.items()}
    derived = Counter((r.day, r.period) for found in by_group.values() for r in found if r.derived)
    ordered = sorted(set(slots), key=lambda s: (s[0], PERIODS.index(s[1])))
    result = [
        SlotPresence(
            day=day,
            period=period,
            present=_split(counts["confirmed"][(day, period)], counts["pending"][(day, period)]),
            derived=derived[(day, period)],
        )
        for day, period in ordered
    ]
    daytime = [s.present.total for s in result if s.period != PERIOD_EVENING]
    person_days = _split(
        len({(r.person_id, r.day) for r in by_group["confirmed"]}),
        len({(r.person_id, r.day) for r in by_group["pending"]}),
    )
    return PresenceSection(
        slots=result,
        peak=max((s.present.total for s in result), default=0),
        average_per_daytime_slot=round(sum(daytime) / len(daytime), 1) if daytime else 0.0,
        person_days=person_days,
    )


def _diet_counts(bookings: Iterable[BookingFacts]) -> dict[str, int]:
    counted = Counter(b.diet if b.diet in DIETS else NO_DIET for b in bookings)
    return {key: counted.get(key, 0) for key in (*DIETS, NO_DIET)}


def _meals(
    confirmed: Sequence[BookingFacts], pending: Sequence[BookingFacts], slots
) -> MealsSection:
    days = sorted({day for day, _ in slots})

    def per_meal(group: Sequence[BookingFacts]) -> Counter[tuple[date, str]]:
        return Counter(meal for b in group for meal in b.meals)

    sure, waiting = per_meal(confirmed), per_meal(pending)
    day_rows = [
        MealDay(
            day=day,
            lunches=_split(sure[(day, MEAL_LUNCH)], waiting[(day, MEAL_LUNCH)]),
            dinners=_split(sure[(day, MEAL_DINNER)], waiting[(day, MEAL_DINNER)]),
        )
        for day in days
    ]

    def total(kind: str, group: Sequence[BookingFacts]) -> int:
        return sum(1 for b in group for _, k in b.meals if k == kind)

    seated = [*confirmed, *pending]
    return MealsSection(
        days=day_rows,
        lunches=_split(total(MEAL_LUNCH, confirmed), total(MEAL_LUNCH, pending)),
        dinners=_split(total(MEAL_DINNER, confirmed), total(MEAL_DINNER, pending)),
        lunch_diets=_diet_counts(b for b in seated if any(k == MEAL_LUNCH for _, k in b.meals)),
        dinner_diets=_diet_counts(b for b in seated if any(k == MEAL_DINNER for _, k in b.meals)),
        people_with_allergies=sum(1 for b in seated if b.has_allergies),
    )


def _activities(
    activities: Sequence[ActivityFacts],
    confirmed: Sequence[BookingFacts],
    pending: Sequence[BookingFacts],
) -> list[ActivityRow]:
    rows = []
    for activity in sorted(activities, key=lambda a: (a.day, PERIODS.index(a.period), a.id)):
        joined = _split(
            sum(1 for b in confirmed if activity.id in b.activity_ids),
            sum(1 for b in pending if activity.id in b.activity_ids),
        )
        rows.append(
            ActivityRow(
                id=activity.id,
                title=activity.title,
                day=activity.day,
                period=activity.period,
                price_cents=activity.price_cents,
                capacity=activity.capacity,
                joined=joined,
                expected_cents=collectable(activity.price_cents, activity.payment_mode)
                * joined.total,
                payment_mode=activity.payment_mode,
            )
        )
    return rows


def _waitlist(entries: Iterable[WaitlistFacts]) -> WaitlistSection:
    entries = list(entries)
    reasons = Counter(e.close_reason for e in entries)
    return WaitlistSection(
        waiting=reasons[None],
        promoted=reasons[CLOSE_PROMOTED],
        promoted_plus_one=sum(
            1 for e in entries if e.close_reason == CLOSE_PROMOTED and e.plus_one
        ),
        left=reasons[CLOSE_LEFT],
        removed=reasons[CLOSE_REMOVED],
        cancelled=reasons[CLOSE_CANCELLED],
        booked=reasons[CLOSE_BOOKED],
    )


def _revenue(
    bookings: Sequence[BookingFacts],
    payments: Iterable[PaymentFacts],
    activities: Sequence[ActivityFacts],
    edition: EditionFacts,
) -> RevenueSection:
    price_of = {a.id: collectable(a.price_cents, a.payment_mode) for a in activities}
    seated = [b for b in bookings if occupies_seats(b.status)]
    due = sum(b.amount_due_cents for b in seated)
    fee = sum(
        b.registration_fee_cents
        if b.registration_fee_cents is not None
        else compute_fee(
            {day for day, _ in b.slots}, edition.base_fee_cents, edition.per_day_fee_cents
        )
        for b in seated
    )
    meals = sum(
        collectable(
            *edition.meal_terms.get(
                (day, kind),
                (
                    edition.lunch_price_cents if kind == MEAL_LUNCH else edition.dinner_price_cents,
                    "organizer",
                ),
            )
        )
        for b in seated
        for day, kind in b.meals
    )
    activity_cents = sum(price_of.get(a, 0) for b in seated for a in b.activity_ids)
    by_channel: Counter[str] = Counter()
    for payment in payments:
        by_channel[payment.channel] += payment.amount_cents
    paid = sum(b.paid_cents for b in bookings)
    refunded = sum(b.refund_cents for b in bookings)
    pending = [b for b in bookings if b.status == STATUS_PENDING]
    pending_confirmation_dues = [
        confirmation_due_cents(
            edition.confirmation_policy, b.amount_due_cents, b.registration_fee_cents
        )
        for b in pending
    ]
    to_confirm = (
        None
        if any(due is None for due in pending_confirmation_dues)
        else sum(
            max(0, due - b.paid_cents)
            for b, due in zip(pending, pending_confirmation_dues, strict=True)
        )
    )
    return RevenueSection(
        due_cents=due,
        due_fee_cents=fee,
        due_meals_cents=meals,
        due_activities_cents=activity_cents,
        due_difference_cents=due - fee - meals - activity_cents,
        paid_cents=paid,
        paid_by_channel=dict(sorted(by_channel.items())),
        refunded_cents=refunded,
        net_cents=paid - refunded,
        to_collect_cents=sum(max(b.amount_due_cents - b.paid_cents, 0) for b in seated),
        to_confirm_cents=to_confirm,
        credits_cents=sum(max(b.paid_cents - b.amount_due_cents, 0) for b in seated),
        to_refund_cents=sum(
            max(b.paid_cents - b.refund_cents, 0)
            for b in bookings
            if b.status == STATUS_CANCEL_REQUESTED
        ),
    )


def edition_report(
    edition: EditionFacts,
    bookings: Sequence[BookingFacts],
    activities: Sequence[ActivityFacts],
    waitlist: Iterable[WaitlistFacts],
    payments: Iterable[PaymentFacts],
) -> EditionReport:
    confirmed, pending = _seated(bookings)
    contributions = Counter(kind for b in [*confirmed, *pending] for kind in b.contributions)
    return EditionReport(
        enrollment=_enrollment(bookings),
        presence=_presence(confirmed, pending, edition.slots),
        meals=_meals(confirmed, pending, edition.slots),
        activities=_activities(activities, confirmed, pending),
        contributions={kind: contributions.get(kind, 0) for kind in CONTRIBUTION_KINDS},
        waitlist=_waitlist(waitlist),
        revenue=_revenue(bookings, payments, activities, edition),
        days=sorted({day for day, _ in edition.slots}),
    )
