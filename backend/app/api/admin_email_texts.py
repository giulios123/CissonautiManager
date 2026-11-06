"""Texts the admin can edit: the emails and the paragraph above the sign-up form."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_admin
from app.domain import email_texts as domain
from app.models import Edition, Participant
from app.services import audit
from app.services import edition as edition_service
from app.services import email_texts as service

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


class PartsOut(BaseModel):
    subject: str
    intro: str
    closing: str


class StoredOut(BaseModel):
    subject: str | None
    intro: str | None
    closing: str | None


class EmailTextOut(BaseModel):
    kind: str
    label: str
    # What the automatic block of this email contains (not editable).
    automatic: str
    defaults: PartsOut
    stored: StoredOut


class StoredIntro(BaseModel):
    stored: str | None
    default: str


class EmailTextsOut(BaseModel):
    placeholders: list[str]
    emails: list[EmailTextOut]
    registration_intro: StoredIntro


class EmailTextIn(BaseModel):
    subject: str | None = Field(default=None, max_length=1000)
    intro: str | None = Field(default=None, max_length=20000)
    closing: str | None = Field(default=None, max_length=20000)


class IntroIn(BaseModel):
    text: str | None = Field(default=None, max_length=20000)


def _require_edition(db: Session) -> Edition:
    edition = edition_service.get_active_edition(db)
    if edition is None:
        raise HTTPException(status_code=404, detail="Nessuna edizione configurata")
    return edition


def _email_out(kind: str, row) -> EmailTextOut:
    info = domain.KINDS[kind]
    defaults = info.defaults
    return EmailTextOut(
        kind=kind,
        label=info.label,
        automatic=info.automatic,
        defaults=PartsOut(subject=defaults.subject, intro=defaults.intro, closing=defaults.closing),
        stored=StoredOut(
            subject=row.subject if row else None,
            intro=row.intro if row else None,
            closing=row.closing if row else None,
        ),
    )


@router.get("/email-texts")
def get_email_texts(db: Session = Depends(get_db)) -> EmailTextsOut:
    edition = _require_edition(db)
    rows = service.stored_texts(db, edition)
    return EmailTextsOut(
        placeholders=list(domain.PLACEHOLDERS),
        emails=[_email_out(kind, rows.get(kind)) for kind in domain.KINDS],
        registration_intro=StoredIntro(
            stored=edition.registration_intro, default=domain.DEFAULT_REGISTRATION_INTRO
        ),
    )


@router.put("/email-texts/{kind}")
def put_email_text(
    kind: str,
    body: EmailTextIn,
    db: Session = Depends(get_db),
    admin: Participant = Depends(require_admin),
) -> EmailTextOut:
    if kind not in domain.KINDS:
        raise HTTPException(status_code=404, detail="Email sconosciuta")
    error = domain.validate(body.subject, body.intro, body.closing)
    if error:
        raise HTTPException(status_code=422, detail=error)
    edition = _require_edition(db)
    row = service.save_texts(db, edition, kind, body.subject, body.intro, body.closing, admin)
    audit.log(db, admin, "email_text_changed", f"Testo dell'email «{domain.KINDS[kind].label}»")
    db.commit()
    return _email_out(kind, row)


@router.put("/registration-intro")
def put_registration_intro(
    body: IntroIn,
    db: Session = Depends(get_db),
    admin: Participant = Depends(require_admin),
) -> StoredIntro:
    if body.text is not None and len(body.text) > domain.TEXT_MAX:
        raise HTTPException(
            status_code=422, detail=f"Il testo può avere al massimo {domain.TEXT_MAX} caratteri"
        )
    edition = _require_edition(db)
    edition.registration_intro = (body.text or "").strip() or None
    audit.log(db, admin, "registration_intro_changed", "Testo sopra il modulo di iscrizione")
    db.commit()
    return StoredIntro(stored=edition.registration_intro, default=domain.DEFAULT_REGISTRATION_INTRO)
