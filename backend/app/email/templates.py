"""Texts of the emails sent by the app, in Italian and English.

Every email is written in the language of its recipient (`participant.locale`). The wording lives
in `app/email_texts.py`; this module only assembles it.
"""

import html
import re

from app.email.base import (
    EmailAttachment,
    EmailMessage,
    EmailTexts,
    RegistrationExtras,
)
from app.i18n import channel_label, normalize_locale, t
from app.models import Booking, Participant, PaymentChannel, Slot, slot_sort_key
from app.presence_summary import format_presence_summary
from app.timefmt import format_deadline, format_euro, format_slot

CARD_CONTENT_ID = "registration-card"


def _greeting(first_name: str, loc: str) -> str:
    return t("email.greeting", loc, first_name=first_name) + "\n\n"


def _personal_link(link: str, loc: str) -> str:
    return t("email.personal_link", loc, link=link) + "\n"


def _manage_link(link: str, loc: str) -> str:
    return t("email.manage_link", loc, link=link) + "\n"


def _opening(texts: EmailTexts, first_name: str, loc: str, key: str) -> str:
    """The greeting and first sentence: what the organizers wrote, or the standard wording."""
    return texts.body or (_greeting(first_name, loc) + t(key, loc)).rstrip("\n")


def _subject(texts: EmailTexts, key: str, loc: str) -> str:
    return texts.subject or t(key, loc, event=texts.event_name)


def _slot_lines(slots: list[Slot], loc: str) -> str:
    return "\n".join(
        f"- {format_slot(s.date, s.period, s.start_time, s.end_time, loc)}"
        for s in sorted(slots, key=slot_sort_key)
    )


def _presence_block(booking: Booking, loc: str) -> str:
    """Format booked attendance when present; test bookings may have no slots."""
    if not booking.slots:
        return ""
    return format_presence_summary(booking.slots, booking.slots[0].edition.slots, loc) + "\n\n"


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
    to: str,
    first_name: str,
    removed: bool,
    left_waitlist: bool = False,
    locale: str = "it",
    texts: EmailTexts | None = None,
) -> EmailMessage:
    """Confirmation of a cancellation. `removed` means no payment was ever registered."""
    loc = normalize_locale(locale)
    texts = texts or EmailTexts()
    details = t("email.cancellation.removed" if removed else "email.cancellation.paid", loc)
    left = ("\n" + t("email.cancellation.left_waitlist", loc) + "\n") if left_waitlist else ""
    return EmailMessage(
        to=to,
        subject=_subject(texts, "email.cancellation.subject", loc),
        body=(
            _opening(texts, first_name, loc, "email.cancellation.body") + f"\n\n{details}\n{left}"
        ),
    )


_URL = re.compile(r"https?://[^\s<>\"]+")


def _html(text: str, card_alt: str | None = None, emphasized_lines: tuple[str, ...] = ()) -> str:
    """The plain text as a simple HTML email, with the optional picture on top."""
    rendered = []
    for line in text.splitlines():
        safe = html.escape(line.lstrip() if line.startswith("  ") else line)
        safe = _URL.sub(lambda m: f'<a href="{m.group(0)}">{m.group(0)}</a>', safe)
        if line.startswith("  "):
            rendered.append(f'<div style="font-size:13px;color:#5d6f73">{safe}</div>')
        elif line:
            content = f"<strong>{safe}</strong>" if line in emphasized_lines else safe
            rendered.append(f"<div>{content}</div>")
        else:
            rendered.append('<div style="height:12px"></div>')
    picture = ""
    if card_alt is not None:
        picture = (
            f'<p style="margin:0 0 16px"><img src="cid:{CARD_CONTENT_ID}" '
            f'alt="{html.escape(card_alt)}" '
            'style="display:block;width:100%;max-width:600px;height:auto;border-radius:8px"></p>'
        )
    return (
        '<div style="font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.5;'
        'color:#22363b;max-width:600px">' + picture + "<div>" + "".join(rendered) + "</div></div>"
    )


