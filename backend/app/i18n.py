"""Server messages in Italian and English, chosen by the language of the request.

The language of a request comes from `Accept-Language` (the frontend sends `it` or `en`) and is
kept in a context variable, so code deep in a service can say `t("booking.not_editable")` without
passing the language around. Emails and jobs have no request: they pass the participant's
language explicitly.
"""

import re
from contextvars import ContextVar
from urllib.parse import parse_qs

from starlette.types import ASGIApp, Receive, Scope, Send

from app.admin_texts import ADMIN_MESSAGES, LABELS_EN
from app.email_texts import EMAIL_MESSAGES

LOCALES = ("it", "en")
DEFAULT_LOCALE = "it"

_current: ContextVar[str] = ContextVar("locale", default=DEFAULT_LOCALE)


def normalize_locale(value: str | None) -> str:
    """`it` or `en`; anything else falls back to Italian."""
    return value if value in LOCALES else DEFAULT_LOCALE


def parse_accept_language(header: str | None) -> str:
    """The first supported language of an Accept-Language header, by quality then order."""
    if not header:
        return DEFAULT_LOCALE
    candidates: list[tuple[float, int, str]] = []
    for position, part in enumerate(header.split(",")):
        tag, _, params = part.strip().partition(";")
        language = tag.strip().lower().split("-")[0]
        if language not in LOCALES:
            continue
        quality = 1.0
        match = re.search(r"q=([0-9.]+)", params)
        if match:
            try:
                quality = float(match.group(1))
            except ValueError:
                quality = 0.0
        if quality > 0:
            candidates.append((-quality, position, language))
    return min(candidates)[2] if candidates else DEFAULT_LOCALE


def current_locale() -> str:
    return _current.get()


