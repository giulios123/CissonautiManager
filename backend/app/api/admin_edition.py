import logging
from datetime import date, datetime, time
from typing import Annotated, Literal, Self

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import get_db
from app.deps import get_email_sender, get_now, get_settings_dep, require_admin
from app.email import EmailSender
from app.email.card import MAX_UPLOAD_BYTES, InvalidImage, normalize_image
from app.i18n import t
from app.models import (
    DOC_ATTENDANCE,
    DOC_HEALTH,
    DOC_MEDIA,
    Edition,
    LegalDocument,
    Participant,
    PaymentChannel,
    slot_sort_key,
)
from app.services import confirmation_policy as confirmation_policy_service
from app.services import edition as edition_service
from app.services import payments as payment_service
from app.services import waitlist as waitlist_service
from app.services.edition_logo import logo_url

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])
logger = logging.getLogger("app.api.admin_edition")


MIDNIGHT = time(0, 0)


def _valid_range(start: time, end: time) -> bool:
    """End must come after start. An end of 00:00 means midnight, the end of the day."""
    if end == MIDNIGHT:
        return start != MIDNIGHT
    return start < end


class EditionIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    start_date: date | None = None
    end_date: date | None = None
    morning_start: time = time(9, 0)
    morning_end: time = time(13, 0)
    afternoon_start: time = time(14, 0)
    afternoon_end: time = time(18, 0)
    evening_start: time = time(19, 0)
    evening_end: time = time(0, 0)
    # Seats per morning and afternoon slot. The evening has no limit.
    default_capacity: int = Field(default=25, ge=1, le=10000)
    hold_days: int = Field(default=3, ge=1, le=60)
    # Waitlist length of a full slot, as a percentage of its capacity (rounded down).
    waitlist_percent: int = Field(default=20, ge=0, le=100)
    base_fee_cents: int = Field(default=1000, ge=0)
    per_day_fee_cents: int = Field(default=100, ge=0)
    lunch_price_cents: int = Field(default=800, ge=0, le=100_000)
    dinner_price_cents: int = Field(default=1200, ge=0, le=100_000)

    @model_validator(mode="after")
    def check_consistency(self) -> Self:
        if (self.start_date is None) != (self.end_date is None):
            raise ValueError(t("edition.both_dates"))
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError(t("edition.end_before_start"))
        if self.start_date and self.end_date and (self.end_date - self.start_date).days > 60:
            raise ValueError(t("edition.too_long"))
        ranges = [
            (self.morning_start, self.morning_end),
            (self.afternoon_start, self.afternoon_end),
            (self.evening_start, self.evening_end),
        ]
        if not all(_valid_range(start, end) for start, end in ranges):
            raise ValueError(t("edition.time_order"))
        return self


class SlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date: date
    period: str
    start_time: time
    end_time: time
    capacity: int | None


class ChannelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: str
    label: str
    instructions: str
    enabled: bool


class LegalOut(BaseModel):
    id: int
    kind: str
    version: int
    body: str
    body_it: str | None
    body_en: str | None
    is_legacy: bool


class EditionOut(EditionIn):
    id: int
    slots: list[SlotOut]
    payment_channels: list[ChannelOut]
    privacy: LegalOut | None
    disclaimer: LegalOut | None
    # Specific consent for health data (allergies); optional, it does not close registrations.
    health: LegalOut | None = None
    attendance: LegalOut | None = None
    media: LegalOut | None = None
    logo_url: str | None = None


class ChannelIn(BaseModel):
    code: Literal["revolut", "satispay", "paypal", "iban"]
    instructions: str = Field(default="", max_length=2000)
    enabled: bool = False


class LegalIn(BaseModel):
    kind: Literal["privacy", "disclaimer", "health", "attendance", "media"]
    body_it: str = Field(min_length=1, max_length=50000)
    body_en: str = Field(min_length=1, max_length=50000)

    @field_validator("body_it", "body_en")
    @classmethod
    def require_nonblank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(t("legal.bilingual_required"))
        return value


class ConfirmationPolicyRow(BaseModel):
    booking_id: int
    name: str
    email: str
    status_before: str
    status_after: str
    registration_fee_cents: int
    amount_due_cents: int
    paid_cents: int
    balance_before_cents: int
    balance_after_cents: int
    confirmation_balance_after_cents: int
    sends_confirmation: bool


class ConfirmationPolicyBlocker(BaseModel):
    booking_id: int
    name: str
    reason: str


class ConfirmationPolicyPreviewOut(BaseModel):
    current_policy: str
    proposed_policy: str
    ready: bool
    already_active: bool
    preview_token: str | None
    eligible_count: int
    excluded_expired_count: int
    excluded_closed_count: int
    waitlist_only_count: int
    new_confirmation_count: int
    blockers: list[ConfirmationPolicyBlocker]
    rows: list[ConfirmationPolicyRow]


class ConfirmationPolicyActivateIn(BaseModel):
    preview_token: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


class ConfirmationPolicyActivateOut(BaseModel):
    already_applied: bool
    activated_at: datetime
    updated_bookings: int
    new_confirmations: int
    transferred_notices: int


def _legal_out(document: LegalDocument | None) -> LegalOut | None:
    if document is None:
        return None
    return LegalOut(
        id=document.id,
        kind=document.kind,
        version=document.version,
        body=document.body,
        body_it=document.body_it,
        body_en=document.body_en,
        is_legacy=document.body_it is None or document.body_en is None,
    )


