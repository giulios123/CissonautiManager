from collections.abc import Iterable
from datetime import date, datetime, timedelta

from app.domain.fees import is_covered
from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
)
from app.timefmt import to_rome


def hold_deadline(created_at: datetime, hold_days: int) -> datetime:
    """A pending booking holds its seats for hold_days x 24 hours from creation."""
    return created_at + timedelta(days=hold_days)


def effective_status(status: str, hold_expires_at: datetime, now: datetime) -> str:
    """Status as seen at `now`. A pending booking past its deadline is expired.

    Expiry is evaluated on read, so no scheduled job is needed.
    At exactly the deadline the hold is already over.
    """
    if status == STATUS_PENDING and now >= hold_expires_at:
        return STATUS_EXPIRED
    return status


def occupies_seats(status: str) -> bool:
    """Only pending (not expired) and confirmed bookings occupy seats.

    Expired, cancellation requested and refunded bookings free their seats.
    """
    return status in (STATUS_PENDING, STATUS_CONFIRMED)


def available_seats(capacity: int | None, occupied: int) -> int | None:
    """Seats left in a slot. None means the slot has no limit (the evening)."""
    if capacity is None:
        return None
    return max(capacity - occupied, 0)


def has_free_seat(free: int | None) -> bool:
    return free is None or free >= 1


def can_reactivate(free_seats_per_slot: Iterable[int | None]) -> bool:
    """An expired booking can come back only if every one of its slots still has a free seat."""
    return all(has_free_seat(free) for free in free_seats_per_slot)


def can_edit_slots(status: str) -> bool:
    """A participant can change slots only on a pending or confirmed booking."""
    return status in (STATUS_PENDING, STATUS_CONFIRMED)


def can_request_cancellation(status: str) -> bool:
    return status in (STATUS_PENDING, STATUS_CONFIRMED)


def is_past_day(day: date, now: datetime) -> bool:
    """True when the day is over in Europe/Rome. Today still counts as not past."""
    return day < to_rome(now).date()


def can_refund(status: str, paid_cents: int, refund_cents: int) -> bool:
    """A refund closes a requested cancellation and cannot exceed what was paid."""
    return status == STATUS_CANCEL_REQUESTED and 0 <= refund_cents <= paid_cents


def can_extend_hold(status: str) -> bool:
    """Only a booking still waiting for payment has a hold to extend."""
    return status == STATUS_PENDING


def status_after_void(status: str, due_cents: int | None, paid_cents: int) -> str:
    """A confirmed booking whose payments no longer cover the amount goes back to waiting."""
    if (
        due_cents is not None
        and status == STATUS_CONFIRMED
        and not is_covered(due_cents, paid_cents)
    ):
        return STATUS_PENDING
    return status
