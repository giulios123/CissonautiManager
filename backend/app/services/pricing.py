"""Reprice active bookings in the same transaction as a collection-policy edit."""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.booking import effective_status, occupies_seats
from app.domain.fees import is_covered
from app.models import STATUS_CONFIRMED, STATUS_PENDING, Booking, Edition, Participant
from app.services import audit
from app.services.amounts import recompute_amount
from app.services.payments import paid_total
from app.services.seats import lock_booking
from app.timefmt import format_euro


def reprice(
    db: Session,
    edition: Edition,
    admin: Participant,
    now: datetime,
    *,
    activity_id: int | None = None,
    meal: tuple[date, str] | None = None,
) -> list[Booking]:
    """Caller holds the edition lock; notifications are sent only after its commit."""
    confirmed = []
    query = select(Booking).where(Booking.edition_id == edition.id)
    if activity_id is not None:
        from app.models import Activity

        query = query.where(Booking.activities.any(Activity.id == activity_id))
    if meal is not None:
        from app.models import BookingMeal

        query = query.where(
            Booking.meals.any((BookingMeal.date == meal[0]) & (BookingMeal.kind == meal[1]))
        )
    bookings = db.scalars(query.order_by(Booking.id)).all()
    for booking in bookings:
        if not occupies_seats(effective_status(booking.status, booking.hold_expires_at, now)):
            continue
        lock_booking(db, booking.id)
        db.refresh(booking)
        old = booking.amount_due_cents
        recompute_amount(edition, booking)
        if old != booking.amount_due_cents:
            audit.log(
                db,
                admin,
                "pricing_changed",
                f"Ricalcolo quota: {format_euro(old)} → {format_euro(booking.amount_due_cents)}.",
                booking.id,
            )
        if booking.status == STATUS_PENDING and is_covered(
            booking.amount_due_cents, paid_total(booking)
        ):
            booking.status = STATUS_CONFIRMED
            confirmed.append(booking)
    return confirmed
