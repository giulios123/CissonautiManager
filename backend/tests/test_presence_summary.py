from datetime import date, time
from types import SimpleNamespace

from app.presence_summary import format_presence_summary


def slot(day: int, period: str, start: int, end: int):
    return SimpleNamespace(
        date=date(2026, 11, day),
        period=period,
        start_time=time(start),
        end_time=time(end),
    )


def test_summary_groups_days_and_hides_periods_for_complete_days():
    booked = [
        slot(20, "morning", 9, 13),
        slot(20, "afternoon", 14, 18),
        slot(22, "evening", 19, 0),
    ]
    schedule = [
        *booked,
        slot(20, "evening", 19, 0),
        slot(21, "morning", 9, 13),
    ]

    summary = format_presence_summary(booked, schedule, "it")

    assert "- ven 20 nov\n- dom 22 nov" in summary
    assert "dom 22 nov\n  Sera" in summary
    assert "sab 21 nov" not in summary
    assert "Mattina 09:00–13:00" in summary
    assert "Pomeriggio 14:00–18:00" in summary
    assert "Sera 19:00–00:00" in summary


def test_partial_days_and_variable_hours_have_one_legend_entry_per_interval():
    booked = [slot(20, "morning", 9, 13), slot(21, "morning", 10, 14)]
    schedule = [*booked, slot(20, "afternoon", 14, 18), slot(21, "evening", 19, 0)]

    summary = format_presence_summary(booked, schedule, "en")

    assert "Fri 20 Nov\n  Morning\n- Sat 21 Nov\n  Morning" in summary
    assert "Morning 09:00–13:00 (Fri 20 Nov)" in summary
    assert "Morning 10:00–14:00 (Sat 21 Nov)" in summary
    assert "Afternoon" not in summary
    assert "Evening" not in summary


def test_five_complete_days_stay_five_rows_and_evenings_are_included():
    dates = range(20, 25)
    booked = [
        slot(day, period, start, end)
        for day in dates
        for period, start, end in (
            ("morning", 9, 13),
            ("afternoon", 14, 18),
        )
    ]
    schedule = [
        slot(day, period, start, end)
        for day in dates
        for period, start, end in (
            ("morning", 9, 13),
            ("afternoon", 14, 18),
            ("evening", 19, 0),
        )
    ]

    partial_data_summary = format_presence_summary(booked, schedule, "it")
    all_periods_summary = format_presence_summary([*booked, *schedule[2::3]], schedule, "it")

    day_rows = partial_data_summary.split("\n\n")[0].splitlines()[2:]
    assert len(day_rows) == 5
    assert all("Mattina" not in row and "Pomeriggio" not in row for row in day_rows)
    assert partial_data_summary == all_periods_summary
