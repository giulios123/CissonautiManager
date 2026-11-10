from dataclasses import dataclass
from datetime import date

import pytest

from app.domain.activities import (
    activities_to_drop,
    check_activity_delete,
    check_activity_edit,
    check_join,
    check_leave,
    is_eligible,
    validate_contribution,
)
from app.domain.fees import compute_amount_due
from app.domain.meals import periods_by_day

MON, TUE = date(2026, 7, 13), date(2026, 7, 14)


@dataclass
class Act:
    id: int
    date: date
    period: str


@pytest.mark.parametrize(
    ("periods", "period", "eligible"),
    [
        ({"morning"}, "morning", True),
        ({"morning"}, "afternoon", False),
        ({"evening"}, "evening", True),
        ({"morning", "afternoon"}, "evening", True),  # whole day: derived evening
        ({"afternoon"}, "evening", False),
        (set(), "morning", False),
    ],
)
def test_presence_in_the_part_of_the_day(periods, period, eligible):
    assert is_eligible(periods, period) is eligible


def test_dropping_a_slot_drops_its_activities():
    hike = Act(1, MON, "morning")
    talk = Act(2, MON, "evening")
    games = Act(3, TUE, "afternoon")
    periods = periods_by_day([(MON, "evening"), (TUE, "afternoon")])
    assert activities_to_drop([hike, talk, games], periods) == [hike]


@pytest.mark.parametrize(
    ("kwargs", "ok", "reason"),
    [
        (dict(eligible=True, free=1, past_day=False), True, None),
        (dict(eligible=True, free=None, past_day=False), True, None),
        (dict(eligible=False, free=1, past_day=False), False, "not_present"),
        (dict(eligible=True, free=0, past_day=False), False, "full"),
        (dict(eligible=True, free=1, past_day=True), False, "past_day"),
        (dict(eligible=True, free=1, past_day=True, allow_past=True), True, None),
        (dict(eligible=True, free=0, past_day=False, force=True), True, None),
        (
            dict(eligible=False, free=1, past_day=False, force=True, allow_past=True),
            False,
            "not_present",
        ),
    ],
)
def test_check_join(kwargs, ok, reason):
    check = check_join(**kwargs)
    assert (check.ok, check.reason) == (ok, reason)


def test_leaving_a_past_activity_only_for_admins():
    assert not check_leave(past_day=True).ok
    assert check_leave(past_day=True, allow_past=True).ok
    assert check_leave(past_day=False).ok


@pytest.mark.parametrize(
    ("joined", "price", "when", "capacity", "reason"),
    [
        (0, True, True, 1, None),
        (2, False, False, 2, None),
        (2, False, False, None, None),
        (2, True, False, 5, "fixed_with_people"),
        (2, False, True, 5, "fixed_with_people"),
        (3, False, False, 2, "capacity_below_people"),
    ],
)
def test_check_activity_edit(joined, price, when, capacity, reason):
    check = check_activity_edit(joined, price, when, capacity)
    assert check.reason == reason
    assert check.ok is (reason is None)


def test_an_activity_with_people_cannot_be_deleted():
    assert check_activity_delete(0).ok
    assert check_activity_delete(1).reason == "has_people"


@pytest.mark.parametrize(
    ("kind", "title", "reason"),
    [
        ("talk", "Macchine", None),
        ("topic", "x", None),
        ("skill", "  ", "title_required"),
        ("wanted_skill", "Saldatura", None),
        ("wanted_skill", "  ", "title_required"),
        ("song", "x", "invalid_kind"),
    ],
)
def test_validate_contribution(kind, title, reason):
    assert validate_contribution(kind, title).reason == reason


def test_amount_due_adds_paid_activities():
    base = compute_amount_due([MON], 0, 0, 1000, 100, 800, 1200)
    assert compute_amount_due([MON], 0, 0, 1000, 100, 800, 1200, activities_cents=0) == base
    assert (
        compute_amount_due([MON], 1, 0, 1000, 100, 800, 1200, activities_cents=1500)
        == 1100 + 800 + 1500
    )
