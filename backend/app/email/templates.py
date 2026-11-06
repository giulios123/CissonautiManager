"""Texts of the emails sent by the app, in Italian.

Subject, opening and closing come from `EmailTexts` (editable by the admin, see
`domain/email_texts.py`); the block with the booking data is always built here.
"""

from app.domain.email_texts import EmailTexts, compose, default_texts
from app.email.base import EmailMessage
from app.models import Booking, Participant, PaymentChannel, Slot, slot_sort_key
from app.timefmt import format_deadline, format_euro, format_slot

LINK_VALIDITY = "vale 10 minuti"


def _message(
    kind: str, texts: EmailTexts | None, to: str, first_name: str, automatic: str
) -> EmailMessage:
    texts = texts or default_texts(kind)
    subject, body = compose(texts.parts, first_name, texts.event_name, automatic)
    return EmailMessage(to=to, subject=subject, body=body)


def cancellation_email(
    to: str,
    first_name: str,
    removed: bool,
    left_waitlist: bool = False,
    texts: EmailTexts | None = None,
) -> EmailMessage:
    """Confirmation of a cancellation. `removed` means no payment was ever registered."""
    if removed:
        details = (
            "Non risultano pagamenti, quindi non devi fare altro: l'iscrizione è stata "
            "annullata. Se cambi idea puoi iscriverti di nuovo quando vuoi."
        )
    else:
        details = (
            "Ci sono pagamenti registrati: chi organizza ti scriverà per il rimborso "
            "e segnerà la disdetta come conclusa."
        )
    if left_waitlist:
        details += "\n\nSei uscito anche dalle liste d'attesa in cui eri."
    return _message("cancellation", texts, to, first_name, details)


def _slot_lines(slots: list[Slot]) -> str:
    return "\n".join(
        f"- {format_slot(s.date, s.period, s.start_time, s.end_time)}"
        for s in sorted(slots, key=slot_sort_key)
    )


def _waitlist_section(waitlisted: list[Slot]) -> str:
    if not waitlisted:
        return ""
    return (
        f"Sei in lista d'attesa per:\n{_slot_lines(waitlisted)}\n"
        "Se si libera un posto ti scriviamo e lo slot diventa tuo.\n\n"
    )


def _pay_lines(channels: list[PaymentChannel]) -> str:
    return "\n".join(f"- {c.label}: {c.instructions}".rstrip(": ") for c in channels) or (
        "- Ti scriveremo le istruzioni appena possibile."
    )


def registration_email(
    participant: Participant,
    booking: Booking,
    channels: list[PaymentChannel],
    link: str,
    waitlisted: list[Slot] | None = None,
    texts: EmailTexts | None = None,
) -> EmailMessage:
    automatic = (
        f"I tuoi slot:\n{_slot_lines(booking.slots)}\n\n"
        f"Quota da versare: {format_euro(booking.amount_due_cents)}\n"
        f"Causale: {participant.personal_code}\n"
        f"Il posto è bloccato fino al {format_deadline(booking.hold_expires_at)}: "
        "senza pagamento entro quella data si libera.\n\n"
        f"{_waitlist_section(waitlisted or [])}"
        f"Come pagare:\n{_pay_lines(channels)}\n\n"
        f"Il tuo link personale ({LINK_VALIDITY}):\n{link}"
    )
    return _message("registration", texts, participant.email, participant.first_name, automatic)


def waitlist_joined_email(
    participant: Participant,
    waitlisted: list[Slot],
    link: str,
    texts: EmailTexts | None = None,
) -> EmailMessage:
    """Sent to someone who registered only for full slots: they are on the waitlist."""
    automatic = (
        f"{_waitlist_section(waitlisted)}"
        "Finché non si libera un posto non devi pagare nulla.\n\n"
        f"Il tuo link personale ({LINK_VALIDITY}):\n{link}"
    )
    return _message("waitlist_joined", texts, participant.email, participant.first_name, automatic)


def already_registered_email(
    participant: Participant, link: str, texts: EmailTexts | None = None
) -> EmailMessage:
    automatic = f"Per vedere la tua pagina personale apri questo link ({LINK_VALIDITY}):\n{link}"
    return _message(
        "already_registered", texts, participant.email, participant.first_name, automatic
    )


def magic_link_email(
    participant: Participant, link: str, texts: EmailTexts | None = None
) -> EmailMessage:
    automatic = f"{link}\n\nIl link {LINK_VALIDITY}."
    return _message("magic_link", texts, participant.email, participant.first_name, automatic)


def payment_confirmation_email(
    booking: Booking, paid_cents: int, texts: EmailTexts | None = None
) -> EmailMessage:
    participant = booking.participant
    automatic = (
        f"Pagamento registrato: {format_euro(paid_cents)}\n\n"
        f"I tuoi slot:\n{_slot_lines(booking.slots)}"
    )
    return _message(
        "payment_confirmation", texts, participant.email, participant.first_name, automatic
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
    automatic = (
        f"Il posto è bloccato fino al {format_deadline(booking.hold_expires_at)}: senza "
        "pagamento entro quella data si libera.\n\n"
        f"Ancora da versare: {format_euro(balance_cents)}\n"
        f"Causale: {participant.personal_code}\n\n"
        f"Come pagare:\n{_pay_lines(channels)}\n\n"
        f"Per vedere o modificare la tua iscrizione: {login_url}"
    )
    return _message(
        "reminder_final" if kind == "final" else "reminder_mid",
        texts,
        participant.email,
        participant.first_name,
        automatic,
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
    label = format_slot(slot.date, slot.period, slot.start_time, slot.end_time)
    if kind == "add_to_confirmed":
        deadline = (
            "La tua iscrizione resta confermata: versa la differenza con le stesse istruzioni."
        )
    else:
        deadline = (
            f"Il posto è bloccato fino al {format_deadline(booking.hold_expires_at)}: "
            "senza pagamento entro quella data si libera."
        )
    if kind == "new_booking":
        access = f"Il tuo link personale ({LINK_VALIDITY}):\n{link}"
    else:
        access = f"Per vedere o modificare la tua iscrizione: {link}"
    automatic = (
        f"Slot assegnato: {label}\n\n"
        f"I tuoi slot:\n{_slot_lines(booking.slots)}\n\n"
        f"Quota: {format_euro(booking.amount_due_cents)}\n"
        f"Ancora da versare: {format_euro(max(balance_cents, 0))}\n"
        f"Causale: {participant.personal_code}\n"
        f"{deadline}\n\n"
        f"Come pagare:\n{_pay_lines(channels)}\n\n"
        f"{access}"
    )
    return _message(
        "waitlist_promoted", texts, participant.email, participant.first_name, automatic
    )
