from collections.abc import Iterable
from datetime import datetime, timedelta

from app.models import STATUS_CONFIRMED, STATUS_EXPIRED, STATUS_PENDING


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


def available_seats(capacity: int, occupied: int) -> int:
    return max(capacity - occupied, 0)


def can_reactivate(free_seats_per_slot: Iterable[int]) -> bool:
    """An expired booking can come back only if every one of its slots still has a free seat."""
    return all(free >= 1 for free in free_seats_per_slot)
