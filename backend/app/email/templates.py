"""Texts of the emails sent by the app, in Italian."""

from app.email.base import EmailMessage
from app.models import Booking, Participant, PaymentChannel, slot_sort_key
from app.timefmt import format_deadline, format_euro, format_slot


def cancellation_email(to: str, first_name: str, removed: bool) -> EmailMessage:
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
    return EmailMessage(
        to=to,
        subject="Disdetta al Cissonauti Summer Camp",
        body=(
            f"Ciao {first_name},\n\n"
            "abbiamo registrato la tua disdetta e i tuoi posti sono stati liberati.\n\n"
            f"{details}\n"
        ),
    )


def registration_email(
    participant: Participant, booking: Booking, channels: list[PaymentChannel], link: str
) -> EmailMessage:
    slots = "\n".join(
        f"- {format_slot(s.date, s.period, s.start_time, s.end_time)}"
        for s in sorted(booking.slots, key=slot_sort_key)
    )
    pay = "\n".join(f"- {c.label}: {c.instructions}".rstrip(": ") for c in channels) or (
        "- Ti scriveremo le istruzioni appena possibile."
    )
    return EmailMessage(
        to=participant.email,
        subject="Iscrizione al Cissonauti Summer Camp",
        body=(
            f"Ciao {participant.first_name},\n\n"
            "grazie per esserti iscritto al Cissonauti Summer Camp!\n\n"
            f"I tuoi slot:\n{slots}\n\n"
            f"Quota da versare: {format_euro(booking.amount_due_cents)}\n"
            f"Causale: {participant.personal_code}\n"
            f"Il posto è bloccato fino al {format_deadline(booking.hold_expires_at)}: "
            "senza pagamento entro quella data si libera.\n\n"
            f"Come pagare:\n{pay}\n\n"
            f"Il tuo link personale (vale 30 minuti, si usa una volta sola):\n{link}\n"
        ),
    )


def already_registered_email(participant: Participant, link: str) -> EmailMessage:
    return EmailMessage(
        to=participant.email,
        subject="Sei già iscritto al Cissonauti Summer Camp",
        body=(
            f"Ciao {participant.first_name},\n\n"
            "risulti già iscritto: non abbiamo creato una nuova iscrizione.\n"
            "Per vedere la tua pagina personale apri questo link "
            "(vale 30 minuti, si usa una volta sola):\n"
            f"{link}\n"
        ),
    )


def magic_link_email(participant: Participant, link: str) -> EmailMessage:
    return EmailMessage(
        to=participant.email,
        subject="Il tuo link di accesso ai Cissonauti",
        body=(
            f"Ciao {participant.first_name},\n\n"
            f"apri questo link per entrare: {link}\n\n"
            "Il link vale 30 minuti e si può usare una sola volta."
        ),
    )


def payment_confirmation_email(booking: Booking, paid_cents: int) -> EmailMessage:
    participant = booking.participant
    slots = "\n".join(
        f"- {format_slot(s.date, s.period, s.start_time, s.end_time)}"
        for s in sorted(booking.slots, key=slot_sort_key)
    )
    return EmailMessage(
        to=participant.email,
        subject="Pagamento ricevuto: sei dentro!",
        body=(
            f"Ciao {participant.first_name},\n\n"
            f"abbiamo registrato il tuo pagamento ({format_euro(paid_cents)}): "
            "la tua iscrizione al Cissonauti Summer Camp è confermata.\n\n"
            f"I tuoi slot:\n{slots}\n\nCi vediamo presto!\n"
        ),
    )
