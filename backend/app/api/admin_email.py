"""Admin endpoints of the editable registration email: texts, background picture, preview and a
test message to the admin who is editing."""

from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import get_db
from app.deps import get_email_sender, get_now, get_settings_dep, require_admin
from app.domain.email_template import (
    CARD_POSITIONS,
    DEFAULT_CARD_COLOR,
    DEFAULT_CARD_POSITION,
    FORM_INTRO_MAX,
    OTHER_EMAIL_KINDS,
    PLACEHOLDERS,
    is_valid_color,
    render,
    unknown_placeholders,
)
from app.email import EmailSender
from app.email.card import MAX_UPLOAD_BYTES, InvalidImage, normalize_image, render_card
from app.email.templates import registration_email
from app.i18n import normalize_locale, t
from app.models import Edition, Participant, slot_sort_key
from app.services import auth as auth_service
from app.services import edition as edition_service
from app.services import email_templates as service
from app.services.registration import enabled_channels

router = APIRouter(
    prefix="/api/admin/email/registration", tags=["admin"], dependencies=[Depends(require_admin)]
)

# The other emails and the paragraph of the sign-up form, edited from the same settings page.
texts_router = APIRouter(
    prefix="/api/admin/email", tags=["admin"], dependencies=[Depends(require_admin)]
)

Language = Literal["it", "en"]


def _braced(names) -> str:
    return ", ".join(f"{{{name}}}" for name in names)


def _unknown_message(unknown: list[str]) -> str:
    return t("emailtpl.unknown_placeholder", names=_braced(unknown), allowed=_braced(PLACEHOLDERS))


def _check_placeholders(text: str) -> str:
    unknown = unknown_placeholders(text)
    if unknown:
        raise ValueError(_unknown_message(unknown))
    return text


class TemplateIn(BaseModel):
    subject: Annotated[str, Field(max_length=200)] = ""
    body: Annotated[str, Field(max_length=5000)] = ""

    _check = field_validator("subject", "body")(_check_placeholders)


class CardIn(BaseModel):
    text_it: Annotated[str, Field(max_length=500)] = ""
    text_en: Annotated[str, Field(max_length=500)] = ""
    text_color: str = DEFAULT_CARD_COLOR
    text_position: Literal["top", "center", "bottom"] = "bottom"

    _check = field_validator("text_it", "text_en")(_check_placeholders)

    @field_validator("text_color")
    @classmethod
    def _color(cls, value: str) -> str:
        if not is_valid_color(value):
            raise ValueError(t("emailtpl.invalid_color"))
        return value


class SettingsTemplatesIn(BaseModel):
    templates: dict[Language, TemplateIn]


class SettingsIn(SettingsTemplatesIn):
    card: CardIn


def _require_edition(db: Session) -> Edition:
    edition = edition_service.get_active_edition(db)
    if edition is None:
        raise HTTPException(status_code=404, detail=t("edition.none"))
    return edition


@router.get("")
def get_settings(db: Session = Depends(get_db)) -> dict:
    return service.settings_view(db, _require_edition(db))


@router.put("")
def put_settings(
    body: SettingsIn, admin: Participant = Depends(require_admin), db: Session = Depends(get_db)
) -> dict:
    edition = _require_edition(db)
    service.save_settings(
        db,
        edition,
        admin,
        {locale: template.model_dump() for locale, template in body.templates.items()},
        body.card.model_dump(),
    )
    return service.settings_view(db, edition)


@router.put("/image")
def upload_image(file: Annotated[UploadFile, File()], db: Session = Depends(get_db)) -> dict:
    edition = _require_edition(db)
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    try:
        png = normalize_image(data)
    except InvalidImage as exc:
        status = 413 if exc.reason == "too_big" else 422
        raise HTTPException(status_code=status, detail=t(f"emailtpl.image_{exc.reason}")) from exc
    service.set_image(db, edition, png)
    return service.settings_view(db, edition)


