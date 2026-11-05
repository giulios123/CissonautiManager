from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.public import ChannelPublic, LegalPublic
from app.api.schemas import BookingView, booking_view
from app.config import Settings
from app.db import get_db
from app.deps import current_user, get_email_sender, get_now, get_settings_dep
from app.email import EmailSender
from app.models import DOC_HEALTH, Booking, Edition, Participant, WaitlistEntry
from app.services import booking_changes
from app.services import edition as edition_service
from app.services import health as health_service
from app.services import meals as meals_service
from app.services import registration as registration_service
from app.services import waitlist as waitlist_service
from app.services.passwords import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH, hash_password
from app.services.registration import InvalidSlots, SlotsFull
from app.timefmt import format_meal, format_slot

router = APIRouter(prefix="/api", tags=["me"])


class WaitlistView(BaseModel):
    id: int
    slot_id: int
    date: date
    period: str
    label: str
    position: int


class MeOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    role: str
    personal_code: str
    has_password: bool
    bookings: list[BookingView]
    payment_channels: list[ChannelPublic]
    waitlist: list[WaitlistView] = []
    lunch_price_cents: int | None = None
    dinner_price_cents: int | None = None
    # Text of the consent for allergies; None while the admins have not published it.
    health_consent: LegalPublic | None = None


class PasswordIn(BaseModel):
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)


@router.get("/me")
def get_me(
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> MeOut:
    edition = edition_service.get_active_edition(db)
    bookings: list[Booking] = []
    channels = []
    waitlist: list[WaitlistView] = []
    if edition is not None:
        waitlist = [
            _waitlist_view(db, entry) for entry in waitlist_service.entries_of(db, user, edition)
        ]
        bookings = list(
            db.scalars(
                select(Booking)
                .where(Booking.participant_id == user.id, Booking.edition_id == edition.id)
                .order_by(Booking.id.desc())
            )
        )
        channels = [
            ChannelPublic(code=c.code, label=c.label, instructions=c.instructions)
            for c in registration_service.enabled_channels(db, edition)
        ]
    return MeOut(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        role=user.role,
        personal_code=user.personal_code,
        has_password=user.password_hash is not None,
        bookings=[booking_view(b, now) for b in bookings],
        payment_channels=channels,
        waitlist=waitlist,
        health_consent=_health_consent(db, edition),
        lunch_price_cents=edition.lunch_price_cents if edition else None,
        dinner_price_cents=edition.dinner_price_cents if edition else None,
    )


def _health_consent(db: Session, edition: Edition | None) -> LegalPublic | None:
    if edition is None:
        return None
    document = edition_service.latest_legal_document(db, edition, DOC_HEALTH)
    return LegalPublic(version=document.version, body=document.body) if document else None


def _waitlist_view(db: Session, entry: WaitlistEntry) -> WaitlistView:
    slot = entry.slot
    return WaitlistView(
        id=entry.id,
        slot_id=slot.id,
        date=slot.date,
        period=slot.period,
        label=format_slot(slot.date, slot.period, slot.start_time, slot.end_time),
        position=waitlist_service.position_of(db, entry),
    )


class WaitlistIn(BaseModel):
    slot_id: int


@router.post("/me/waitlist", status_code=201)
def join_waitlist(
    body: WaitlistIn,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> WaitlistView:
    try:
        entry = waitlist_service.join(db, user, body.slot_id, now)
    except waitlist_service.EntryNotFound as exc:
        raise HTTPException(status_code=404, detail="Slot non trovato") from exc
    except waitlist_service.NoLegalAcceptance as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Prima iscriviti al camp dal modulo di iscrizione"
        ) from exc
    except waitlist_service.WaitlistRefused as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail=waitlist_service.REFUSAL_MESSAGES[exc.reason]
        ) from exc
    db.commit()
    return _waitlist_view(db, entry)


