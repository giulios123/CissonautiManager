from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from app.domain.waitlist import (
    can_join,
    can_verify_plus_one,
    hold_after_promotion,
    position,
    promotion_kind,
    queue,
    waitlist_limit,
)
from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    STATUS_REFUNDED,
)

NOW = datetime(2026, 7, 1, 10, 0, tzinfo=UTC)


@dataclass
class Entry:
    id: int
    created_at: datetime
    participant_id: int = 0


@pytest.mark.parametrize(
    ("capacity", "percent", "expected"),
    [(25, 20, 5), (3, 20, 0), (10, 25, 2), (25, 0, 0), (25, 100, 25), (None, 20, 0)],
)
def test_waitlist_limit_rounds_down_and_the_evening_has_none(capacity, percent, expected):
    assert waitlist_limit(capacity, percent) == expected


def join(**overrides):
    values = dict(
        free=0,
        active_entries=0,
        limit=5,
        already_booked=False,
        already_listed=False,
        past_day=False,
    )
    values.update(overrides)
    return can_join(**values)


def test_can_join_a_full_slot_with_room_on_the_list():
    assert join().ok


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"free": 1}, "not_full"),
        ({"free": None}, "not_full"),
        ({"active_entries": 5}, "list_full"),
        ({"limit": 0}, "list_full"),
        ({"already_booked": True}, "already_booked"),
        ({"already_listed": True}, "already_listed"),
        ({"past_day": True}, "past_day"),
    ],
)
def test_can_join_refusals(overrides, reason):
    check = join(**overrides)
    assert not check.ok
    assert check.reason == reason


def test_queue_is_first_come_first_served_with_the_id_breaking_ties():
    later = Entry(1, NOW + timedelta(minutes=5))
    first = Entry(3, NOW)
    same_instant = Entry(2, NOW)
    assert [e.id for e in queue([later, first, same_instant])] == [2, 3, 1]


def test_position_is_one_based():
    entries = [Entry(7, NOW + timedelta(hours=1)), Entry(4, NOW)]
    assert position(entries, 4) == 1
    assert position(entries, 7) == 2
    with pytest.raises(ValueError):
        position(entries, 99)


def test_hold_after_promotion_gives_a_full_hold_from_now():
    assert hold_after_promotion(NOW + timedelta(hours=2), NOW, 3) == NOW + timedelta(days=3)


def test_hold_after_promotion_never_shortens_the_deadline():
    later = NOW + timedelta(days=5)
    assert hold_after_promotion(later, NOW, 3) == later


@pytest.mark.parametrize(
    ("status", "kind"),
    [
        (STATUS_PENDING, "add_to_pending"),
        (STATUS_CONFIRMED, "add_to_confirmed"),
        (STATUS_EXPIRED, "new_booking"),
        (STATUS_CANCEL_REQUESTED, "new_booking"),
        (STATUS_REFUNDED, "new_booking"),
        (None, "new_booking"),
    ],
)
def test_promotion_kind(status, kind):
    assert promotion_kind(status) == kind


def test_queue_puts_a_verified_plus_one_before_someone_who_arrived_earlier():
    early = Entry(1, NOW, participant_id=10)
    plus_one = Entry(2, NOW + timedelta(hours=3), participant_id=20)
    assert [e.id for e in queue([early, plus_one], priority_ids={20})] == [2, 1]


def test_queue_keeps_arrival_order_inside_each_group():
    first = Entry(1, NOW, participant_id=10)
    second = Entry(2, NOW + timedelta(minutes=1), participant_id=11)
    plus_one_late = Entry(3, NOW + timedelta(hours=2), participant_id=20)
    plus_one_early = Entry(4, NOW + timedelta(hours=1), participant_id=21)
    ordered = queue([second, plus_one_late, first, plus_one_early], priority_ids={20, 21})
    assert [e.id for e in ordered] == [4, 3, 1, 2]


def test_queue_breaks_a_tie_between_plus_ones_by_id():
    a = Entry(5, NOW, participant_id=20)
    b = Entry(3, NOW, participant_id=21)
    assert [e.id for e in queue([a, b], priority_ids={20, 21})] == [3, 5]


def test_queue_without_priority_is_unchanged():
    entries = [Entry(1, NOW + timedelta(minutes=5), 10), Entry(2, NOW, 20)]
    assert queue(entries) == queue(entries, priority_ids=frozenset())
    assert [e.id for e in queue(entries)] == [2, 1]


def test_position_follows_the_priority():
    entries = [Entry(1, NOW, 10), Entry(2, NOW + timedelta(hours=1), 20)]
    assert position(entries, 2) == 2
    assert position(entries, 2, priority_ids={20}) == 1
    assert position(entries, 1, priority_ids={20}) == 2


@pytest.mark.parametrize(
    ("invited_by", "expected"),
    [("Ada", True), ("  Ada Lovelace ", True), ("", False), ("   ", False), (None, False)],
)
def test_a_plus_one_needs_someone_who_invited_them(invited_by, expected):
    assert can_verify_plus_one(invited_by) is expected
