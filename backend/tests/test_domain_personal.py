from datetime import UTC, date, datetime, timedelta

import pytest

from app.domain.booking import can_edit_slots, can_request_cancellation, is_past_day
from app.domain.reminders import due_reminder
from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    STATUS_REFUNDED,
)

START = datetime(2026, 7, 1, 10, 0, tzinfo=UTC)
THREE_DAYS = START + timedelta(days=3)


@pytest.mark.parametrize(
    ("status", "allowed"),
    [
        (STATUS_PENDING, True),
        (STATUS_CONFIRMED, True),
        (STATUS_EXPIRED, False),
        (STATUS_CANCEL_REQUESTED, False),
        (STATUS_REFUNDED, False),
    ],
)
def test_edit_and_cancel_allowed_only_on_pending_and_confirmed(status, allowed):
    assert can_edit_slots(status) is allowed
    assert can_request_cancellation(status) is allowed


def test_today_is_not_past_and_yesterday_is():
    now = datetime(2026, 7, 14, 9, 0, tzinfo=UTC)  # 11:00 in Rome
    assert is_past_day(date(2026, 7, 13), now) is True
    assert is_past_day(date(2026, 7, 14), now) is False
    assert is_past_day(date(2026, 7, 15), now) is False


def test_past_day_is_evaluated_in_rome_not_utc():
    # 22:30 UTC on the 13th is already 00:30 on the 14th in Rome (summer time).
    now = datetime(2026, 7, 13, 22, 30, tzinfo=UTC)
    assert is_past_day(date(2026, 7, 13), now) is True
    assert is_past_day(date(2026, 7, 14), now) is False


def reminder(now, mid=None, final=None, expires=THREE_DAYS, started=START):
    return due_reminder(started, expires, mid, final, now)


def test_nothing_due_before_half_of_the_hold():
    assert reminder(START + timedelta(hours=35, minutes=59)) is None


def test_middle_reminder_due_at_half_of_the_hold():
    assert reminder(START + timedelta(hours=36)) == "mid"


def test_middle_reminder_is_sent_only_once():
    assert reminder(START + timedelta(hours=40), mid=START + timedelta(hours=36)) is None


def test_final_reminder_due_24_hours_before_deadline():
    mid = START + timedelta(hours=36)
    assert reminder(THREE_DAYS - timedelta(hours=24, minutes=1), mid=mid) is None
    assert reminder(THREE_DAYS - timedelta(hours=24), mid=mid) == "final"


def test_final_reminder_is_sent_only_once():
    mid = START + timedelta(hours=36)
    final = THREE_DAYS - timedelta(hours=24)
    assert reminder(THREE_DAYS - timedelta(hours=10), mid=mid, final=final) is None


def test_late_run_sends_only_the_final_reminder():
    now = THREE_DAYS - timedelta(hours=5)
    assert reminder(now) == "final"
    assert reminder(now, final=now) is None  # and then the middle one never follows


def test_nothing_is_due_after_the_deadline():
    assert reminder(THREE_DAYS) is None
    assert reminder(THREE_DAYS + timedelta(hours=1)) is None


def test_short_hold_has_only_the_middle_reminder():
    expires = START + timedelta(hours=40)
    assert reminder(START + timedelta(hours=19), expires=expires) is None
    assert reminder(START + timedelta(hours=20), expires=expires) == "mid"
    done = START + timedelta(hours=20)
    assert reminder(START + timedelta(hours=30), mid=done, expires=expires) is None


def test_hold_of_exactly_48_hours_has_both_reminders():
    expires = START + timedelta(hours=48)
    assert reminder(START + timedelta(hours=24), expires=expires) == "final"
    assert reminder(START + timedelta(hours=24), mid=START, expires=expires) == "final"


def test_reactivated_hold_counts_from_its_new_start():
    new_start = START + timedelta(days=10)
    expires = new_start + timedelta(days=3)
    now = new_start + timedelta(hours=36)
    assert due_reminder(new_start, expires, None, None, now) == "mid"