@router.delete("/me/waitlist/{entry_id}", status_code=204)
def leave_waitlist(
    entry_id: int,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> None:
    try:
        waitlist_service.leave(db, user, entry_id, now)
    except waitlist_service.EntryNotFound as exc:
        raise HTTPException(status_code=404, detail="Non risulti in questa lista") from exc


@router.put("/me/password", status_code=204)
def set_password(
    body: PasswordIn, user: Participant = Depends(current_user), db: Session = Depends(get_db)
) -> None:
    user = db.merge(user)
    user.password_hash = hash_password(body.password)
    db.commit()


class SlotsIn(BaseModel):
    slot_ids: list[int] = Field(max_length=60)


@router.put("/me/booking/slots", response_model=None)
def change_my_slots(
    body: SlotsIn,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
    settings: Settings = Depends(get_settings_dep),
    now: datetime = Depends(get_now),
) -> BookingView | JSONResponse:
    booking = booking_changes.get_current_booking(db, user)
    if booking is None:
        raise HTTPException(status_code=404, detail="Non hai ancora un'iscrizione")
    try:
        result = booking_changes.change_slots(db, sender, booking, body.slot_ids, now)
    except booking_changes.NotEditable as exc:
        raise HTTPException(
            status_code=409, detail="Questa iscrizione non si può più modificare"
        ) from exc
    except booking_changes.EmptySelection as exc:
        raise HTTPException(
            status_code=422, detail="Scegli almeno uno slot. Per rinunciare usa la disdetta"
        ) from exc
    except booking_changes.PastDay as exc:
        raise HTTPException(
            status_code=422,
            detail="Gli slot di giorni già passati non si possono cambiare: scrivi a chi organizza",
        ) from exc
    except InvalidSlots as exc:
        raise HTTPException(status_code=422, detail="Gli slot scelti non sono validi") from exc
    except SlotsFull as exc:
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
    waitlist_service.promote_freed(db, sender, settings, result.removed_slot_ids, now)
    db.refresh(result.booking)
    view = booking_view(result.booking, now)
    view.dropped_meals = [format_meal(day, kind) for day, kind in result.dropped_meals]
    return view


class MealIn(BaseModel):
    date: date
    kind: Literal["lunch", "dinner"]


class MealsIn(BaseModel):
    meals: list[MealIn] = Field(max_length=200)


MEAL_REFUSALS = {
    "not_allowed": "Puoi scegliere un pasto solo nei giorni e nelle fasce in cui sei presente",
    "past_day": "I pasti di giorni già passati non si possono cambiare: scrivi a chi organizza",
}


@router.put("/me/booking/meals")
def change_my_meals(
    body: MealsIn,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
    now: datetime = Depends(get_now),
) -> BookingView:
    booking = booking_changes.get_current_booking(db, user)
    if booking is None:
        raise HTTPException(status_code=404, detail="Non hai ancora un'iscrizione")
    try:
        result = meals_service.change_meals(
            db, sender, booking, [(m.date, m.kind) for m in body.meals], now
        )
    except booking_changes.NotEditable as exc:
        raise HTTPException(
            status_code=409, detail="Questa iscrizione non si può più modificare"
        ) from exc
    except meals_service.MealsRefused as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=MEAL_REFUSALS[exc.reason]) from exc
    return booking_view(result.booking, now)


class DietaryIn(BaseModel):
    diet: Literal["omnivore", "vegetarian", "vegan"] | None = None
    allergies: str | None = Field(default=None, max_length=2000)
    consent: bool = False


@router.put("/me/booking/dietary")
def save_my_dietary(
    body: DietaryIn,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> BookingView:
    booking = booking_changes.get_current_booking(db, user)
    if booking is None:
        raise HTTPException(status_code=404, detail="Non hai ancora un'iscrizione")
    try:
        health_service.save_dietary(db, booking, body.diet, body.allergies, body.consent, now)
    except booking_changes.NotEditable as exc:
        raise HTTPException(
            status_code=409, detail="Questa iscrizione non si può più modificare"
        ) from exc
    except health_service.ConsentRequired as exc:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail="Per salvare allergie e intolleranze serve il consenso al trattamento dei "
            "dati sanitari",
        ) from exc
    except health_service.NoConsentText as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Per ora non si possono indicare allergie: scrivi a chi organizza",
        ) from exc
    return booking_view(booking, now)


class CancelOut(BaseModel):
    outcome: str


@router.post("/me/booking/cancel")
def cancel_my_booking(
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
    settings: Settings = Depends(get_settings_dep),
    now: datetime = Depends(get_now),
) -> CancelOut:
    booking = booking_changes.get_current_booking(db, user)
    if booking is None:
        raise HTTPException(status_code=404, detail="Non hai ancora un'iscrizione")
    freed = [s.id for s in booking.slots]
    try:
        outcome = booking_changes.request_cancellation(db, sender, booking, now)
    except booking_changes.NotEditable as exc:
        raise HTTPException(
            status_code=409, detail="Questa iscrizione non si può più disdire"
        ) from exc
    waitlist_service.promote_freed(db, sender, settings, freed, now)
    return CancelOut(outcome=outcome)
