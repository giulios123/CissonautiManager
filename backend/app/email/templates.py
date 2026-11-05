"""Texts of the emails sent by the app, in Italian and English.

Every email is written in the language of its recipient (`participant.locale`). The wording lives
in `app/email_texts.py`; this module only assembles it.
"""

import html
import re

from app.email.base import EmailAttachment, EmailMessage, RegistrationExtras
from app.i18n import channel_label, normalize_locale, t
from app.models import Booking, Participant, PaymentChannel, Slot, slot_sort_key
from app.timefmt import format_deadline, format_euro, format_slot

# The brand name does not change with the language.
EVENT_NAME = "Cissonauti Summer Camp"
CARD_CONTENT_ID = "registration-card"


def _greeting(first_name: str, loc: str) -> str:
    return t("email.greeting", loc, first_name=first_name) + "\n\n"


def _personal_link(link: str, loc: str) -> str:
    return t("email.personal_link", loc, link=link) + "\n"


def _manage_link(link: str, loc: str) -> str:
    return t("email.manage_link", loc, link=link) + "\n"


def _slot_lines(slots: list[Slot], loc: str) -> str:
    return "\n".join(
        f"- {format_slot(s.date, s.period, s.start_time, s.end_time, loc)}"
        for s in sorted(slots, key=slot_sort_key)
    )


def _waitlist_section(waitlisted: list[Slot], loc: str) -> str:
    if not waitlisted:
        return ""
    return t("email.waitlist_section", loc, slots=_slot_lines(waitlisted, loc)) + "\n\n"


def _payment_lines(channels: list[PaymentChannel], loc: str) -> str:
    lines = [
        f"- {channel_label(c.code, c.label, loc)}: {c.instructions}".rstrip(": ") for c in channels
    ]
    return "\n".join(lines) or t("email.pay_default", loc)


def cancellation_email(
    to: str, first_name: str, removed: bool, left_waitlist: bool = False, locale: str = "it"
) -> EmailMessage:
    """Confirmation of a cancellation. `removed` means no payment was ever registered."""
    loc = normalize_locale(locale)
    details = t("email.cancellation.removed" if removed else "email.cancellation.paid", loc)
    left = ("\n" + t("email.cancellation.left_waitlist", loc) + "\n") if left_waitlist else ""
    return EmailMessage(
        to=to,
        subject=t("email.cancellation.subject", loc, event=EVENT_NAME),
        body=(
            _greeting(first_name, loc)
            + t("email.cancellation.body", loc)
            + f"\n\n{details}\n{left}"
        ),
    )


_URL = re.compile(r"https?://[^\s<>\"]+")


def _html(text: str, card_alt: str) -> str:
    """The plain text as a simple HTML email, with the picture on top. All text is escaped."""
    safe = html.escape(text)
    safe = _URL.sub(lambda m: f'<a href="{m.group(0)}">{m.group(0)}</a>', safe)
    picture = (
        f'<p style="margin:0 0 16px"><img src="cid:{CARD_CONTENT_ID}" '
        f'alt="{html.escape(card_alt)}" '
        'style="display:block;width:100%;max-width:600px;height:auto;border-radius:8px"></p>'
    )
    return (
        '<div style="font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.5;'
        'color:#22363b;max-width:600px">'
        + picture
        + "<div>"
        + safe.replace("\n", "<br>")
        + "</div></div>"
    )


def registration_email(
    participant: Participant,
    booking: Booking,
    channels: list[PaymentChannel],
    link: str,
    waitlisted: list[Slot] | None = None,
    extras: RegistrationExtras | None = None,
) -> EmailMessage:
    loc = normalize_locale(participant.locale)
    extras = extras or RegistrationExtras()
    intro = extras.body or (
        _greeting(participant.first_name, loc).rstrip("\n")
        + "\n\n"
        + t("email.registration.thanks", loc, event=EVENT_NAME)
    )
    body = (
        intro
        + "\n\n"
        + f"{t('email.your_slots', loc)}\n{_slot_lines(booking.slots, loc)}\n\n"
        + t("email.registration.fee", loc, amount=format_euro(booking.amount_due_cents, loc))
        + "\n"
        + t("email.reference", loc, code=participant.personal_code)
        + "\n"
        + t(
            "email.hold_until",
            loc,
            deadline=format_deadline(booking.hold_expires_at, loc),
        )
        + "\n\n"
        + _waitlist_section(waitlisted or [], loc)
        + f"{t('email.how_to_pay', loc)}\n{_payment_lines(channels, loc)}\n\n"
        + _personal_link(link, loc)
    )
    subject = extras.subject or t("email.registration.subject", loc, event=EVENT_NAME)
    if extras.card_png is None:
        return EmailMessage(to=participant.email, subject=subject, body=body)
    return EmailMessage(
        to=participant.email,
        subject=subject,
        body=body,
        html=_html(body, extras.card_text),
        attachments=(
            EmailAttachment("card.png", "image/png", extras.card_png, content_id=CARD_CONTENT_ID),
        ),
    )


