from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.public import ChannelPublic
from app.api.schemas import BookingView, booking_view
from app.db import get_db
from app.deps import current_user, get_email_sender, get_now
from app.email import EmailSender
from app.models import Booking, Participant
from app.services import booking_changes
from app.services import edition as edition_service
from app.services import registration as registration_service
from app.services.passwords import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH, hash_password
from app.services.registration import InvalidSlots, SlotsFull
from app.timefmt import format_slot

router = APIRouter(prefix="/api", tags=["me"])


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
    if edition is not None:
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
    )


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
    return booking_view(result.booking, now)


class CancelOut(BaseModel):
    outcome: str


@router.post("/me/booking/cancel")
def cancel_my_booking(
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
    now: datetime = Depends(get_now),
) -> CancelOut:
    booking = booking_changes.get_current_booking(db, user)
    if booking is None:
        raise HTTPException(status_code=404, detail="Non hai ancora un'iscrizione")
    try:
        outcome = booking_changes.request_cancellation(db, sender, booking, now)
    except booking_changes.NotEditable as exc:
        raise HTTPException(
            status_code=409, detail="Questa iscrizione non si può più disdire"
        ) from exc
    return CancelOut(outcome=outcome)