def registration_email(
    participant: Participant,
    booking: Booking,
    channels: list[PaymentChannel],
    link: str,
    waitlisted: list[Slot] | None = None,
    extras: RegistrationExtras | None = None,
    locale: str | None = None,
) -> EmailMessage:
    """`locale` overrides the language saved on the person for this one email (the form they
    just filled in); without it the saved language is used."""
    loc = normalize_locale(locale or participant.locale)
    extras = extras or RegistrationExtras()
    intro = extras.body or (
        _greeting(participant.first_name, loc).rstrip("\n")
        + "\n\n"
        + t("email.registration.thanks", loc, event=extras.event_name)
    )
    body = (
        intro
        + "\n\n"
        + t("email.registration.fee", loc, amount=format_euro(booking.amount_due_cents, loc))
        + "\n\n"
        + _presence_block(booking, loc)
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
    subject = extras.subject or t("email.registration.subject", loc, event=extras.event_name)
    return EmailMessage(
        to=participant.email,
        subject=subject,
        body=body,
        html=_html(
            body,
            extras.card_text if extras.card_png is not None else None,
            (t("email.registration.fee", loc, amount=format_euro(booking.amount_due_cents, loc)),),
        ),
        attachments=(
            (EmailAttachment("card.png", "image/png", extras.card_png, content_id=CARD_CONTENT_ID),)
            if extras.card_png is not None
            else ()
        ),
    )


def waitlist_joined_email(
    participant: Participant,
    waitlisted: list[Slot],
    link: str,
    locale: str | None = None,
    texts: EmailTexts | None = None,
) -> EmailMessage:
    """Sent to someone who registered only for full slots: they are on the waitlist."""
    loc = normalize_locale(locale or participant.locale)
    texts = texts or EmailTexts()
    return EmailMessage(
        to=participant.email,
        subject=_subject(texts, "email.waitlist_joined.subject", loc),
        body=(
            _opening(texts, participant.first_name, loc, "email.waitlist_joined.body")
            + "\n\n"
            + _waitlist_section(waitlisted, loc)
            + t("email.waitlist_joined.nothing_to_pay", loc)
            + "\n\n"
            + _personal_link(link, loc)
        ),
    )


def already_registered_email(
    participant: Participant,
    link: str,
    locale: str | None = None,
    texts: EmailTexts | None = None,
) -> EmailMessage:
    loc = normalize_locale(locale or participant.locale)
    texts = texts or EmailTexts()
    return EmailMessage(
        to=participant.email,
        subject=_subject(texts, "email.already.subject", loc),
        body=(
            _opening(texts, participant.first_name, loc, "email.already.body")
            + "\n\n"
            + t("email.already.link", loc, link=link)
            + "\n"
        ),
    )


def magic_link_email(
    participant: Participant, link: str, texts: EmailTexts | None = None
) -> EmailMessage:
    loc = normalize_locale(participant.locale)
    texts = texts or EmailTexts()
    return EmailMessage(
        to=participant.email,
        subject=_subject(texts, "email.magic.subject", loc),
        body=(
            _opening(texts, participant.first_name, loc, "email.magic.body")
            + "\n\n"
            + t("email.magic.link", loc, link=link)
        ),
    )


def payment_confirmation_email(
    booking: Booking, paid_cents: int, texts: EmailTexts | None = None
) -> EmailMessage:
    participant = booking.participant
    loc = normalize_locale(participant.locale)
    texts = texts or EmailTexts()
    opening = texts.body or (
        _greeting(participant.first_name, loc)
        + t("email.payment.body", loc, event=texts.event_name)
    ).rstrip("\n")
    return EmailMessage(
        to=participant.email,
        subject=_subject(texts, "email.payment.subject", loc),
        body=(
            opening
            + "\n\n"
            + t("email.payment.amount", loc, amount=format_euro(paid_cents, loc))
            + "\n\n"
            + _presence_block(booking, loc)
            + t("email.payment.see_you", loc)
            + "\n"
        ),
        html=_html(
            opening
            + "\n\n"
            + t("email.payment.amount", loc, amount=format_euro(paid_cents, loc))
            + "\n\n"
            + _presence_block(booking, loc)
            + t("email.payment.see_you", loc)
            + "\n",
            emphasized_lines=(t("email.payment.amount", loc, amount=format_euro(paid_cents, loc)),),
        ),
    )


def booking_confirmation_email(
    booking: Booking,
    paid_cents: int,
    login_url: str,
    texts: EmailTexts | None = None,
) -> EmailMessage:
    """Confirmation caused by a fee rule or booking change, without a new payment receipt."""
    participant = booking.participant
    loc = normalize_locale(participant.locale)
    texts = texts or EmailTexts()
    opening = texts.body or (
        _greeting(participant.first_name, loc)
        + t("email.booking_confirmation.body", loc, event=texts.event_name)
    ).rstrip("\n")
    fee_line = t(
        "email.booking_confirmation.fee",
        loc,
        amount=format_euro(booking.registration_fee_cents or 0, loc),
    )
    balance_cents = booking.amount_due_cents - paid_cents
    if balance_cents > 0:
        balance_line = t(
            "email.booking_confirmation.balance",
            loc,
            amount=format_euro(balance_cents, loc),
        )
    elif balance_cents < 0:
        balance_line = t(
            "email.booking_confirmation.credit",
            loc,
            amount=format_euro(-balance_cents, loc),
        )
    else:
        balance_line = t("email.booking_confirmation.no_balance", loc)
    body = (
        opening
        + "\n\n"
        + fee_line
        + "\n"
        + balance_line
        + "\n\n"
        + _presence_block(booking, loc)
        + t("email.booking_confirmation.access", loc, link=login_url)
        + "\n"
    )
    return EmailMessage(
        to=participant.email,
        subject=_subject(texts, "email.booking_confirmation.subject", loc),
        body=body,
        html=_html(body, emphasized_lines=(fee_line, balance_line)),
    )


def reminder_email(
    booking: Booking,
    kind: str,
    channels: list[PaymentChannel],
    balance_cents: int,
    login_url: str,
    texts: EmailTexts | None = None,
) -> EmailMessage:
    """Payment reminder. `kind` is "mid" (half of the hold) or "final" (24 hours before)."""
    participant = booking.participant
    loc = normalize_locale(participant.locale)
    texts = texts or EmailTexts()
    deadline = format_deadline(booking.hold_expires_at, loc)
    which = "final" if kind == "final" else "mid"
    return EmailMessage(
        to=participant.email,
        subject=_subject(texts, f"email.reminder.subject_{which}", loc),
        body=(
            _opening(texts, participant.first_name, loc, f"email.reminder.intro_{which}")
            + "\n\n"
            + t("email.hold_until", loc, deadline=deadline)
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
    texts: EmailTexts | None = None,
) -> EmailMessage:
    """A seat freed up and went to this person. `kind` is the promotion kind (see the domain)."""
    participant = booking.participant
    loc = normalize_locale(participant.locale)
    texts = texts or EmailTexts()
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
        subject=_subject(texts, "email.promoted.subject", loc),
        body=(
            _opening(texts, participant.first_name, loc, "email.promoted.body")
            + "\n\n"
            + t("email.promoted.slot", loc, label=label)
            + "\n\n"
            + t("email.promoted.fee", loc, amount=format_euro(booking.amount_due_cents, loc))
            + "\n"
            + t(
                "email.reminder.balance",
                loc,
                amount=format_euro(max(balance_cents, 0), loc),
            )
            + "\n\n"
            + _presence_block(booking, loc)
            + t("email.reference", loc, code=participant.personal_code)
            + "\n"
            + f"{deadline}\n"
            + f"{t('email.how_to_pay', loc)}\n{_payment_lines(channels, loc)}\n\n"
            + access
        ),
        html=_html(
            _opening(texts, participant.first_name, loc, "email.promoted.body")
            + "\n\n"
            + t("email.promoted.slot", loc, label=label)
            + "\n\n"
            + t("email.promoted.fee", loc, amount=format_euro(booking.amount_due_cents, loc))
            + "\n"
            + t(
                "email.reminder.balance",
                loc,
                amount=format_euro(max(balance_cents, 0), loc),
            )
            + "\n\n"
            + _presence_block(booking, loc)
            + t("email.reference", loc, code=participant.personal_code)
            + "\n"
            + deadline
            + "\n"
            + f"{t('email.how_to_pay', loc)}\n{_payment_lines(channels, loc)}\n\n"
            + access,
            emphasized_lines=(
                t("email.promoted.fee", loc, amount=format_euro(booking.amount_due_cents, loc)),
                t(
                    "email.reminder.balance",
                    loc,
                    amount=format_euro(max(balance_cents, 0), loc),
                ),
            ),
        ),
    )
