from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import Session

from app.domain.booking import available_seats
from app.models import (
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    Activity,
    Booking,
    BookingActivity,
    BookingSlot,
    Edition,
    Slot,
)


def lock_edition(db: Session, edition_id: int | None = None) -> None:
    """Serialize pricing edits with booking writes. Always take this before booking/seat locks."""
    query = select(Edition.id).order_by(Edition.id)
    if edition_id is not None:
        query = query.where(Edition.id == edition_id)
    db.execute(query.with_for_update().with_hint(Edition, "WITH (UPDLOCK, HOLDLOCK)", "mssql"))


def slots_for_update(slot_ids: Iterable[int], edition_id: int | None = None):
    """Select slots and lock them until the end of the transaction.

    SQLAlchemy's `with_for_update()` is ignored on SQL Server, which has no FOR UPDATE: it needs
    the explicit UPDLOCK hint. HOLDLOCK keeps the lock until commit. Both are kept so the query
    stays correct on other databases too.
    """
    query = select(Slot).where(Slot.id.in_(list(slot_ids))).order_by(Slot.id)
    if edition_id is not None:
        query = query.where(Slot.edition_id == edition_id)
    return query.with_for_update().with_hint(Slot, "WITH (UPDLOCK, HOLDLOCK)", "mssql")


def lock_booking(db: Session, booking_id: int) -> None:
    """Lock one booking until the end of the transaction, so changes to its payments and status
    are applied one at a time (two admins voiding payments at once would each see the other's
    payment as still counting). Like the slot lock, SQL Server needs the explicit hint."""
    db.execute(
        select(Booking.id)
        .where(Booking.id == booking_id)
        .with_for_update()
        .with_hint(Booking, "WITH (UPDLOCK, HOLDLOCK)", "mssql")
    )


def has_other_active_booking(db: Session, booking: Booking, now: datetime) -> bool:
    """True if the same person already has another pending (within its hold) or confirmed
    booking in the same edition."""
    return (
        db.scalar(
            select(Booking.id)
            .where(
                Booking.participant_id == booking.participant_id,
                Booking.edition_id == booking.edition_id,
                Booking.id != booking.id,
                or_(
                    Booking.status == STATUS_CONFIRMED,
                    and_(Booking.status == STATUS_PENDING, Booking.hold_expires_at > now),
                ),
            )
            .limit(1)
        )
        is not None
    )


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


def occupied_by_activity(db: Session, activity_ids: Iterable[int], now: datetime) -> dict[int, int]:
    """Seats taken per activity: confirmed bookings plus pending ones still within their hold."""
    ids = list(activity_ids)
    rows = db.execute(
        select(BookingActivity.activity_id, func.count())
        .join(Booking, Booking.id == BookingActivity.booking_id)
        .where(
            BookingActivity.activity_id.in_(ids),
            or_(
                Booking.status == STATUS_CONFIRMED,
                and_(Booking.status == STATUS_PENDING, Booking.hold_expires_at > now),
            ),
        )
        .group_by(BookingActivity.activity_id)
    ).all()
    counts = {activity_id: count for activity_id, count in rows}
    return {activity_id: counts.get(activity_id, 0) for activity_id in ids}


def free_by_activity(
    db: Session, activities: Iterable[Activity], now: datetime
) -> dict[int, int | None]:
    activities = list(activities)
    occupied = occupied_by_activity(db, [a.id for a in activities], now)
    return {a.id: available_seats(a.capacity, occupied[a.id]) for a in activities}


def activities_for_update(activity_ids: Iterable[int], edition_id: int):
    """Select activities and lock them until commit, as `slots_for_update` does for slots
    (SQL Server needs the explicit hint, D-011)."""
    return (
        select(Activity)
        .where(Activity.id.in_(list(activity_ids)), Activity.edition_id == edition_id)
        .order_by(Activity.id)
        .with_for_update()
        .with_hint(Activity, "WITH (UPDLOCK, HOLDLOCK)", "mssql")
    )
