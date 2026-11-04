from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import Session

from app.domain.booking import available_seats
from app.models import STATUS_CONFIRMED, STATUS_EXPIRED, STATUS_PENDING, Booking, BookingSlot, Slot


def expire_overdue(db: Session, now: datetime) -> None:
    """Write the `scaduta` status for pending bookings past their deadline.

    Expiry is always evaluated on read (seat counts ignore overdue holds anyway); this keeps
    the stored status consistent for lists and filters. No scheduled job is needed.
    """
    db.execute(
        update(Booking)
        .where(Booking.status == STATUS_PENDING, Booking.hold_expires_at <= now)
        .values(status=STATUS_EXPIRED)
    )
    db.flush()


def occupied_by_slot(db: Session, slot_ids: Iterable[int], now: datetime) -> dict[int, int]:
    """Seats taken per slot: confirmed bookings plus pending ones still within their hold."""
    ids = list(slot_ids)
    rows = db.execute(
        select(BookingSlot.slot_id, func.count())
        .join(Booking, Booking.id == BookingSlot.booking_id)
        .where(
            BookingSlot.slot_id.in_(ids),
            or_(
                Booking.status == STATUS_CONFIRMED,
                and_(Booking.status == STATUS_PENDING, Booking.hold_expires_at > now),
            ),
        )
        .group_by(BookingSlot.slot_id)
    ).all()
    counts = {slot_id: count for slot_id, count in rows}
    return {slot_id: counts.get(slot_id, 0) for slot_id in ids}


def free_by_slot(db: Session, slots: Iterable[Slot], now: datetime) -> dict[int, int | None]:
    slots = list(slots)
    occupied = occupied_by_slot(db, [s.id for s in slots], now)
    return {s.id: available_seats(s.capacity, occupied[s.id]) for s in slots}