def waitlist_joined_email(
    participant: Participant, waitlisted: list[Slot], link: str
) -> EmailMessage:
    """Sent to someone who registered only for full slots: they are on the waitlist."""
    loc = normalize_locale(participant.locale)
    return EmailMessage(
        to=participant.email,
        subject=t("email.waitlist_joined.subject", loc, event=EVENT_NAME),
        body=(
            _greeting(participant.first_name, loc)
            + t("email.waitlist_joined.body", loc)
            + "\n\n"
            + _waitlist_section(waitlisted, loc)
            + t("email.waitlist_joined.nothing_to_pay", loc)
            + "\n\n"
            + _personal_link(link, loc)
        ),
    )


def already_registered_email(participant: Participant, link: str) -> EmailMessage:
    loc = normalize_locale(participant.locale)
    return EmailMessage(
        to=participant.email,
        subject=t("email.already.subject", loc, event=EVENT_NAME),
        body=(
            _greeting(participant.first_name, loc) + t("email.already.body", loc, link=link) + "\n"
        ),
    )


def magic_link_email(participant: Participant, link: str) -> EmailMessage:
    loc = normalize_locale(participant.locale)
    return EmailMessage(
        to=participant.email,
        subject=t("email.magic.subject", loc),
        body=_greeting(participant.first_name, loc) + t("email.magic.body", loc, link=link),
    )


def payment_confirmation_email(booking: Booking, paid_cents: int) -> EmailMessage:
    participant = booking.participant
    loc = normalize_locale(participant.locale)
    return EmailMessage(
        to=participant.email,
        subject=t("email.payment.subject", loc),
        body=(
            _greeting(participant.first_name, loc)
            + t(
                "email.payment.body",
                loc,
                amount=format_euro(paid_cents, loc),
                event=EVENT_NAME,
            )
            + "\n\n"
            + f"{t('email.your_slots', loc)}\n{_slot_lines(booking.slots, loc)}\n\n"
            + t("email.payment.see_you", loc)
            + "\n"
        ),
    )


def reminder_email(
    booking: Booking,
    kind: str,
    channels: list[PaymentChannel],
    balance_cents: int,
    login_url: str,
) -> EmailMessage:
    """Payment reminder. `kind` is "mid" (half of the hold) or "final" (24 hours before)."""
    participant = booking.participant
    loc = normalize_locale(participant.locale)
    deadline = format_deadline(booking.hold_expires_at, loc)
    which = "final" if kind == "final" else "mid"
    return EmailMessage(
        to=participant.email,
        subject=t(f"email.reminder.subject_{which}", loc, event=EVENT_NAME),
        body=(
            _greeting(participant.first_name, loc)
            + t(f"email.reminder.intro_{which}", loc, deadline=deadline)
            + " "
            + t("email.reminder.release", loc)
            + "\n\n"
            + t("email.reminder.balance", loc, amount=format_euro(balance_cents, loc))
            + "\n"
            + t("email.reference", loc, code=participant.personal_code)
            + "\n\n"
            + f"{t('email.how_to_pay', loc)}\n{_payment_lines(channels, loc)}\n\n"
            + _manage_link(login_url, loc)
            + "\n"
            + t("email.reminder.already_paid", loc)
            + "\n"
        ),
    )


def waitlist_promoted_email(
    booking: Booking,
    slot: Slot,
    kind: str,
    channels: list[PaymentChannel],
    balance_cents: int,
    link: str,
) -> EmailMessage:
    """A seat freed up and went to this person. `kind` is the promotion kind (see the domain)."""
    participant = booking.participant
    loc = normalize_locale(participant.locale)
    label = format_slot(slot.date, slot.period, slot.start_time, slot.end_time, loc)
    if kind == "add_to_confirmed":
        deadline = t("email.promoted.stays_confirmed", loc) + "\n"
    else:
        deadline = (
            t("email.hold_until", loc, deadline=format_deadline(booking.hold_expires_at, loc))
            + "\n"
        )
    access = _personal_link(link, loc) if kind == "new_booking" else _manage_link(link, loc)
    return EmailMessage(
        to=participant.email,
        subject=t("email.promoted.subject", loc, event=EVENT_NAME),
        body=(
            _greeting(participant.first_name, loc)
            + t("email.promoted.body", loc, label=label)
            + "\n\n"
            + f"{t('email.your_slots', loc)}\n{_slot_lines(booking.slots, loc)}\n\n"
            + t("email.promoted.fee", loc, amount=format_euro(booking.amount_due_cents, loc))
            + "\n"
            + t(
                "email.reminder.balance",
                loc,
                amount=format_euro(max(balance_cents, 0), loc),
            )
            + "\n"
            + t("email.reference", loc, code=participant.personal_code)
            + "\n"
            + f"{deadline}\n"
            + f"{t('email.how_to_pay', loc)}\n{_payment_lines(channels, loc)}\n\n"
            + access
        ),
    )