def _edition_out(db: Session, edition: Edition) -> EditionOut:
    slots = sorted(edition.slots, key=slot_sort_key)
    privacy = edition_service.latest_legal_document(db, edition, "privacy")
    disclaimer = edition_service.latest_legal_document(db, edition, "disclaimer")
    health = edition_service.latest_legal_document(db, edition, DOC_HEALTH)
    attendance = edition_service.latest_legal_document(db, edition, DOC_ATTENDANCE)
    media = edition_service.latest_legal_document(db, edition, DOC_MEDIA)
    base = EditionIn.model_validate(edition, from_attributes=True)
    return EditionOut(
        **base.model_dump(),
        id=edition.id,
        logo_url=logo_url(edition),
        slots=[SlotOut.model_validate(s) for s in slots],
        payment_channels=[
            ChannelOut.model_validate(c) for c in edition_service.list_channels(db, edition)
        ],
        privacy=_legal_out(privacy),
        disclaimer=_legal_out(disclaimer),
        health=_legal_out(health),
        attendance=_legal_out(attendance),
        media=_legal_out(media),
    )


def _require_edition(db: Session) -> Edition:
    edition = edition_service.get_active_edition(db)
    if edition is None:
        raise HTTPException(status_code=404, detail=t("edition.none"))
    return edition


@router.get("/edition")
def get_edition(db: Session = Depends(get_db)) -> EditionOut:
    return _edition_out(db, _require_edition(db))


@router.get("/edition/confirmation-policy/preview")
def preview_confirmation_policy(
    response: Response,
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> ConfirmationPolicyPreviewOut:
    response.headers["Cache-Control"] = "no-store"
    edition = _require_edition(db)
    result = confirmation_policy_service.preview(db, edition, now)
    result.pop("_rows", None)
    return ConfirmationPolicyPreviewOut(**result)


@router.post("/edition/confirmation-policy/activate")
def activate_confirmation_policy(
    body: ConfirmationPolicyActivateIn,
    response: Response,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
    settings: Settings = Depends(get_settings_dep),
    now: datetime = Depends(get_now),
) -> ConfirmationPolicyActivateOut:
    response.headers["Cache-Control"] = "no-store"
    edition = _require_edition(db)
    try:
        result = confirmation_policy_service.activate(db, edition, admin, now, body.preview_token)
    except confirmation_policy_service.PreviewOutOfDate as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail=t("confirmation_policy.preview_changed")
        ) from exc
    except confirmation_policy_service.PreviewNotReady as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail=t("confirmation_policy.preview_blocked")
        ) from exc
    except confirmation_policy_service.PolicyAlreadyActive as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail=t("confirmation_policy.already_active")
        ) from exc
    if not result["already_applied"]:
        try:
            payment_service.send_due_confirmations(db, sender, now, settings)
        except Exception:
            logger.exception("Confirmation-policy emails failed")
    return ConfirmationPolicyActivateOut(**result)


@router.put("/edition")
def put_edition(
    body: EditionIn,
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
    settings: Settings = Depends(get_settings_dep),
    now: datetime = Depends(get_now),
) -> EditionOut:
    try:
        edition = edition_service.save_edition(db, body.model_dump())
    except edition_service.SlotsInUseError as exc:
        days = ", ".join(d.strftime("%d/%m/%Y") for d in exc.days)
        raise HTTPException(
            status_code=409,
            detail=t("edition.days_in_use", days=days),
        ) from exc
    # A larger capacity (or a higher waitlist share) can free seats for people waiting.
    waitlist_service.promote_freed(
        db, sender, settings, waitlist_service.slots_with_waiting_people(db, edition), now
    )
    db.refresh(edition)
    return _edition_out(db, edition)


@router.put("/edition/logo")
def upload_edition_logo(
    file: Annotated[UploadFile, File()], db: Session = Depends(get_db)
) -> EditionOut:
    edition = _require_edition(db)
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    try:
        edition.logo_image = normalize_image(data, preserve_alpha=True)
    except InvalidImage as exc:
        status = 413 if exc.reason == "too_big" else 422
        raise HTTPException(status_code=status, detail=t(f"emailtpl.image_{exc.reason}")) from exc
    db.commit()
    db.refresh(edition)
    return _edition_out(db, edition)


@router.delete("/edition/logo")
def delete_edition_logo(db: Session = Depends(get_db)) -> EditionOut:
    edition = _require_edition(db)
    edition.logo_image = None
    db.commit()
    db.refresh(edition)
    return _edition_out(db, edition)


@router.put("/payment-channels")
def put_payment_channels(body: list[ChannelIn], db: Session = Depends(get_db)) -> list[ChannelOut]:
    edition = _require_edition(db)
    by_code = {c.code: c for c in edition_service.list_channels(db, edition)}
    for item in body:
        channel: PaymentChannel = by_code[item.code]
        channel.instructions = item.instructions
        channel.enabled = item.enabled
    db.commit()
    return [ChannelOut.model_validate(c) for c in edition_service.list_channels(db, edition)]


@router.post("/legal-documents", status_code=201)
def post_legal_document(body: LegalIn, db: Session = Depends(get_db)) -> LegalOut:
    edition = _require_edition(db)
    document: LegalDocument = edition_service.publish_legal_document(
        db, edition, body.kind, body.body_it, body.body_en
    )
    result = _legal_out(document)
    assert result is not None
    return result
