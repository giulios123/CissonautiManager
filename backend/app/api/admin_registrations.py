from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.schemas import BookingView, booking_view
from app.db import get_db
from app.deps import get_email_sender, get_now, require_admin
from app.email import EmailSender
from app.models import STATUS_EXPIRED, Booking, LegalDocument, Participant
from app.services import edition as edition_service
from app.services import payments as payment_service
from app.services.seats import expire_overdue
from app.timefmt import to_rome

router = APIRouter(
    prefix="/api/admin/registrations", tags=["admin"], dependencies=[Depends(require_admin)]
)

Status = Literal["in_attesa_pagamento", "confermata", "scaduta", "disdetta_richiesta", "rimborsata"]


class RegistrationRow(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    personal_code: str
    days: int
    status: str
    amount_due_cents: int
    paid_cents: int
    balance_cents: int
    hold_expires_at: datetime
    created_at: datetime


class ParticipantView(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone: str | None
    invited_by: str | None
    can_bring: str | None
    personal_code: str


class LegalAcceptance(BaseModel):
    version: int
    accepted_at: datetime


class RegistrationDetail(BaseModel):
    participant: ParticipantView
    booking: BookingView
    privacy: LegalAcceptance
    disclaimer: LegalAcceptance
    warning: str | None = None


class PaymentIn(BaseModel):
    amount_cents: int = Field(gt=0, le=1_000_000)
    channel: Literal["revolut", "satispay", "paypal", "iban"]
    paid_on: date | None = None
    note: str | None = Field(default=None, max_length=1000)


def _row(booking: Booking, now: datetime) -> RegistrationRow:
    view = booking_view(booking, now)
    participant = booking.participant
    return RegistrationRow(
        id=booking.id,
        first_name=participant.first_name,
        last_name=participant.last_name,
        email=participant.email,
        personal_code=participant.personal_code,
        days=len({s.date for s in booking.slots}),
        status=view.status,
        amount_due_cents=view.amount_due_cents,
        paid_cents=view.paid_cents,
        balance_cents=view.balance_cents,
        hold_expires_at=booking.hold_expires_at,
        created_at=booking.created_at,
    )


def _detail(db: Session, booking: Booking, now: datetime, warning: str | None = None):
    view = booking_view(booking, now, include_notes=True)
    participant = booking.participant
    privacy = db.get(LegalDocument, booking.privacy_document_id)
    disclaimer = db.get(LegalDocument, booking.disclaimer_document_id)
    assert privacy is not None and disclaimer is not None
    if warning is None and view.status == STATUS_EXPIRED and view.paid_cents > 0:
        warning = "Ci sono pagamenti registrati su una prenotazione scaduta."
    return RegistrationDetail(
        participant=ParticipantView(
            id=participant.id,
            first_name=participant.first_name,
            last_name=participant.last_name,
            email=participant.email,
            phone=participant.phone,
            invited_by=participant.invited_by,
            can_bring=participant.can_bring,
            personal_code=participant.personal_code,
        ),
        booking=view,
        privacy=LegalAcceptance(version=privacy.version, accepted_at=booking.privacy_accepted_at),
        disclaimer=LegalAcceptance(
            version=disclaimer.version, accepted_at=booking.disclaimer_accepted_at
        ),
        warning=warning,
    )


def _get_booking(db: Session, booking_id: int) -> Booking:
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Iscrizione non trovata")
    return booking


@router.get("")
def list_registrations(
    status: Status | None = None,
    q: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> list[RegistrationRow]:
    expire_overdue(db, now)
    db.commit()
    edition = edition_service.get_active_edition(db)
    if edition is None:
        return []
    query = (
        select(Booking)
        .join(Participant, Participant.id == Booking.participant_id)
        .where(Booking.edition_id == edition.id)
        .order_by(Booking.created_at.desc(), Booking.id.desc())
    )
    if status:
        query = query.where(Booking.status == status)
    if q and q.strip():
        needle = q.strip().lower()
        query = query.where(
            or_(
                *[
                    func.lower(column).contains(needle, autoescape=True)
                    for column in (
                        Participant.first_name,
                        Participant.last_name,
                        Participant.email,
                        Participant.personal_code,
                    )
                ]
            )
        )
    return [_row(b, now) for b in db.scalars(query)]


@router.get("/{booking_id}")
def get_registration(
    booking_id: int, db: Session = Depends(get_db), now: datetime = Depends(get_now)
) -> RegistrationDetail:
    expire_overdue(db, now)
    db.commit()
    return _detail(db, _get_booking(db, booking_id), now)


@router.post("/{booking_id}/payments", status_code=201)
def add_payment(
    booking_id: int,
    body: PaymentIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
    now: datetime = Depends(get_now),
) -> RegistrationDetail:
    booking = _get_booking(db, booking_id)
    result = payment_service.record_payment(
        db,
        sender,
        booking,
        admin,
        amount_cents=body.amount_cents,
        channel=body.channel,
        paid_on=body.paid_on or to_rome(now).date(),
        note=body.note,
        now=now,
    )
    db.refresh(booking)
    return _detail(db, booking, now, warning=result.warning)
