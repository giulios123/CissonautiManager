"""Deliveries of the benefits of the edition (MVP 30).

Who is entitled comes from `domain.benefits`. A delivery is tied to the person and the edition:
it outlives the booking, and it stays on record when the entitlement is lost or when it is
annulled (with a reason, never deleted).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.domain.benefits import is_entitled
from app.domain.booking import effective_status, occupies_seats
from app.models import (
    AuditLog,
    Benefit,
    BenefitDelivery,
    Booking,
    Edition,
    Participant,
    net_paid_cents,
)

State = Literal["to_deliver", "delivered", "delivered_without_entitlement"]
StateFilter = Literal["all", "pending", "delivered"]


class BenefitNotFound(Exception):
    pass


class BenefitRetired(Exception):
    pass


class NotEntitled(Exception):
    pass


class PersonNotFound(Exception):
    pass


class DeliveryNotFound(Exception):
    pass


class ReasonRequired(Exception):
    pass


@dataclass
class Row:
    participant_id: int
    first_name: str
    last_name: str
    booking_id: int | None
    category: str | None
    entitled: bool
    active: BenefitDelivery | None = None
    annulled: list[BenefitDelivery] = field(default_factory=list)

    @property
    def state(self) -> State:
        if self.active is None:
            return "to_deliver"
        return "delivered" if self.entitled else "delivered_without_entitlement"


def _bookings(db: Session, edition: Edition, participant_id: int | None = None) -> list[Booking]:
    query = (
        select(Booking)
        .where(Booking.edition_id == edition.id)
        .options(
            selectinload(Booking.participant),
            selectinload(Booking.payments),
            selectinload(Booking.refunds),
        )
    )
    if participant_id is not None:
        query = query.where(Booking.participant_id == participant_id)
    return list(db.scalars(query))


def _entitled(booking: Booking, edition: Edition, now: datetime) -> bool:
    status = effective_status(booking.status, booking.hold_expires_at, now)
    return is_entitled(
        active=occupies_seats(status),
        category=booking.category,
        fee_exempt=booking.fee_exempt,
        net_paid_cents=net_paid_cents(booking),
        base_fee_cents=edition.base_fee_cents,
    )


def entitled_bookings(db: Session, edition: Edition, now: datetime) -> list[Booking]:
    """The active bookings of the edition whose owner is entitled to the benefits."""
    return [b for b in _bookings(db, edition) if _entitled(b, edition, now)]


def get_benefit(db: Session, edition: Edition, benefit_id: int) -> Benefit:
    benefit = db.get(Benefit, benefit_id)
    if benefit is None or benefit.edition_id != edition.id:
        raise BenefitNotFound()
    return benefit


def catalogue(db: Session, edition: Edition, now: datetime) -> list[dict]:
    """The benefits to deliver, with how many are delivered and how many people are entitled.

    A retired benefit shows up only when something was delivered with it."""
    entitled = len(entitled_bookings(db, edition, now))
    active: dict[int, int] = {}
    for delivery in db.scalars(
        select(BenefitDelivery).where(
            BenefitDelivery.edition_id == edition.id, BenefitDelivery.annulled_at.is_(None)
        )
    ):
        active[delivery.benefit_id] = active.get(delivery.benefit_id, 0) + 1
    result = []
    for benefit in db.scalars(
        select(Benefit)
        .where(Benefit.edition_id == edition.id)
        .order_by(Benefit.sort_order, Benefit.id)
    ):
        if benefit.retired and not active.get(benefit.id):
            continue
        result.append(
            {
                "benefit": benefit,
                "delivered": active.get(benefit.id, 0),
                "entitled": entitled,
            }
        )
    return result


def rows_for(
    db: Session,
    edition: Edition,
    benefit: Benefit,
    now: datetime,
    query: str = "",
    state: StateFilter = "all",
) -> list[Row]:
    """The people entitled to the benefit, plus whoever has a delivery of it on record.

    Someone who lost the entitlement keeps appearing while a delivery is active; with only
    annulled deliveries they are left out."""
    rows: dict[int, Row] = {}
    for booking in _bookings(db, edition):
        if _entitled(booking, edition, now):
            person = booking.participant
            rows[person.id] = Row(
                person.id,
                person.first_name,
                person.last_name,
                booking.id,
                booking.category,
                True,
            )
    deliveries = db.scalars(
        select(BenefitDelivery)
        .where(BenefitDelivery.edition_id == edition.id, BenefitDelivery.benefit_id == benefit.id)
        .options(
            selectinload(BenefitDelivery.participant),
            selectinload(BenefitDelivery.delivered_by),
            selectinload(BenefitDelivery.annulled_by),
        )
        .order_by(BenefitDelivery.id)
    ).all()
    bookings = None
    for delivery in deliveries:
        row = rows.get(delivery.participant_id)
        if row is None:
            if delivery.annulled_at is not None:
                continue
            if bookings is None:
                bookings = {b.participant_id: b for b in _bookings(db, edition)}
            booking = bookings.get(delivery.participant_id)
            person = delivery.participant
            row = rows[person.id] = Row(
                person.id,
                person.first_name,
                person.last_name,
                booking.id if booking else None,
                booking.category if booking else None,
                False,
            )
        if delivery.annulled_at is None:
            row.active = delivery
        else:
            row.annulled.append(delivery)
    needle = query.strip().lower()
    result = [
        row
        for row in rows.values()
        if (not needle or needle in f"{row.first_name} {row.last_name}".lower())
        and (state == "all" or (state == "delivered") == (row.active is not None))
    ]
    return sorted(
        result, key=lambda r: (r.last_name.lower(), r.first_name.lower(), r.participant_id)
    )


def _log(
    db: Session,
    admin: Participant,
    action: str,
    edition: Edition,
    delivery: BenefitDelivery,
    benefit: Benefit,
    booking_id: int | None,
    extra: str = "",
) -> None:
    person = delivery.participant
    db.add(
        AuditLog(
            actor_id=admin.id,
            booking_id=booking_id,
            participant_id=delivery.participant_id,
            edition_id=edition.id,
            action=action,
            detail=f"{benefit.name_it}: {person.first_name} {person.last_name}{extra}",
        )
    )


def deliver(
    db: Session,
    admin: Participant,
    edition: Edition,
    participant_id: int,
    benefit_id: int,
    request_key: str | None,
    now: datetime,
) -> tuple[BenefitDelivery, bool]:
    """Register a delivery. Returns it and whether it is new: a repeated request, or one for a
    benefit already delivered to that person, returns the existing delivery."""
    if request_key is not None:
        existing = db.scalar(
            select(BenefitDelivery).where(
                BenefitDelivery.edition_id == edition.id,
                BenefitDelivery.request_key == request_key,
            )
        )
        if existing is not None:
            return existing, False
    benefit = get_benefit(db, edition, benefit_id)
    person = db.get(Participant, participant_id)
    if person is None:
        raise PersonNotFound()
    active = _active(db, participant_id, benefit_id)
    if active is not None:
        return active, False
    if benefit.retired:
        raise BenefitRetired()
    bookings = _bookings(db, edition, participant_id)
    if not any(_entitled(b, edition, now) for b in bookings):
        raise NotEntitled()
    delivery = BenefitDelivery(
        edition_id=edition.id,
        participant_id=participant_id,
        benefit_id=benefit_id,
        delivered_at=now,
        delivered_by_id=admin.id,
        request_key=request_key,
    )
    delivery.participant = person
    db.add(delivery)
    try:
        db.flush()
    except IntegrityError:
        # Two admins in a race: the other delivery won.
        db.rollback()
        winner = _active(db, participant_id, benefit_id)
        if winner is None and request_key is not None:
            winner = db.scalar(
                select(BenefitDelivery).where(BenefitDelivery.request_key == request_key)
            )
        if winner is None:
            raise
        return winner, False
    _log(
        db,
        admin,
        "benefit_delivered",
        edition,
        delivery,
        benefit,
        bookings[0].id if bookings else None,
    )
    db.commit()
    return delivery, True


def _active(db: Session, participant_id: int, benefit_id: int) -> BenefitDelivery | None:
    return db.scalar(
        select(BenefitDelivery).where(
            BenefitDelivery.participant_id == participant_id,
            BenefitDelivery.benefit_id == benefit_id,
            BenefitDelivery.annulled_at.is_(None),
        )
    )


def annul(
    db: Session,
    admin: Participant,
    edition: Edition,
    delivery_id: int,
    reason: str,
    now: datetime,
) -> tuple[BenefitDelivery, bool]:
    """Annul a delivery with a reason. Returns it and whether it changed: annulling twice does
    nothing and leaves no second entry in the history."""
    delivery = db.get(BenefitDelivery, delivery_id)
    if delivery is None or delivery.edition_id != edition.id:
        raise DeliveryNotFound()
    if delivery.annulled_at is not None:
        return delivery, False
    reason = reason.strip()
    if not reason:
        raise ReasonRequired()
    delivery.annulled_at = now
    delivery.annulled_by_id = admin.id
    delivery.annul_reason = reason[:200]
    booking = db.scalar(
        select(Booking).where(
            Booking.edition_id == edition.id, Booking.participant_id == delivery.participant_id
        )
    )
    _log(
        db,
        admin,
        "benefit_annulled",
        edition,
        delivery,
        delivery.benefit,
        booking.id if booking else None,
        f" (annullata: {delivery.annul_reason})",
    )
    db.commit()
    return delivery, True
