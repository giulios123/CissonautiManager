"""Activities: who can join, what happens when slots change, which edits are allowed.

Pure functions. An activity takes place on a day in one part of it; only people present then can
join (the evening of someone booking the whole day counts, D-009).
"""

from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Literal, Protocol

from app.domain.booking import has_free_seat
from app.domain.presence import has_evening
from app.models import CONTRIBUTION_KINDS, PERIOD_EVENING

JoinRefusal = Literal["not_present", "full", "past_day"]
EditRefusal = Literal["fixed_with_people", "capacity_below_people", "has_people"]


class ActivityLike(Protocol):
    id: int
    date: date
    period: str


@dataclass(frozen=True)
class Check:
    ok: bool
    reason: str | None = None


def is_eligible(periods_that_day: Collection[str], period: str) -> bool:
    """Present in that part of the day."""
    if period == PERIOD_EVENING:
        return has_evening(periods_that_day)
    return period in periods_that_day


def activities_to_drop[A: ActivityLike](
    activities: Iterable[A], periods: Mapping[date, Collection[str]]
) -> list[A]:
    """Activities the person no longer has a right to after a change of slots."""
    return [a for a in activities if not is_eligible(periods.get(a.date, ()), a.period)]


def check_join(
    eligible: bool,
    free: int | None,
    past_day: bool,
    allow_past: bool = False,
    force: bool = False,
) -> Check:
    """Whether someone can join. Presence is always needed; admins may join past days
    (`allow_past`) and go over capacity (`force`)."""
    if not eligible:
        return Check(False, "not_present")
    if past_day and not allow_past:
        return Check(False, "past_day")
    if not has_free_seat(free) and not force:
        return Check(False, "full")
    return Check(True)


def check_leave(past_day: bool, allow_past: bool = False) -> Check:
    if past_day and not allow_past:
        return Check(False, "past_day")
    return Check(True)


def check_activity_edit(
    joined: int,
    price_changed: bool,
    when_changed: bool,
    new_capacity: int | None,
) -> Check:
    """Schedule edits are fixed with sign-ups. Financial edits use the repricing transaction.

    `price_changed` is retained for callers that cannot atomically reprice existing bookings.
    """
    if joined > 0 and (price_changed or when_changed):
        return Check(False, "fixed_with_people")
    if new_capacity is not None and new_capacity < joined:
        return Check(False, "capacity_below_people")
    return Check(True)


def check_activity_delete(joined: int) -> Check:
    return Check(True) if joined == 0 else Check(False, "has_people")


def validate_contribution(kind: str, title: str) -> Check:
    if kind not in CONTRIBUTION_KINDS:
        return Check(False, "invalid_kind")
    if not title.strip():
        return Check(False, "title_required")
    return Check(True)
