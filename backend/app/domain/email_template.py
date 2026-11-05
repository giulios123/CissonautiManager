"""Rules of the editable registration email: placeholders and the default texts.

Pure functions, no database. The admin writes a subject, a text and the sentence printed on the
image; `{first_name}`-style placeholders are replaced when the email is sent.
"""

import re
from collections.abc import Mapping

PLACEHOLDERS = ("first_name", "last_name", "event", "start_date", "end_date")

_TOKEN = re.compile(r"\{([^{}]*)\}")

DEFAULT_CARD_TEXT = {
    "it": "Sono {first_name} {last_name} e sarò a {event} dal {start_date} al {end_date}",
    "en": "I'm {first_name} {last_name} and I'll be at {event} from {start_date} to {end_date}",
}
DEFAULT_SUBJECT = {
    "it": "Iscrizione al {event}",
    "en": "Registration for {event}",
}
DEFAULT_BODY = {
    "it": "Ciao {first_name},\n\ngrazie per esserti iscritto al {event}!",
    "en": "Hi {first_name},\n\nthank you for signing up for {event}!",
}

CARD_POSITIONS = ("top", "center", "bottom")
DEFAULT_CARD_COLOR = "#ffffff"
DEFAULT_CARD_POSITION = "bottom"
_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def unknown_placeholders(text: str) -> list[str]:
    """Names between braces that are not one of PLACEHOLDERS, in order, without repeats."""
    seen: list[str] = []
    for name in _TOKEN.findall(text):
        if name not in PLACEHOLDERS and name not in seen:
            seen.append(name)
    return seen


def render(text: str, values: Mapping[str, str]) -> str:
    """Replaces the known placeholders; anything else is left as written."""
    return _TOKEN.sub(lambda match: values.get(match.group(1), match.group(0)), text)


def is_valid_color(value: str) -> bool:
    return bool(_COLOR.match(value))
