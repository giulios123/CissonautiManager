from collections.abc import Iterable
from datetime import date


def compute_fee(slot_dates: Iterable[date], base_cents: int, per_day_cents: int) -> int:
    """Base fee plus a per-day amount for each distinct day with a booked slot."""
    distinct_days = set(slot_dates)
    return base_cents + per_day_cents * len(distinct_days)


def balance_cents(due_cents: int, paid_cents: int) -> int:
    """Participant balance: what is still owed (negative when overpaid)."""
    return due_cents - paid_cents


def is_covered(due_cents: int, paid_cents: int) -> bool:
    """True when registered payments cover the amount due."""
    return paid_cents >= due_cents
