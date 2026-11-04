from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.public import ChannelPublic
from app.api.schemas import BookingView, booking_view
from app.db import get_db
from app.deps import current_user, get_now
from app.models import Booking, Participant
from app.services import edition as edition_service
from app.services import registration as registration_service
from app.services.passwords import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH, hash_password

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
