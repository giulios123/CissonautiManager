"""The editable registration email: reading and saving what the organizers wrote, and building
the pieces (subject, text, picture) that registration_email puts into the message."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import utcnow
from app.domain.email_template import (
    DEFAULT_BODY,
    DEFAULT_CARD_COLOR,
    DEFAULT_CARD_POSITION,
    DEFAULT_CARD_TEXT,
    DEFAULT_FORM_INTRO,
    DEFAULT_SUBJECT,
    OTHER_EMAIL_KINDS,
    render,
)
from app.email.base import DEFAULT_EVENT_NAME, EmailTexts, RegistrationExtras
from app.email.card import render_card
from app.i18n import LOCALES, normalize_locale, t
from app.models import Edition, EmailTemplate, Participant, RegistrationCard
from app.timefmt import format_long_date

KIND_REGISTRATION = "registration"


def get_template(
    db: Session, edition_id: int, locale: str, kind: str = KIND_REGISTRATION
) -> EmailTemplate | None:
    return db.scalar(
        select(EmailTemplate).where(
            EmailTemplate.edition_id == edition_id,
            EmailTemplate.kind == kind,
            EmailTemplate.locale == locale,
        )
    )


def get_card(db: Session, edition_id: int) -> RegistrationCard | None:
    return db.scalar(select(RegistrationCard).where(RegistrationCard.edition_id == edition_id))


def placeholder_values(participant: Participant, edition: Edition, locale: str) -> dict[str, str]:
    return {
        "first_name": participant.first_name,
        "last_name": participant.last_name,
        "event": edition.name,
        "start_date": format_long_date(edition.start_date, locale) if edition.start_date else "",
        "end_date": format_long_date(edition.end_date, locale) if edition.end_date else "",
    }


def card_text_for(card: RegistrationCard | None, locale: str) -> str:
    """The sentence of the picture, with placeholders, in the language."""
    custom = (card.text_en if locale == "en" else card.text_it) if card else ""
    return custom.strip() or DEFAULT_CARD_TEXT[locale]


def registration_extras(
    db: Session,
    edition: Edition,
    participant: Participant,
    *,
    draw_card: bool = True,
    locale: str | None = None,
) -> RegistrationExtras:
    """The customized subject, text and picture for this person, in their language (or in
    `locale`, when the email goes out in another one than the one saved)."""
    locale = normalize_locale(locale or participant.locale)
    values = placeholder_values(participant, edition, locale)
    template = get_template(db, edition.id, locale)
    subject = render(template.subject, values).strip() if template and template.subject else None
    body = render(template.body, values).strip() if template and template.body.strip() else None
    card = get_card(db, edition.id)
    png = None
    text = ""
    if draw_card and card is not None and card.image:
        text = render(card_text_for(card, locale), values)
        png = render_card(
            card.image,
            text,
            card.text_color or DEFAULT_CARD_COLOR,
            card.text_position or DEFAULT_CARD_POSITION,
        )
    return RegistrationExtras(
        event_name=edition.name or DEFAULT_EVENT_NAME,
        subject=subject or None,
        body=body,
        card_png=png,
        card_text=text,
    )


def texts_for(
    db: Session,
    edition: Edition | None,
    participant: Participant,
    kind: str,
    locale: str | None = None,
) -> EmailTexts:
    """The event name and what the organizers wrote for one of the other emails, in the language
    of the person (or in `locale`). Without an edition, the standard wording."""
    if edition is None:
        return EmailTexts()
    loc = normalize_locale(locale or participant.locale)
    values = placeholder_values(participant, edition, loc)
    template = get_template(db, edition.id, loc, kind)
    subject = render(template.subject, values).strip() if template else ""
    body = render(template.body, values).strip() if template else ""
    return EmailTexts(
        event_name=edition.name or DEFAULT_EVENT_NAME, subject=subject or None, body=body or None
    )


def texts_for_booking(db: Session, booking, kind: str) -> EmailTexts:
    """`texts_for` for the person and edition of a booking."""
    return texts_for(db, db.get(Edition, booking.edition_id), booking.participant, kind)


# --- the other emails and the paragraph of the form: what the admin page reads and writes -----


def default_email(kind: str, locale: str) -> dict[str, str]:
    """The standard subject and opening of one of the other emails, placeholders unreplaced."""
    subject_key, body_key = OTHER_EMAIL_KINDS[kind]
    return {
        "subject": t(subject_key, locale, event="{event}"),
        "body": t("email.greeting", locale, first_name="{first_name}")
        + "\n\n"
        + t(body_key, locale, event="{event}"),
    }


def emails_view(db: Session, edition: Edition) -> dict:
    emails = {}
    for kind in OTHER_EMAIL_KINDS:
        templates = {}
        for locale in LOCALES:
            row = get_template(db, edition.id, locale, kind)
            templates[locale] = {
                "subject": row.subject if row else "",
                "body": row.body if row else "",
            }
        emails[kind] = {
            "templates": templates,
            "defaults": {locale: default_email(kind, locale) for locale in LOCALES},
        }
    return {
        "emails": emails,
        "form_intro": {
            "it": edition.registration_intro_it or "",
            "en": edition.registration_intro_en or "",
            "defaults": dict(DEFAULT_FORM_INTRO),
        },
    }


def save_email(
    db: Session,
    edition: Edition,
    admin: Participant,
    kind: str,
    templates: dict[str, dict[str, str]],
    now: datetime | None = None,
) -> None:
    now = now or utcnow()
    for locale in LOCALES:
        data = templates.get(locale, {})
        row = get_template(db, edition.id, locale, kind)
        if row is None:
            row = EmailTemplate(edition_id=edition.id, kind=kind, locale=locale)
            db.add(row)
        row.subject = data.get("subject", "").strip()
        row.body = data.get("body", "").strip()
        row.updated_at = now
        row.updated_by_id = admin.id
    db.commit()


def save_form_intro(db: Session, edition: Edition, it: str, en: str) -> None:
    edition.registration_intro_it = it.strip() or None
    edition.registration_intro_en = en.strip() or None
    db.commit()


def form_intro_for(edition: Edition, locale: str) -> str:
    """The paragraph above the sign-up form in a language: the organizers' or the standard one."""
    custom = edition.registration_intro_en if locale == "en" else edition.registration_intro_it
    return (custom or "").strip() or DEFAULT_FORM_INTRO[locale]


