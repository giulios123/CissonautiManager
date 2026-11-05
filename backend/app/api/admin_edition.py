from datetime import date, datetime, time
from typing import Literal, Self

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import get_db
from app.deps import get_email_sender, get_now, get_settings_dep, require_admin
from app.email import EmailSender
from app.i18n import t
from app.models import DOC_HEALTH, Edition, LegalDocument, PaymentChannel, slot_sort_key
from app.services import edition as edition_service
from app.services import waitlist as waitlist_service

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


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
    model_config = ConfigDict(from_attributes=True)
    kind: str
    version: int
    body: str


class EditionOut(EditionIn):
    id: int
    slots: list[SlotOut]
    payment_channels: list[ChannelOut]
    privacy: LegalOut | None
    disclaimer: LegalOut | None
    # Specific consent for health data (allergies); optional, it does not close registrations.
    health: LegalOut | None = None


class ChannelIn(BaseModel):
    code: Literal["revolut", "satispay", "paypal", "iban"]
    instructions: str = Field(default="", max_length=2000)
    enabled: bool = False


class LegalIn(BaseModel):
    kind: Literal["privacy", "disclaimer", "health"]
    body: str = Field(min_length=1, max_length=50000)


def _edition_out(db: Session, edition: Edition) -> EditionOut:
    slots = sorted(edition.slots, key=slot_sort_key)
    privacy = edition_service.latest_legal_document(db, edition, "privacy")
    disclaimer = edition_service.latest_legal_document(db, edition, "disclaimer")
    health = edition_service.latest_legal_document(db, edition, DOC_HEALTH)
    base = EditionIn.model_validate(edition, from_attributes=True)
    return EditionOut(
        **base.model_dump(),
        id=edition.id,
        slots=[SlotOut.model_validate(s) for s in slots],
        payment_channels=[
            ChannelOut.model_validate(c) for c in edition_service.list_channels(db, edition)
        ],
        privacy=LegalOut.model_validate(privacy) if privacy else None,
        disclaimer=LegalOut.model_validate(disclaimer) if disclaimer else None,
        health=LegalOut.model_validate(health) if health else None,
    )


def _require_edition(db: Session) -> Edition:
    edition = edition_service.get_active_edition(db)
    if edition is None:
        raise HTTPException(status_code=404, detail=t("edition.none"))
    return edition


@router.get("/edition")
def get_edition(db: Session = Depends(get_db)) -> EditionOut:
    return _edition_out(db, _require_edition(db))


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
        db, edition, body.kind, body.body
    )
    return LegalOut.model_validate(document)
