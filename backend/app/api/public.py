from datetime import date, datetime, time
from hashlib import sha256
from itertools import groupby
from typing import Annotated, Literal, Self

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, EmailStr, Field, StringConstraints, model_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas import ScheduleSlotView
from app.config import Settings
from app.db import get_db
from app.deps import get_email_sender, get_now, get_settings_dep
from app.domain.booking import is_past_day
from app.email import EmailSender
from app.i18n import LOCALES, channel_label, current_locale, t
from app.models import (
    DOC_ATTENDANCE,
    DOC_DISCLAIMER,
    DOC_MEDIA,
    DOC_PRIVACY,
    OPTIONAL_CONSENT_KINDS,
    LegalDocument,
    slot_sort_key,
)
from app.services import edition as edition_service
from app.services import email_templates as email_templates_service
from app.services import registration as registration_service
from app.services import waitlist as waitlist_service
from app.services.edition_logo import logo_url
from app.services.seats import expire_overdue, free_by_slot
from app.timefmt import format_slot

router = APIRouter(prefix="/api/public", tags=["public"])

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class SlotAvailability(BaseModel):
    id: int
    period: str
    start_time: time
    end_time: time
    capacity: int | None
    available: int | None
    # Places left on the waitlist of a full slot; None when the slot is not full or has no list.
    waitlist_free: int | None = None


class DayOut(BaseModel):
    date: date
    past: bool
    slots: list[SlotAvailability]


class LegalPublic(BaseModel):
    version: int
    body: str
    id: int | None = None
    body_it: str | None = None
    body_en: str | None = None
    is_legacy: bool = False


class OptionalConsentPublic(BaseModel):
    id: int
    version: int
    texts: dict[str, str]


class ChannelPublic(BaseModel):
    code: str
    label: str
    instructions: str


class PublicEditionOut(BaseModel):
    registration_open: bool
    name: str | None = None
    # The paragraph above the form in each language (the page can switch language by itself).
    registration_intro: dict[str, str] | None = None
    logo_url: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    base_fee_cents: int | None = None
    per_day_fee_cents: int | None = None
    hold_days: int | None = None
    days: list[DayOut] = []
    payment_channels: list[ChannelPublic] = []
    privacy: LegalPublic | None = None
    disclaimer: LegalPublic | None = None
    attendance_consent: OptionalConsentPublic | None = None
    media_consent: OptionalConsentPublic | None = None


class RegistrationIn(BaseModel):
    first_name: Name
    last_name: Name
    email: EmailStr
    phone: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
    invited_by: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None = (
        None
    )
    can_bring: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
    ]
    slot_ids: list[int] = Field(default_factory=list, max_length=60)
    # Full slots to wait for: someone can register with these only.
    waitlist_slot_ids: list[int] = Field(default_factory=list, max_length=60)
    # Language of the form: the one of the later emails. Missing means the request language.
    locale: Literal["it", "en"] | None = None
    accept_privacy: bool
    accept_disclaimer: bool
    privacy_version: int
    disclaimer_version: int

    @model_validator(mode="after")
    def check_acceptances(self) -> Self:
        if not self.slot_ids and not self.waitlist_slot_ids:
            raise ValueError(t("register.slots_required"))
        if not self.accept_privacy:
            raise ValueError(t("register.privacy_required"))
        if not self.accept_disclaimer:
            raise ValueError(t("register.disclaimer_required"))
        return self


class BookedSlot(BaseModel):
    date: date
    period: str
    label: str


class WaitlistedSlot(BaseModel):
    date: date
    period: str
    label: str
    position: int


class BookingSummary(BaseModel):
    personal_code: str
    status: str
    amount_due_cents: int
    hold_expires_at: datetime
    slots: list[BookedSlot]
    schedule: list[ScheduleSlotView]
    payment_channels: list[ChannelPublic]


class RegistrationOut(BaseModel):
    result: str
    message: str | None = None
    booking: BookingSummary | None = None
    personal_code: str | None = None
    # Slots the person is waiting for, with their place on each list.
    waitlist: list[WaitlistedSlot] = []


def _channels(db: Session, edition) -> list[ChannelPublic]:
    return [
        ChannelPublic(
            code=c.code, label=channel_label(c.code, c.label), instructions=c.instructions
        )
        for c in registration_service.enabled_channels(db, edition)
    ]


def _legal_public(document: LegalDocument | None) -> LegalPublic | None:
    if document is None:
        return None
    return LegalPublic(
        id=document.id,
        version=document.version,
        body=document.body,
        body_it=document.body_it,
        body_en=document.body_en,
        is_legacy=document.body_it is None or document.body_en is None,
    )


def _optional_consent_public(db: Session, edition, kind: str) -> OptionalConsentPublic | None:
    document = edition_service.latest_legal_document(db, edition, kind)
    if (
        document is None
        or not document.body_it
        or not document.body_it.strip()
        or not document.body_en
        or not document.body_en.strip()
    ):
        return None
    return OptionalConsentPublic(
        id=document.id,
        version=document.version,
        texts={"it": document.body_it, "en": document.body_en},
    )


def _public_legal_fields(db: Session, edition) -> dict:
    privacy = edition_service.latest_legal_document(db, edition, DOC_PRIVACY)
    disclaimer = edition_service.latest_legal_document(db, edition, DOC_DISCLAIMER)
    optional = {
        kind: _optional_consent_public(db, edition, kind) for kind in OPTIONAL_CONSENT_KINDS
    }
    return {
        "privacy": _legal_public(privacy),
        "disclaimer": _legal_public(disclaimer),
        "attendance_consent": optional[DOC_ATTENDANCE],
        "media_consent": optional[DOC_MEDIA],
    }


