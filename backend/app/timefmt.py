from datetime import date, datetime, time
from zoneinfo import ZoneInfo

ROME = ZoneInfo("Europe/Rome")

_WEEKDAYS = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]
_PERIODS = {"morning": "mattina", "afternoon": "pomeriggio", "evening": "sera"}


STATUS_LABELS = {
    "in_attesa_pagamento": "In attesa di pagamento",
    "confermata": "Confermata",
    "scaduta": "Scaduta",
    "disdetta_richiesta": "Disdetta richiesta",
    "rimborsata": "Rimborsata",
    "in_lista": "Solo in lista d'attesa",
}


def period_label(period: str) -> str:
    return _PERIODS.get(period, period).capitalize()


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def to_rome(value: datetime) -> datetime:
    return value.astimezone(ROME)


def format_deadline(value: datetime) -> str:
    return to_rome(value).strftime("%d/%m/%Y alle %H:%M")


def format_euro(cents: int) -> str:
    return f"{cents // 100},{cents % 100:02d} €"


def format_amount(cents: int) -> str:
    """Plain amount with a decimal comma and no currency symbol, for spreadsheets."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100},{cents % 100:02d}"


def format_slot(day: date, period: str, start: time, end: time) -> str:
    label = _PERIODS.get(period, period)
    return f"{_WEEKDAYS[day.weekday()]} {day.strftime('%d/%m')} {label} ({start:%H:%M}-{end:%H:%M})"


_MEALS = {"lunch": "pranzo", "dinner": "cena"}


def meal_label(kind: str) -> str:
    return _MEALS.get(kind, kind).capitalize()


def format_meal(day: date, kind: str) -> str:
    return f"{_MEALS.get(kind, kind)} di {_WEEKDAYS[day.weekday()]} {day.strftime('%d/%m')}"
