"""Texts of the emails sent by the app, in Italian."""

from app.email.base import EmailMessage


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
