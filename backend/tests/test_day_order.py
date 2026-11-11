from datetime import UTC, date, datetime

import pytest

from app.domain.presence import event_today, in_useful_order, useful_day_order
from app.timefmt import rome_today

START, END = date(2026, 7, 10), date(2026, 7, 16)
DAYS = [date(2026, 7, n) for n in range(10, 17)]


def order(today: date, days=DAYS, start=START, end=END) -> list[int]:
    return [d.day for d in useful_day_order(days, today, start, end)]


def test_before_the_event_it_stays_chronological():
    assert order(date(2026, 7, 9)) == [10, 11, 12, 13, 14, 15, 16]


def test_after_the_event_it_stays_chronological():
    assert order(date(2026, 7, 17)) == [10, 11, 12, 13, 14, 15, 16]


def test_the_first_day_leads_and_nothing_is_past():
    assert order(date(2026, 7, 10)) == [10, 11, 12, 13, 14, 15, 16]


def test_in_the_middle_it_is_today_then_the_future_then_the_past():
    assert order(date(2026, 7, 13)) == [13, 14, 15, 16, 10, 11, 12]


def test_on_the_last_day_it_is_today_then_the_whole_past():
    assert order(date(2026, 7, 16)) == [16, 10, 11, 12, 13, 14, 15]


def test_today_without_a_row_starts_from_the_first_future_day():
    days = [d for d in DAYS if d.day != 13]
    assert order(date(2026, 7, 13), days) == [14, 15, 16, 10, 11, 12]


def test_duplicates_collapse_and_input_order_does_not_matter():
    shuffled = [DAYS[3], DAYS[0], DAYS[3], DAYS[6]]
    assert order(date(2026, 7, 12), shuffled) == [13, 16, 10]


@pytest.mark.parametrize("start,end", [(None, END), (START, None), (None, None)])
def test_an_edition_without_dates_is_chronological(start, end):
    assert order(date(2026, 7, 13), start=start, end=end) == [10, 11, 12, 13, 14, 15, 16]


def test_no_days_gives_nothing():
    assert useful_day_order([], date(2026, 7, 13), START, END) == []


def test_event_today_is_none_outside_the_edition_and_inclusive_inside():
    assert event_today(date(2026, 7, 9), START, END) is None
    assert event_today(date(2026, 7, 17), START, END) is None
    assert event_today(START, START, END) == START
    assert event_today(END, START, END) == END
    assert event_today(START, None, END) is None


def test_items_are_reordered_without_touching_them():
    items = [{"d": d, "n": d.day * 10} for d in DAYS]
    result = in_useful_order(items, lambda i: i["d"], date(2026, 7, 14), START, END)
    assert [i["n"] for i in result] == [140, 150, 160, 100, 110, 120, 130]


@pytest.mark.parametrize(
    "instant,expected",
    [
        # 22:30 UTC on the 10th is already the 11th in Rome (summer time, UTC+2).
        (datetime(2026, 7, 10, 22, 30, tzinfo=UTC), date(2026, 7, 11)),
        # 21:59 UTC is still the 10th.
        (datetime(2026, 7, 10, 21, 59, tzinfo=UTC), date(2026, 7, 10)),
        # Midnight UTC is 02:00 in Rome: same day, nothing changes.
        (datetime(2026, 7, 11, 0, 0, tzinfo=UTC), date(2026, 7, 11)),
        # Winter time (UTC+1): 23:30 UTC is already the next day.
        (datetime(2026, 1, 10, 23, 30, tzinfo=UTC), date(2026, 1, 11)),
        (datetime(2026, 1, 10, 22, 59, tzinfo=UTC), date(2026, 1, 10)),
    ],
)
def test_rome_today_follows_rome_not_utc(instant, expected):
    assert rome_today(instant) == expected
