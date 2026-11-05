"""Waitlist rules for full slots. Pure functions, no database."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from app.domain.booking import has_free_seat, hold_deadline
from app.models import STATUS_CONFIRMED, STATUS_PENDING

JoinRefusal = Literal["not_full", "list_full", "already_booked", "already_listed", "past_day"]
PromotionKind = Literal["add_to_pending", "add_to_confirmed", "new_booking"]


class QueuedEntry(Protocol):
    id: int
    created_at: datetime


@dataclass(frozen=True)
class JoinCheck:
    ok: bool
    reason: JoinRefusal | None = None


def waitlist_limit(capacity: int | None, percent: int) -> int:
    """How many people can wait for a slot: a share of its capacity, rounded down.

    A slot without a limit (the evening) is never full, so it has no waitlist.
    """
    if capacity is None:
        return 0
    return capacity * percent // 100


def can_join(
    free: int | None,
    active_entries: int,
    limit: int,
    already_booked: bool,
    already_listed: bool,
    past_day: bool,
) -> JoinCheck:
    """Whether someone can join the waitlist of a slot, with the reason when they cannot."""
    if past_day:
        return JoinCheck(False, "past_day")
    if already_booked:
        return JoinCheck(False, "already_booked")
    if already_listed:
        return JoinCheck(False, "already_listed")
    if has_free_seat(free):
        return JoinCheck(False, "not_full")
    if active_entries >= limit:
        return JoinCheck(False, "list_full")
    return JoinCheck(True)


def queue[E: QueuedEntry](entries: Iterable[E]) -> list[E]:
    """Promotion order: first come, first served (the id breaks ties on the same instant).

    This is where a priority (the +1 of MVP 7) will plug in.
    """
    return sorted(entries, key=lambda e: (e.created_at, e.id))


def position(entries: Iterable[QueuedEntry], entry_id: int) -> int:
    """1-based position of an entry among the active entries of its slot."""
    for index, entry in enumerate(queue(entries), start=1):
        if entry.id == entry_id:
            return index
    raise ValueError(f"entry {entry_id} is not in the queue")


def hold_after_promotion(current_expiry: datetime, now: datetime, hold_days: int) -> datetime:
    """A pending booking that gets a seat from the waitlist has at least a full hold from now.

    The deadline never moves backwards.
    """
    return max(current_expiry, hold_deadline(now, hold_days))


def promotion_kind(current_status: str | None) -> PromotionKind:
    """What a promotion does, given the effective status of the person's current booking."""
    if current_status == STATUS_PENDING:
        return "add_to_pending"
    if current_status == STATUS_CONFIRMED:
        return "add_to_confirmed"
    return "new_booking"