class LocaleMiddleware:
    """Sets the language of the request from Accept-Language (pure ASGI, so the context holds)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        header = next(
            (v.decode("latin-1") for k, v in scope["headers"] if k == b"accept-language"), None
        )
        # A plain download link cannot send headers: `?lang=en` in the address says it instead.
        asked = parse_qs(scope.get("query_string", b"").decode("latin-1")).get("lang", [None])[0]
        locale = asked if asked in LOCALES else parse_accept_language(header)
        token = _current.set(locale)
        try:
            await self.app(scope, receive, send)
        finally:
            _current.reset(token)


def tr(text: str, locale: str | None = None) -> str:
    """A fixed Italian label (CSV header, report row...) in the language. Text with no English
    version, such as names typed by people, is returned as it is."""
    if normalize_locale(locale or current_locale()) == "en":
        return LABELS_EN.get(text, text)
    return text


def channel_label(code: str, stored: str, locale: str | None = None) -> str:
    """Name of a payment channel in the language. Channels the catalog does not know keep the
    label stored with them."""
    key = f"channel.{code}"
    return t(key, locale) if key in MESSAGES else stored


def t(key: str, locale: str | None = None, **params: object) -> str:
    """The message `key` in `locale` (default: the language of the request)."""
    texts = MESSAGES[key]
    text = texts[normalize_locale(locale or current_locale())]
    return text.format(**params) if params else text


# key -> {language: text}. `{name}` are placeholders filled by `t(key, name=...)`.
MESSAGES: dict[str, dict[str, str]] = {
    "legal.bilingual_required": {
        "it": "Inserisci il testo completo sia in italiano sia in inglese.",
        "en": "Enter the complete text in both Italian and English.",
    },
    "collection.terms_required": {
        "it": "Per il pagamento diretto indica costo e istruzioni con il destinatario.",
        "en": "For direct payment, provide the cost and instructions including the recipient.",
    },
    "collection.organizer": {"it": "Organizzatori", "en": "Organizers"},
    "collection.provider": {"it": "Erogatore", "en": "Provider"},
    "activity.invalid_time": {
        "it": "Scegli inizio e fine nella fascia; la fine deve seguire l'inizio.",
        "en": "Choose start and end within the time slot; the end must follow the start.",
    },
    "activity.bilingual_required": {
        "it": "Inserisci titolo e descrizione non vuoti sia in italiano sia in inglese.",
        "en": "Enter a non-empty title and description in both Italian and English.",
    },
    "activity.bilingual_description": {
        "it": "Inserisci una descrizione non vuota in italiano e in inglese.",
        "en": "Enter a non-empty description in both Italian and English.",
    },
    # --- edition and settings
    "edition.not_configured_first": {
        "it": "Configura prima l'edizione",
        "en": "Set up the edition first",
    },
    "edition.none": {"it": "Nessuna edizione configurata", "en": "No edition configured"},
    "edition.logo_none": {"it": "Nessun logo configurato", "en": "No logo configured"},
    "edition.both_dates": {
        "it": "Indica sia la data di inizio sia quella di fine",
        "en": "Enter both the start and the end date",
    },
    "edition.end_before_start": {
        "it": "La data di fine non può precedere quella di inizio",
        "en": "The end date can't be before the start date",
    },
    "edition.too_long": {
        "it": "L'edizione non può durare più di 60 giorni",
        "en": "The edition can't last more than 60 days",
    },
    "edition.time_order": {
        "it": "L'orario di inizio deve precedere quello di fine",
        "en": "The start time must be before the end time",
    },
    "edition.days_in_use": {
        "it": "Non puoi togliere giorni con slot già prenotati: {days}",
        "en": "You can't remove days that have booked slots: {days}",
    },
    "confirmation_policy.preview_changed": {
        "it": "I dati sono cambiati. Ricarica l'anteprima prima di applicare.",
        "en": "The data has changed. Refresh the preview before applying.",
    },
    "confirmation_policy.preview_blocked": {
        "it": "Risolvi i dati segnalati nell'anteprima prima di applicare la regola.",
        "en": "Resolve the issues shown in the preview before applying the rule.",
    },
    "confirmation_policy.already_active": {
        "it": "La nuova regola di conferma è già attiva.",
        "en": "The new confirmation rule is already active.",
    },
    "included_meals.policy_unavailable": {
        "it": "Attiva prima la conferma sulla quota per configurare i pasti compresi.",
        "en": "Activate registration-fee confirmation before configuring included meals.",
    },
    "included_meals.preview_changed": {
        "it": "I dati sono cambiati. Ricarica l'anteprima prima di applicare.",
        "en": "The data changed. Refresh the preview before applying.",
    },
    "benefit.not_found": {
        "it": "Benefit non trovato per questa edizione.",
        "en": "Benefit not found for this edition.",
    },
    # --- activities (admin)
    "activity.outside_edition": {
        "it": "Il giorno deve essere tra le date dell'edizione",
        "en": "The day must fall within the edition dates",
    },
    "activity.fixed_with_people": {
        "it": "Con persone già iscritte non si cambiano giorno e fascia",
        "en": "With people already signed up, day and time slot can't be changed",
    },
    "activity.capacity_below_people": {
        "it": "La capienza non può scendere sotto il numero di iscritti",
        "en": "Capacity can't go below the number of people signed up",
    },
    "activity.has_people": {
        "it": "Un'attività con iscritti non si elimina",
        "en": "An activity with people signed up can't be deleted",
    },
    "activity.not_found": {"it": "Attività non trovata", "en": "Activity not found"},
    # --- admins
    "admin.already": {
        "it": "Questa persona è già admin.",
        "en": "This person is already an admin.",
    },
    "admin.need_name": {
        "it": "Questa email non è ancora registrata: scrivi anche nome e cognome.",
        "en": "This email is not registered yet: please also enter first and last name.",
    },
    "admin.not_found": {"it": "Admin non trovato.", "en": "Admin not found."},
    "admin.remove_self": {
        "it": "Non puoi rimuovere te stesso: chiedi a un altro admin.",
        "en": "You can't remove yourself: ask another admin.",
    },
    "admin.remove_seed": {
        "it": (
            "Questo admin è quello iniziale, definito dalla variabile ADMIN_EMAIL: "
            "per cambiarlo si modifica la configurazione."
        ),
        "en": (
            "This is the initial admin, set by the ADMIN_EMAIL variable: "
            "to change it, edit the configuration."
        ),
    },
    "admin.remove_last": {
        "it": "Deve restare almeno un admin.",
        "en": "At least one admin must remain.",
    },
    "admin.remove_generic": {
        "it": "Non si può rimuovere questo admin.",
        "en": "This admin can't be removed.",
    },
    # --- people, registrations, payments (admin)
    "person.not_found": {"it": "Persona non trovata", "en": "Person not found"},
    "plus_one.needs_inviter": {
        "it": "Per verificare un +1 serve che la persona abbia indicato chi l'ha invitata",
        "en": "To verify a +1 the person must have said who invited them",
    },
    "waitlist.entry_not_found": {
        "it": "Voce della lista non trovata",
        "en": "Waitlist entry not found",
    },
    "booking.not_found": {"it": "Iscrizione non trovata", "en": "Registration not found"},
    "booking.none": {
        "it": "Non hai ancora un'iscrizione",
        "en": "You don't have a registration yet",
    },
    "booking.not_editable": {
        "it": "Questa iscrizione non si può più modificare",
        "en": "This registration can no longer be changed",
    },
    "booking.not_cancellable": {
        "it": "Questa iscrizione non si può più disdire",
        "en": "This registration can no longer be cancelled",
    },
    "booking.reactivate_only_expired": {
        "it": "Si può riattivare solo una prenotazione scaduta",
        "en": "Only an expired booking can be reactivated",
    },
    "booking.reactivate_other_active": {
        "it": (
            "Questa persona ha già un'altra iscrizione attiva: non si può riattivare anche questa"
        ),
        "en": (
            "This person already has another active registration: this one can't be reactivated too"
        ),
    },
    "refund.only_cancelled": {
        "it": "Si può registrare un rimborso solo su una disdetta richiesta",
        "en": "A refund can only be recorded on a requested cancellation",
    },
    "refund.too_high": {
        "it": "Il rimborso non può superare quanto versato ({amount})",
        "en": "The refund can't exceed the amount paid ({amount})",
    },
    "field.required": {
        "it": "Questo campo non può essere vuoto",
        "en": "This field can't be empty",
    },
    "email.in_use": {
        "it": "Questa email è già usata da un'altra persona",
        "en": "This email is already used by another person",
    },
    "hold.extend_only_pending": {
        "it": "Si può prorogare solo un blocco in attesa di pagamento",
        "en": "Only a hold awaiting payment can be extended",
    },
    "hold.later": {
        "it": "La nuova scadenza deve essere successiva a quella attuale",
        "en": "The new deadline must be later than the current one",
    },
    "payment.not_found": {"it": "Pagamento non trovato", "en": "Payment not found"},
    "payment.balance_changed": {
        "it": "Il saldo è cambiato. Aggiorna i dati prima di registrare il pagamento.",
        "en": "The balance changed. Refresh the details before recording the payment.",
    },
    "payment.retry_conflict": {
        "it": (
            "Questo tentativo è già associato a un pagamento diverso. "
            "Ripeti la richiesta originale senza modificarla."
        ),
        "en": (
            "This attempt is already linked to a different payment. "
            "Retry the original request without changing it."
        ),
    },
    "payment.already_voided": {
        "it": "Questo pagamento è già annullato",
        "en": "This payment is already voided",
    },
    # --- slots, meals, activities (participant and admin)
    "slot.not_found": {"it": "Slot non trovato", "en": "Slot not found"},
    "slots.invalid": {
        "it": "Gli slot scelti non sono validi",
        "en": "The chosen slots are not valid",
    },
    "slots.at_least_one": {
        "it": "Scegli almeno uno slot. Per rinunciare usa la disdetta",
        "en": "Choose at least one slot. To withdraw, cancel the registration",
    },
    "slots.past_day": {
        "it": "Gli slot di giorni già passati non si possono cambiare: scrivi a chi organizza",
        "en": "Slots on days that have already passed can't be changed: write to the organizers",
    },
    "slots.no_room": {
        "it": "Non c'è più posto in questi slot: {labels}",
        "en": "There is no more room in these slots: {labels}",
    },
    "slots.full_force": {
        "it": (
            "Questi slot sono al completo: {labels}. "
            "Per aggiungerli comunque spunta «Forza oltre la capienza»."
        ),
        "en": ("These slots are full: {labels}. To add them anyway, tick “Force over capacity”."),
    },
    "slots.full_choose_others": {
        "it": "Questi slot sono al completo: {labels}. Scegline altri.",
        "en": "These slots are full: {labels}. Choose others.",
    },
    "meals.admin_not_present": {
        "it": (
            "Un pasto si può dare solo nei giorni e nelle fasce in cui la persona è presente: "
            "aggiungi prima lo slot"
        ),
        "en": (
            "A meal can only be given on the days and time slots when the person is present: "
            "add the slot first"
        ),
    },
    "meals.not_allowed": {
        "it": "Puoi scegliere un pasto solo nei giorni e nelle fasce in cui sei presente",
        "en": "You can only choose a meal on the days and time slots when you are present",
    },
    "meals.past_day": {
        "it": "I pasti di giorni già passati non si possono cambiare: scrivi a chi organizza",
        "en": "Meals on days that have already passed can't be changed: write to the organizers",
    },
    "activities.invalid": {
        "it": "Le attività scelte non sono valide",
        "en": "The chosen activities are not valid",
    },
    "activities.full_force": {
        "it": (
            "Queste attività sono al completo: {names}. "
            "Per aggiungerle comunque spunta «Forza oltre la capienza»."
        ),
        "en": (
            "These activities are full: {names}. To add them anyway, tick “Force over capacity”."
        ),
    },
    "activities.admin_not_present": {
        "it": (
            "La persona non è presente nel momento di queste attività: {names}. "
            "Aggiungi prima lo slot."
        ),
        "en": (
            "The person is not present at the time of these activities: {names}. "
            "Add the slot first."
        ),
    },
    "activities.full": {
        "it": "Queste attività sono al completo: {names}.",
        "en": "These activities are full: {names}.",
    },
    "activities.past_day": {
        "it": "Le attività di giorni già passati non si possono cambiare: scrivi a chi organizza.",
        "en": (
            "Activities on days that have already passed can't be changed: write to the organizers."
        ),
    },
    "activities.not_present": {
        "it": "Puoi aderire solo alle attività dei momenti in cui sei presente: {names}.",
        "en": "You can only join activities at times when you are present: {names}.",
    },
    # --- health data, contributions
    "health.consent_required": {
        "it": (
            "Per salvare allergie e intolleranze serve il consenso al trattamento dei dati sanitari"
        ),
        "en": (
            "To save allergies and intolerances you must consent to the processing of health data"
        ),
    },
    "health.consent_outdated": {
        "it": (
            "Il testo del consenso è stato aggiornato: "
            "ricarica la pagina, rileggilo e conferma di nuovo"
        ),
        "en": (
            "The consent text has been updated: reload the page, read it again and confirm again"
        ),
    },
    "health.not_available": {
        "it": "Per ora non si possono indicare allergie: scrivi a chi organizza",
        "en": "Allergies can't be entered for now: write to the organizers",
    },
    "consent.association_not_found": {
        "it": "Non risulti associato all'edizione attiva",
        "en": "You are not associated with the active edition",
    },
    "consent.kind_not_found": {
        "it": "Finalità di consenso non trovata",
        "en": "Consent purpose not found",
    },
    "consent.changed": {
        "it": "La scelta o il testo sono cambiati. Ricarica e controlla di nuovo.",
        "en": "The choice or text has changed. Reload and review it again.",
    },
    "consent.text_unavailable": {
        "it": "Il testo completo in italiano e inglese non è disponibile.",
        "en": "The complete text in Italian and English is unavailable.",
    },
    "privacy.acceptance_required": {
        "it": "Leggi e accetta la nuova informativa privacy prima di modificare l'iscrizione.",
        "en": "Read and accept the updated privacy notice before changing your registration.",
    },
    "privacy.version_changed": {
        "it": "L'informativa è cambiata. Ricarica la pagina e leggi la versione corrente.",
        "en": "The privacy notice has changed. Reload the page and read the current version.",
    },
    "contribution.title_required": {
        "it": "Scrivi un titolo per il tuo contributo",
        "en": "Write a title for your contribution",
    },
    "contribution.invalid_kind": {
        "it": "Scegli se è un talk, un tema o una competenza",
        "en": "Choose whether it is a talk, a topic or a skill",
    },
    "contribution.not_found": {"it": "Contributo non trovato", "en": "Contribution not found"},
    # --- waitlist (participant)
    "waitlist.register_first": {
        "it": "Prima iscriviti al camp dal modulo di iscrizione",
        "en": "Register for the camp with the registration form first",
    },
    "waitlist.not_listed": {
        "it": "Non risulti in questa lista",
        "en": "You are not on this list",
    },
    "waitlist.not_full": {
        "it": "Lo slot ha ancora posti liberi: prenotalo direttamente",
        "en": "The slot still has free places: book it directly",
    },
    "waitlist.list_full": {
        "it": "La lista d'attesa di questo slot è completa",
        "en": "This slot's waitlist is full",
    },
    "waitlist.already_booked": {"it": "Hai già questo slot", "en": "You already have this slot"},
    "waitlist.already_listed": {
        "it": "Sei già in lista per questo slot",
        "en": "You are already on the list for this slot",
    },
    "waitlist.past_day": {
        "it": "Il giorno di questo slot è già passato",
        "en": "This slot's day has already passed",
    },
    # --- payment channels (their codes are fixed)
    "channel.iban": {"it": "Bonifico (IBAN)", "en": "Bank transfer (IBAN)"},
    # --- sign-up and sign-in
    "register.slots_required": {"it": "Scegli almeno uno slot", "en": "Choose at least one slot"},
    "register.privacy_required": {
        "it": "Per iscriverti devi accettare l'informativa privacy",
        "en": "To sign up you must accept the privacy notice",
    },
    "register.disclaimer_required": {
        "it": "Per iscriverti devi accettare lo scarico di responsabilità",
        "en": "To sign up you must accept the liability waiver",
    },
    "profile.invalid_telegram": {
        "it": "Inserisci un @username Telegram oppure dichiara che non lo possiedi.",
        "en": "Enter a Telegram @username or state that you do not have one.",
    },
    "profile.invalid_linkedin": {
        "it": "Inserisci un URL HTTPS LinkedIn oppure dichiara che non lo possiedi.",
        "en": "Enter an HTTPS LinkedIn URL or state that you do not have one.",
    },
    "profile.invalid_municipality": {
        "it": "Il comune, la provincia e il codice ISTAT non corrispondono.",
        "en": "The municipality, province and ISTAT code do not match.",
    },
    "profile.province_required": {
        "it": "Per un comune italiano non presente nell'elenco, indica la provincia.",
        "en": "For an Italian municipality missing from the list, enter its province.",
    },
    "profile.required": {
        "it": "Completa tutti i campi obbligatori del profilo.",
        "en": "Complete all required profile fields.",
    },
    "profile.no_active_edition": {
        "it": "Non c'è un'edizione attiva.",
        "en": "There is no active edition.",
    },
    "register.closed": {"it": "Le iscrizioni non sono aperte", "en": "Registrations are not open"},
    "register.legal_outdated": {
        "it": "I testi legali sono stati aggiornati: ricarica la pagina e rileggili",
        "en": "The legal texts have been updated: reload the page and read them again",
    },
    "register.slot_freed": {
        "it": (
            "Nel frattempo si è liberato un posto in uno slot che avevi messo in lista: "
            "ricarica la pagina e prenotalo direttamente."
        ),
        "en": (
            "In the meantime a place has opened up in a slot you had put on the list: "
            "reload the page and book it directly."
        ),
    },
    "register.list_filled": {
        "it": "Nel frattempo una lista d'attesa si è riempita: ricarica la pagina e riprova.",
        "en": "In the meantime a waitlist has filled up: reload the page and try again.",
    },
    "register.in_progress": {
        "it": "Esiste già una richiesta in corso, riprova tra poco",
        "en": "A request is already in progress, try again in a moment",
    },
    "register.already": {
        "it": "Risulti già iscritto. Ti abbiamo inviato un link per entrare.",
        "en": "You are already registered. We've sent you a link to sign in.",
    },
    "register.waitlisted": {
        "it": "Sei in lista d'attesa. Ti abbiamo inviato un link per entrare.",
        "en": "You are on the waitlist. We've sent you a link to sign in.",
    },
    "register.known_account_check_email": {
        "it": "Per la causale e i dettagli, controlla l'email che ti abbiamo inviato.",
        "en": "Check the email we sent you for the payment reference and details.",
    },
    "register.optional_consent_invalid": {
        "it": "Una scelta facoltativa non corrisponde a un testo disponibile. Ricarica la pagina.",
        "en": "An optional choice does not match an available text. Reload the page.",
    },
    "auth.link_sent": {
        "it": "Se l'email è registrata riceverai un link per entrare.",
        "en": "If the email is registered you'll receive a link to sign in.",
    },
    "auth.link_invalid": {"it": "Link non valido o scaduto", "en": "Invalid or expired link"},
    "auth.bad_credentials": {
        "it": "Email o password non corretti",
        "en": "Wrong email or password",
    },
}

MESSAGES.update(EMAIL_MESSAGES)
MESSAGES.update(ADMIN_MESSAGES)
