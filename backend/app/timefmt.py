from datetime import date, datetime, time
from zoneinfo import ZoneInfo

ROME = ZoneInfo("Europe/Rome")

_WEEKDAYS = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]
_PERIODS = {"morning": "mattina", "afternoon": "pomeriggio"}


def to_rome(value: datetime) -> datetime:
    return value.astimezone(ROME)


def format_deadline(value: datetime) -> str:
    return to_rome(value).strftime("%d/%m/%Y alle %H:%M")


def format_euro(cents: int) -> str:
    return f"{cents // 100},{cents % 100:02d} €"


def format_slot(day: date, period: str, start: time, end: time) -> str:
    label = _PERIODS.get(period, period)
    return f"{_WEEKDAYS[day.weekday()]} {day.strftime('%d/%m')} {label} ({start:%H:%M}-{end:%H:%M})"