@router.delete("/image")
def delete_image(db: Session = Depends(get_db)) -> dict:
    edition = _require_edition(db)
    service.set_image(db, edition, None)
    return service.settings_view(db, edition)


def _sample(edition: Edition, first_name: str, last_name: str, locale: str) -> Participant:
    return Participant(
        first_name=first_name,
        last_name=last_name,
        email="",
        personal_code="CSC-TEST",
        locale=locale,
    )


@router.get("/preview.png")
def preview(
    locale: Language = "it",
    text: str | None = Query(default=None, max_length=500),
    color: str | None = None,
    position: str | None = None,
    db: Session = Depends(get_db),
) -> Response:
    """The picture as a person called Ada Lovelace would get it. The optional parameters let the
    page show what is typed before it is saved."""
    edition = _require_edition(db)
    card = service.get_card(db, edition.id)
    sentence = text if text is not None else service.card_text_for(card, locale)
    unknown = unknown_placeholders(sentence)
    if unknown:
        raise HTTPException(status_code=422, detail=_unknown_message(unknown))
    chosen_color = color if color and is_valid_color(color) else (card.text_color if card else None)
    chosen_position = position if position in CARD_POSITIONS else None
    values = service.placeholder_values(
        _sample(edition, "Ada", "Lovelace", locale), edition, locale
    )
    png = render_card(
        card.image if card else None,
        render(sentence, values),
        chosen_color or DEFAULT_CARD_COLOR,
        chosen_position or (card.text_position if card else DEFAULT_CARD_POSITION),
    )
    return Response(content=png, media_type="image/png", headers={"Cache-Control": "no-store"})


@router.post("/test")
def send_test(
    locale: Language = "it",
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
    now: datetime = Depends(get_now),
    settings: Settings = Depends(get_settings_dep),
) -> dict:
    """Sends the registration email, as it is now, to the admin who asks."""
    edition = _require_edition(db)
    loc = normalize_locale(locale)
    person = _sample(edition, admin.first_name, admin.last_name, loc)
    person.email = admin.email
    slots = sorted(edition.slots, key=slot_sort_key)[:2]
    booking = SimpleNamespace(
        slots=slots,
        amount_due_cents=edition.base_fee_cents + edition.per_day_fee_cents,
        hold_expires_at=now + timedelta(days=edition.hold_days),
    )
    extras = service.registration_extras(db, edition, person)
    message = registration_email(
        person,
        booking,  # type: ignore[arg-type]
        enabled_channels(db, edition),
        auth_service.magic_link_url(settings, "EXAMPLE"),
        None,
        extras,
    )
    sender.send(message)
    return {"message": t("emailtpl.test_sent", email=admin.email)}


class FormIntroIn(BaseModel):
    it: Annotated[str, Field(max_length=FORM_INTRO_MAX)] = ""
    en: Annotated[str, Field(max_length=FORM_INTRO_MAX)] = ""


@texts_router.get("/texts")
def get_texts(db: Session = Depends(get_db)) -> dict:
    return service.emails_view(db, _require_edition(db))


@texts_router.put("/texts/{kind}")
def put_email_text(
    kind: str,
    body: SettingsTemplatesIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    if kind not in OTHER_EMAIL_KINDS:
        raise HTTPException(status_code=404, detail=t("emailtpl.unknown_email"))
    edition = _require_edition(db)
    templates = {locale: template.model_dump() for locale, template in body.templates.items()}
    # Two first saves of the same email (a double click, two admins) can both try to insert the
    # rows: the loser hits the unique constraint, so it retries and updates the winner's rows.
    for attempt in (1, 2):
        try:
            service.save_email(db, edition, admin, kind, templates)
            break
        except IntegrityError:
            db.rollback()
            if attempt == 2:
                raise
    return service.emails_view(db, edition)


@texts_router.put("/form-intro")
def put_form_intro(body: FormIntroIn, db: Session = Depends(get_db)) -> dict:
    edition = _require_edition(db)
    service.save_form_intro(db, edition, body.it, body.en)
    return service.emails_view(db, edition)
