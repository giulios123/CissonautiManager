"""Editable texts of the emails: defaults, placeholders and composition. Pure, no database.

An email is: subject, opening, an automatic block with the booking data (never editable), closing.
The admin edits subject, opening and closing; an empty field means the default.
"""

import re
from dataclasses import dataclass

DEFAULT_EVENT_NAME = "Cissonauti Summer Camp"
SUBJECT_MAX = 200
TEXT_MAX = 4000
PLACEHOLDERS = ("{nome}", "{evento}")
DEFAULT_REGISTRATION_INTRO = (
    "Scegli i momenti in cui vuoi venire. Puoi scegliere più giorni e più fasce orarie."
)


@dataclass(frozen=True)
class EmailParts:
    subject: str
    intro: str
    closing: str


@dataclass(frozen=True)
class EmailKind:
    label: str
    # What the automatic block contains, shown to the admin next to the editable fields.
    automatic: str
    defaults: EmailParts


@dataclass(frozen=True)
class EmailTexts:
    """What an email needs besides its data: the event name and the resolved parts."""

    event_name: str
    parts: EmailParts


KINDS: dict[str, EmailKind] = {
    "registration": EmailKind(
        "Iscrizione",
        "I slot scelti, la quota, la causale, la scadenza del blocco, l'eventuale lista "
        "d'attesa, le istruzioni di pagamento e il link personale.",
        EmailParts(
            "Iscrizione a {evento}",
            "Ciao {nome},\n\ngrazie per esserti iscritto a {evento}!",
            "",
        ),
    ),
    "waitlist_joined": EmailKind(
        "Lista d'attesa",
        "Gli slot in lista d'attesa e il link personale.",
        EmailParts(
            "Sei in lista d'attesa a {evento}",
            "Ciao {nome},\n\ngli slot che hai scelto sono al completo: ti abbiamo messo in "
            "lista d'attesa.",
            "",
        ),
    ),
    "already_registered": EmailKind(
        "Già iscritto",
        "Il link personale con la sua durata.",
        EmailParts(
            "Sei già iscritto a {evento}",
            "Ciao {nome},\n\nrisulti già iscritto: non abbiamo creato una nuova iscrizione.",
            "",
        ),
    ),
    "magic_link": EmailKind(
        "Link di accesso",
        "Il link di accesso con la sua durata.",
        EmailParts(
            "Il tuo link di accesso a {evento}",
            "Ciao {nome},\n\napri questo link per entrare.",
            "",
        ),
    ),
    "payment_confirmation": EmailKind(
        "Pagamento ricevuto",
        "L'importo registrato e i slot della prenotazione.",
        EmailParts(
            "Pagamento ricevuto: sei dentro a {evento}!",
            "Ciao {nome},\n\nabbiamo registrato il tuo pagamento: la tua iscrizione a "
            "{evento} è confermata.",
            "Ci vediamo presto!",
        ),
    ),
    "reminder_mid": EmailKind(
        "Promemoria di pagamento",
        "La scadenza del blocco, quanto resta da versare, la causale, le istruzioni di "
        "pagamento e il link alla pagina personale.",
        EmailParts(
            "Promemoria: il tuo posto a {evento}",
            "Ciao {nome},\n\nti ricordiamo che il tuo posto è bloccato.",
            "Se hai già pagato, ignora questo messaggio: registreremo il pagamento appena "
            "possibile.",
        ),
    ),
    "reminder_final": EmailKind(
        "Ultimo promemoria (24 ore prima)",
        "La scadenza del blocco, quanto resta da versare, la causale, le istruzioni di "
        "pagamento e il link alla pagina personale.",
        EmailParts(
            "Ultimo promemoria: il tuo posto a {evento} sta per liberarsi",
            "Ciao {nome},\n\nmancano meno di 24 ore alla scadenza del blocco del tuo posto.",
            "Se hai già pagato, ignora questo messaggio: registreremo il pagamento appena "
            "possibile.",
        ),
    ),
    "waitlist_promoted": EmailKind(
        "Posto liberato",
        "Lo slot assegnato, i slot, la quota, quanto resta da versare, la causale, la "
        "scadenza, le istruzioni di pagamento e il link.",
        EmailParts(
            "Si è liberato un posto a {evento}",
            "Ciao {nome},\n\nsi è liberato un posto ed è tuo.",
            "",
        ),
    ),
    "cancellation": EmailKind(
        "Disdetta",
        "Cosa succede ai pagamenti (rimborso o nessuna azione) e l'uscita dalle liste d'attesa.",
        EmailParts(
            "Disdetta a {evento}",
            "Ciao {nome},\n\nabbiamo registrato la tua disdetta e i tuoi posti sono stati "
            "liberati.",
            "",
        ),
    ),
}


def resolve(kind: str, stored: dict[str, str | None] | None) -> EmailParts:
    """The parts to use: the stored ones, with the default for every empty field."""
    defaults = KINDS[kind].defaults
    stored = stored or {}

    def pick(field: str, default: str) -> str:
        value = stored.get(field)
        return value if value and value.strip() else default

    return EmailParts(
        subject=pick("subject", defaults.subject),
        intro=pick("intro", defaults.intro),
        closing=pick("closing", defaults.closing),
    )


def default_texts(kind: str, event_name: str = DEFAULT_EVENT_NAME) -> EmailTexts:
    return EmailTexts(event_name, KINDS[kind].defaults)


def fill(text: str, first_name: str, event_name: str) -> str:
    """Replace {nome} and {evento} in one pass: any other brace, and any placeholder found inside
    a name, stays as written."""
    values = {"{nome}": first_name, "{evento}": event_name}
    return re.sub(r"\{nome\}|\{evento\}", lambda match: values[match.group(0)], text)


def compose(parts: EmailParts, first_name: str, event_name: str, automatic: str) -> tuple[str, str]:
    """Subject and body: opening, the automatic block, closing."""
    subject = fill(parts.subject, first_name, event_name).replace("\n", " ").strip()
    blocks = [fill(parts.intro, first_name, event_name).strip(), automatic.strip()]
    closing = fill(parts.closing, first_name, event_name).strip()
    if closing:
        blocks.append(closing)
    return subject, "\n\n".join(block for block in blocks if block) + "\n"


def registration_intro(stored: str | None) -> str:
    """The paragraph above the sign-up form: the stored text, or the default when empty."""
    return stored.strip() if stored and stored.strip() else DEFAULT_REGISTRATION_INTRO


def validate(subject: str | None, intro: str | None, closing: str | None) -> str | None:
    """An error message in Italian, or None when the texts are acceptable."""
    if subject is not None and len(subject) > SUBJECT_MAX:
        return f"L'oggetto può avere al massimo {SUBJECT_MAX} caratteri"
    for text in (intro, closing):
        if text is not None and len(text) > TEXT_MAX:
            return f"Il testo può avere al massimo {TEXT_MAX} caratteri"
    return None
