from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.i18n import current_locale, normalize_locale

ROME = ZoneInfo("Europe/Rome")

_WEEKDAYS = {
    "it": ["lun", "mar", "mer", "gio", "ven", "sab", "dom"],
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
}
_MONTHS_LONG = {
    "it": [
        "gennaio",
        "febbraio",
        "marzo",
        "aprile",
        "maggio",
        "giugno",
        "luglio",
        "agosto",
        "settembre",
        "ottobre",
        "novembre",
        "dicembre",
    ],
    "en": [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ],
}
_MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
_PERIODS = {
    "it": {"morning": "mattina", "afternoon": "pomeriggio", "evening": "sera"},
    "en": {"morning": "morning", "afternoon": "afternoon", "evening": "evening"},
}
_MEALS = {"it": {"lunch": "pranzo", "dinner": "cena"}, "en": {"lunch": "lunch", "dinner": "dinner"}}

STATUS_LABELS = {
    "it": {
        "in_attesa_pagamento": "In attesa di pagamento",
        "confermata": "Confermata",
        "scaduta": "Scaduta",
        "disdetta_richiesta": "Disdetta richiesta",
        "rimborsata": "Rimborsata",
        "in_lista": "Solo in lista d'attesa",
    },
    "en": {
        "in_attesa_pagamento": "Awaiting payment",
        "confermata": "Confirmed",
        "scaduta": "Expired",
        "disdetta_richiesta": "Cancellation requested",
        "rimborsata": "Refunded",
        "in_lista": "Waitlist only",
    },
}


def _loc(locale: str | None) -> str:
    """The given language or, when missing, the one of the request being served."""
    return normalize_locale(locale or current_locale())


def _period(period: str, loc: str) -> str:
    return _PERIODS[loc].get(period, period)


def period_label(period: str, locale: str | None = None) -> str:
    return _period(period, _loc(locale)).capitalize()


def status_label(status: str, locale: str | None = None) -> str:
    return STATUS_LABELS[_loc(locale)].get(status, status)


def to_rome(value: datetime) -> datetime:
    return value.astimezone(ROME)


def format_day_short(day: date, locale: str | None = None) -> str:
    """ "sab 10/07" in Italian, "Sat 10 Jul" in English."""
    loc = _loc(locale)
    weekday = _WEEKDAYS[loc][day.weekday()]
    if loc == "en":
        return f"{weekday} {day.day} {_MONTHS_EN[day.month - 1]}"
    return f"{weekday} {day.strftime('%d/%m')}"


def format_presence_day(day: date, locale: str | None = None) -> str:
    """Compact calendar date for attendance summaries: "ven 20 nov" / "Fri 20 Nov"."""
    loc = _loc(locale)
    weekday = _WEEKDAYS[loc][day.weekday()]
    month = _MONTHS_EN[day.month - 1] if loc == "en" else _MONTHS_LONG[loc][day.month - 1][:3]
    return f"{weekday} {day.day} {month}"


def format_deadline(value: datetime, locale: str | None = None) -> str:
    rome = to_rome(value)
    if _loc(locale) == "en":
        return f"{rome.day} {_MONTHS_EN[rome.month - 1]} {rome.year} at {rome:%H:%M}"
    return rome.strftime("%d/%m/%Y alle %H:%M")


def format_euro(cents: int, locale: str | None = None) -> str:
    if _loc(locale) == "en":
        sign = "-" if cents < 0 else ""
        return f"{sign}€{abs(cents) // 100}.{abs(cents) % 100:02d}"
    return f"{cents // 100},{cents % 100:02d} €"


def format_amount(cents: int) -> str:
    """Plain amount with a decimal comma and no currency symbol, for spreadsheets."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100},{cents % 100:02d}"


def format_slot(day: date, period: str, start: time, end: time, locale: str | None = None) -> str:
    loc = _loc(locale)
    label = _period(period, loc)
    return f"{format_day_short(day, loc)} {label} ({start:%H:%M}-{end:%H:%M})"


def meal_label(kind: str, locale: str | None = None) -> str:
    return _MEALS[_loc(locale)].get(kind, kind).capitalize()


def format_meal(day: date, kind: str, locale: str | None = None) -> str:
    loc = _loc(locale)
    joiner = "on" if loc == "en" else "di"
    return f"{_MEALS[loc].get(kind, kind)} {joiner} {format_day_short(day, loc)}"


def format_activity(title: str, day: date, period: str, locale: str | None = None) -> str:
    loc = _loc(locale)
    return f"{title} ({format_day_short(day, loc)} {_period(period, loc)})"


def format_long_date(day: date, locale: str | None = None) -> str:
    """ "10 luglio 2027" / "10 July 2027": the date as it is written in a sentence."""
    loc = _loc(locale)
    return f"{day.day} {_MONTHS_LONG[loc][day.month - 1]} {day.year}"
