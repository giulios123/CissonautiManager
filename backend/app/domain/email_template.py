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

# The other emails the organizers can edit. Each one has a subject and an opening text (the
# greeting and first sentence); the data of the message always follows and is not editable.
# Maps the kind to the keys of its default subject and opening in `app/email_texts.py`.
OTHER_EMAIL_KINDS: dict[str, tuple[str, str]] = {
    "waitlist_joined": ("email.waitlist_joined.subject", "email.waitlist_joined.body"),
    "already_registered": ("email.already.subject", "email.already.body"),
    "magic_link": ("email.magic.subject", "email.magic.body"),
    "payment_confirmation": ("email.payment.subject", "email.payment.body"),
    "reminder_mid": ("email.reminder.subject_mid", "email.reminder.intro_mid"),
    "reminder_final": ("email.reminder.subject_final", "email.reminder.intro_final"),
    "waitlist_promoted": ("email.promoted.subject", "email.promoted.body"),
    "cancellation": ("email.cancellation.subject", "email.cancellation.body"),
}

# The paragraph above the sign-up form, until the organizers write their own.
DEFAULT_FORM_INTRO = {
    "it": "Scegli i momenti in cui vuoi venire. Puoi scegliere più giorni e più fasce orarie.",
    "en": "Choose when you want to come. You can pick several days and several time slots.",
}
FORM_INTRO_MAX = 2000

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