# --- what the admin page reads and writes -----------------------------------------------------


def settings_view(db: Session, edition: Edition) -> dict:
    card = get_card(db, edition.id)
    templates = {}
    for locale in LOCALES:
        template = get_template(db, edition.id, locale)
        templates[locale] = {
            "subject": template.subject if template else "",
            "body": template.body if template else "",
        }
    return {
        "templates": templates,
        "defaults": {
            locale: {
                "subject": DEFAULT_SUBJECT[locale],
                "body": DEFAULT_BODY[locale],
                "card_text": DEFAULT_CARD_TEXT[locale],
            }
            for locale in LOCALES
        },
        "card": {
            "has_image": bool(card and card.image),
            "text_it": card.text_it if card else "",
            "text_en": card.text_en if card else "",
            "text_color": card.text_color if card else DEFAULT_CARD_COLOR,
            "text_position": card.text_position if card else DEFAULT_CARD_POSITION,
            "updated_at": card.updated_at if card else None,
        },
    }


def save_settings(
    db: Session,
    edition: Edition,
    admin: Participant,
    templates: dict[str, dict[str, str]],
    card: dict[str, str],
    now: datetime | None = None,
) -> None:
    now = now or utcnow()
    for locale in LOCALES:
        data = templates.get(locale, {})
        row = get_template(db, edition.id, locale)
        if row is None:
            row = EmailTemplate(edition_id=edition.id, kind=KIND_REGISTRATION, locale=locale)
            db.add(row)
        row.subject = data.get("subject", "").strip()
        row.body = data.get("body", "").strip()
        row.updated_at = now
        row.updated_by_id = admin.id
    saved = _card_row(db, edition)
    saved.text_it = card.get("text_it", "").strip()
    saved.text_en = card.get("text_en", "").strip()
    saved.text_color = card.get("text_color", DEFAULT_CARD_COLOR)
    saved.text_position = card.get("text_position", DEFAULT_CARD_POSITION)
    saved.updated_at = now
    db.commit()


def _card_row(db: Session, edition: Edition) -> RegistrationCard:
    card = get_card(db, edition.id)
    if card is None:
        card = RegistrationCard(
            edition_id=edition.id,
            text_it="",
            text_en="",
            text_color=DEFAULT_CARD_COLOR,
            text_position=DEFAULT_CARD_POSITION,
        )
        db.add(card)
    return card


def set_image(
    db: Session, edition: Edition, png: bytes | None, now: datetime | None = None
) -> None:
    card = _card_row(db, edition)
    card.image = png
    card.updated_at = now or utcnow()
    db.commit()