@router.get("/edition/logo")
def get_edition_logo(
    version: Annotated[str | None, Query(alias="v", min_length=64, max_length=64)] = None,
    db: Session = Depends(get_db),
) -> Response:
    edition = edition_service.get_active_edition(db)
    if edition is None or edition.logo_image is None:
        raise HTTPException(status_code=404, detail=t("edition.logo_none"))
    etag = sha256(edition.logo_image).hexdigest()
    if version != etag:
        raise HTTPException(status_code=404, detail=t("edition.logo_none"))
    return Response(
        content=edition.logo_image,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=31536000, immutable", "ETag": f'"{etag}"'},
    )


@router.get("/edition")
def get_public_edition(
    db: Session = Depends(get_db), now: datetime = Depends(get_now)
) -> PublicEditionOut:
    edition = edition_service.get_active_edition(db)
    if not registration_service.is_registration_open(db, edition):
        legal_fields = _public_legal_fields(db, edition) if edition is not None else {}
        return PublicEditionOut(
            registration_open=False,
            name=edition.name if edition else None,
            logo_url=logo_url(edition),
            **legal_fields,
        )
    assert edition is not None
    expire_overdue(db, now)
    db.commit()
    slots = sorted(edition.slots, key=slot_sort_key)
    free = free_by_slot(db, slots, now)
    waitlist_free = waitlist_service.waitlist_availability(db, edition, slots, free, now)
    days = [
        DayOut(
            date=day,
            past=is_past_day(day, now),
            slots=[
                SlotAvailability(
                    id=s.id,
                    period=s.period,
                    start_time=s.start_time,
                    end_time=s.end_time,
                    capacity=s.capacity,
                    available=free[s.id],
                    waitlist_free=waitlist_free[s.id],
                )
                for s in group
            ],
        )
        for day, group in groupby(slots, key=lambda s: s.date)
    ]
    privacy = edition_service.latest_legal_document(db, edition, "privacy")
    disclaimer = edition_service.latest_legal_document(db, edition, "disclaimer")
    assert privacy is not None and disclaimer is not None
    return PublicEditionOut(
        registration_open=True,
        name=edition.name,
        logo_url=logo_url(edition),
        registration_intro={
            loc: email_templates_service.form_intro_for(edition, loc) for loc in LOCALES
        },
        start_date=edition.start_date,
        end_date=edition.end_date,
        base_fee_cents=edition.base_fee_cents,
        per_day_fee_cents=edition.per_day_fee_cents,
        hold_days=edition.hold_days,
        days=days,
        payment_channels=_channels(db, edition),
        **_public_legal_fields(db, edition),
    )


@router.post("/registrations", status_code=201, response_model=None)
def create_registration(
    body: RegistrationIn,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    sender: EmailSender = Depends(get_email_sender),
    now: datetime = Depends(get_now),
) -> RegistrationOut | JSONResponse:
    fields = body.model_dump(exclude={"accept_privacy", "accept_disclaimer", "locale"})
    data = registration_service.RegistrationData(**fields, locale=body.locale or current_locale())
    try:
        result = registration_service.register(db, sender, settings, data, now)
    except registration_service.RegistrationClosed as exc:
        raise HTTPException(status_code=409, detail=t("register.closed")) from exc
    except registration_service.LegalTextsChanged as exc:
        raise HTTPException(
            status_code=409,
            detail=t("register.legal_outdated"),
        ) from exc
    except registration_service.InvalidSlots as exc:
        raise HTTPException(status_code=422, detail=t("slots.invalid")) from exc
    except registration_service.SlotsFull as exc:
        db.rollback()
        labels = ", ".join(
            format_slot(s.date, s.period, s.start_time, s.end_time) for s in exc.slots
        )
        return JSONResponse(
            status_code=409,
            content={
                "detail": t("slots.full_choose_others", labels=labels),
                "full_slot_ids": [s.id for s in exc.slots],
            },
        )
    except waitlist_service.WaitlistRefused as exc:
        db.rollback()
        detail = t("register.slot_freed") if exc.reason == "not_full" else t("register.list_filled")
        raise HTTPException(status_code=409, detail=detail) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=t("register.in_progress")) from exc

    if not result.created:
        return RegistrationOut(
            result="already_registered",
            message=t("register.already"),
        )
    waitlist = [
        WaitlistedSlot(
            date=e.slot.date,
            period=e.slot.period,
            label=format_slot(e.slot.date, e.slot.period, e.slot.start_time, e.slot.end_time),
            position=waitlist_service.position_of(db, e),
        )
        for e in result.waitlist
    ]
    if result.booking is None:
        return RegistrationOut(
            result="waitlisted",
            message=t("register.waitlisted"),
            personal_code=result.participant.personal_code,
            waitlist=waitlist,
        )
    booking = result.booking
    edition = edition_service.get_active_edition(db)
    assert edition is not None
    return RegistrationOut(
        result="created",
        booking=BookingSummary(
            personal_code=result.participant.personal_code,
            status=booking.status,
            amount_due_cents=booking.amount_due_cents,
            hold_expires_at=booking.hold_expires_at,
            slots=[
                BookedSlot(
                    date=s.date,
                    period=s.period,
                    label=format_slot(s.date, s.period, s.start_time, s.end_time),
                )
                for s in sorted(booking.slots, key=slot_sort_key)
            ],
            schedule=[
                ScheduleSlotView(
                    date=s.date,
                    period=s.period,
                    start_time=s.start_time,
                    end_time=s.end_time,
                )
                for s in sorted(edition.slots, key=slot_sort_key)
                if s.date in {booked.date for booked in booking.slots}
            ],
            payment_channels=_channels(db, edition),
        ),
        personal_code=result.participant.personal_code,
        waitlist=waitlist,
    )
