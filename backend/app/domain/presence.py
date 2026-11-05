"""Who is present when. Pure functions over (person, day, period) rows.

The evening of a whole day is derived, not stored (D-009): someone with both the morning and the
afternoon of a day is present that evening too, even if they did not book the evening slot.
"""

from collections import Counter, defaultdict
from collections.abc import Collection, Iterable
from dataclasses import dataclass
from datetime import date

from app.models import PERIOD_AFTERNOON, PERIOD_EVENING, PERIOD_MORNING


@dataclass(frozen=True)
class Presence:
    person_id: int
    day: date
    period: str
    derived: bool = False


@dataclass(frozen=True)
class DaySummary:
    day: date
    morning: int
    afternoon: int
    evening: int  # includes the derived evenings
    evening_derived: int
    people: int  # distinct people present at any time that day


def has_evening(periods: Collection[str]) -> bool:
    """Evening booked explicitly, or implied by booking the whole day."""
    return PERIOD_EVENING in periods or (PERIOD_MORNING in periods and PERIOD_AFTERNOON in periods)


def presences(booked: Iterable[tuple[int, date, str]]) -> list[Presence]:
    """Turn booked (person, day, period) rows into presences, adding the derived evenings.

    Callers pass only bookings that occupy seats: expired, cancelled and refunded ones are out.
    """
    by_person_day: dict[tuple[int, date], set[str]] = defaultdict(set)
    for person_id, day, period in booked:
        by_person_day[(person_id, day)].add(period)
    result: list[Presence] = []
    for (person_id, day), periods in sorted(
        by_person_day.items(), key=lambda kv: (kv[0][1], kv[0][0])
    ):
        result.extend(Presence(person_id, day, period) for period in sorted(periods))
        if has_evening(periods) and PERIOD_EVENING not in periods:
            result.append(Presence(person_id, day, PERIOD_EVENING, derived=True))
    return result


def presence_by_slot(rows: Iterable[Presence]) -> dict[tuple[date, str], list[Presence]]:
    grouped: dict[tuple[date, str], list[Presence]] = defaultdict(list)
    for row in rows:
        grouped[(row.day, row.period)].append(row)
    return dict(grouped)


def week_summary(rows: Iterable[Presence], days: Iterable[date]) -> list[DaySummary]:
    """One summary per day, in order; days without anyone are listed with zeros."""
    rows = list(rows)
    summaries = []
    for day in sorted(set(days)):
        today = [r for r in rows if r.day == day]
        per_period = Counter(r.period for r in today)
        summaries.append(
            DaySummary(
                day=day,
                morning=per_period[PERIOD_MORNING],
                afternoon=per_period[PERIOD_AFTERNOON],
                evening=per_period[PERIOD_EVENING],
                evening_derived=len([r for r in today if r.derived]),
                people=len({r.person_id for r in today}),
            )
        )
    return summaries
