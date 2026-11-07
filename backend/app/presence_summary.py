from collections import defaultdict
from collections.abc import Iterable
from datetime import date, time

from app.i18n import normalize_locale, t
from app.models import PERIOD_AFTERNOON, PERIOD_EVENING, PERIOD_MORNING, Slot, slot_sort_key
from app.timefmt import format_presence_day, period_label

PERIOD_ORDER = (PERIOD_MORNING, PERIOD_AFTERNOON, PERIOD_EVENING)


def format_presence_summary(slots: Iterable[Slot], schedule: Iterable[Slot], locale: str) -> str:
    loc = normalize_locale(locale)
    grouped: dict[date, set[str]] = defaultdict(set)
    for slot in slots:
        grouped[slot.date].add(slot.period)
    days = sorted(grouped)
    lines = [
        t(f"email.presence.heading.{'one' if len(days) == 1 else 'other'}", loc, count=len(days)),
        t("email.presence.note", loc),
    ]
    for day in days:
        periods = grouped[day]
        lines.append(f"- {format_presence_day(day, loc)}")
        if not (PERIOD_MORNING in periods and PERIOD_AFTERNOON in periods):
            labels = " · ".join(period_label(p, loc) for p in PERIOD_ORDER if p in periods)
            lines.append("  " + labels)

    dates = set(days)
    by_period: dict[str, dict[tuple[time, time], list[date]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for slot in sorted(schedule, key=slot_sort_key):
        booked_periods = grouped.get(slot.date, set())
        is_derived_evening = (
            slot.period == PERIOD_EVENING
            and PERIOD_MORNING in booked_periods
            and PERIOD_AFTERNOON in booked_periods
        )
        if slot.date in dates and (slot.period in booked_periods or is_derived_evening):
            by_period[slot.period][(slot.start_time, slot.end_time)].append(slot.date)
    hour_lines = []
    for period in PERIOD_ORDER:
        time_groups = by_period[period]
        for (start, end), period_dates in time_groups.items():
            show_dates = len(time_groups) > 1 or len(period_dates) < len(dates)
            date_text = ", ".join(format_presence_day(day, loc) for day in period_dates)
            suffix = f" ({date_text})" if show_dates else ""
            hour_lines.append(f"- {period_label(period, loc)} {start:%H:%M}–{end:%H:%M}{suffix}")
    if hour_lines:
        lines.extend(("", t("email.presence.hours", loc), *hour_lines))
    return "\n".join(lines)
