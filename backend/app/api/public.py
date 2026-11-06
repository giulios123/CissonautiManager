from datetime import date, datetime, time
from itertools import groupby
from typing import Annotated, Self

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, StringConstraints, model_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import get_db
from app.deps import get_email_sender, get_now, get_settings_dep
from app.domain.booking import is_past_day
from app.domain.email_texts import registration_intro
from app.email import EmailSender
from app.models import slot_sort_key
from app.services import edition as edition_service
from app.services import registration as registration_service
from app.services import waitlist as waitlist_service
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


class ChannelPublic(BaseModel):
    code: str
    label: str
    instructions: str


class PublicEditionOut(BaseModel):
    registration_open: bool
    name: str | None = None
    registration_intro: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    base_fee_cents: int | None = None
    per_day_fee_cents: int | None = None
    hold_days: int | None = None
    days: list[DayOut] = []
    payment_channels: list[ChannelPublic] = []
    privacy: LegalPublic | None = None
    disclaimer: LegalPublic | None = None


class RegistrationIn(BaseModel):
    first_name: Name
    last_name: Name
    email: EmailStr
    phone: Annotated[str, StringConstraints(strip_whitespace=True, max_length=50)] | None = None
    invited_by: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None = (
        None
    )
    can_bring: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
    ]
    slot_ids: list[int] = Field(default_factory=list, max_length=60)
    # Full slots to wait for: someone can register with these only.
    waitlist_slot_ids: list[int] = Field(default_factory=list, max_length=60)
    accept_privacy: bool
    accept_disclaimer: bool
    privacy_version: int
    disclaimer_version: int

    @model_validator(mode="after")
    def check_acceptances(self) -> Self:
        if not self.slot_ids and not self.waitlist_slot_ids:
            raise ValueError("Scegli almeno uno slot")
        if not self.accept_privacy:
            raise ValueError("Per iscriverti devi accettare l'informativa privacy")
        if not self.accept_disclaimer:
            raise ValueError("Per iscriverti devi accettare lo scarico di responsabilità")
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
        ChannelPublic(code=c.code, label=c.label, instructions=c.instructions)
        for c in registration_service.enabled_channels(db, edition)
    ]


@router.get("/edition")
def get_public_edition(
    db: Session = Depends(get_db), now: datetime = Depends(get_now)
) -> PublicEditionOut:
    edition = edition_service.get_active_edition(db)
    if not registration_service.is_registration_open(db, edition):
        return PublicEditionOut(registration_open=False, name=edition.name if edition else None)
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
        registration_intro=registration_intro(edition.registration_intro),
        start_date=edition.start_date,
        end_date=edition.end_date,
        base_fee_cents=edition.base_fee_cents,
        per_day_fee_cents=edition.per_day_fee_cents,
        hold_days=edition.hold_days,
        days=days,
        payment_channels=_channels(db, edition),
        privacy=LegalPublic(version=privacy.version, body=privacy.body),
        disclaimer=LegalPublic(version=disclaimer.version, body=disclaimer.body),
    )


@router.post("/registrations", status_code=201, response_model=None)
def create_registration(
    body: RegistrationIn,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    sender: EmailSender = Depends(get_email_sender),
    now: datetime = Depends(get_now),
) -> RegistrationOut | JSONResponse:
    data = registration_service.RegistrationData(
        **body.model_dump(exclude={"accept_privacy", "accept_disclaimer"})
    )
    try:
        result = registration_service.register(db, sender, settings, data, now)
    except registration_service.RegistrationClosed as exc:
        raise HTTPException(status_code=409, detail="Le iscrizioni non sono aperte") from exc
    except registration_service.LegalTextsChanged as exc:
        raise HTTPException(
            status_code=409,
            detail="I testi legali sono stati aggiornati: ricarica la pagina e rileggili",
        ) from exc
    except registration_service.InvalidSlots as exc:
        raise HTTPException(status_code=422, detail="Gli slot scelti non sono validi") from exc
    except registration_service.SlotsFull as exc:
        db.rollback()
        labels = ", ".join(
            format_slot(s.date, s.period, s.start_time, s.end_time) for s in exc.slots
        )
        return JSONResponse(
            status_code=409,
            content={
                "detail": f"Questi slot sono al completo: {labels}. Scegline altri.",
                "full_slot_ids": [s.id for s in exc.slots],
            },
        )
    except waitlist_service.WaitlistRefused as exc:
        db.rollback()
        detail = (
            "Nel frattempo si è liberato un posto in uno slot che avevi messo in lista: "
            "ricarica la pagina e prenotalo direttamente."
            if exc.reason == "not_full"
            else "Nel frattempo una lista d'attesa si è riempita: ricarica la pagina e riprova."
        )
        raise HTTPException(status_code=409, detail=detail) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Esiste già una richiesta in corso, riprova tra poco"
        ) from exc

    if not result.created:
        return RegistrationOut(
            result="already_registered",
            message="Risulti già iscritto. Ti abbiamo inviato un link per entrare.",
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
            message="Sei in lista d'attesa. Ti abbiamo inviato un link per entrare.",
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
            payment_channels=_channels(db, edition),
        ),
        personal_code=result.participant.personal_code,
        waitlist=waitlist,
    )
