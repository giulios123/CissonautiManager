from collections import defaultdict
from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr, Field, StringConstraints
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas import BookingView, booking_view
from app.csv_export import Amount, csv_filename, csv_response
from app.db import get_db
from app.deps import get_email_sender, get_now, require_admin
from app.domain.booking import occupies_seats
from app.domain.presence import has_evening
from app.email import EmailSender
from app.models import STATUS_EXPIRED, Booking, LegalDocument, Participant
from app.services import audit as audit_service
from app.services import booking_admin as booking_admin_service
from app.services import edition as edition_service
from app.services import payments as payment_service
from app.services import refunds as refund_service
from app.services.registration import SlotsFull
from app.services.seats import expire_overdue
from app.timefmt import ROME, format_euro, format_slot, status_label, to_rome

router = APIRouter(
    prefix="/api/admin/registrations", tags=["admin"], dependencies=[Depends(require_admin)]
)

Status = Literal["in_attesa_pagamento", "confermata", "scaduta", "disdetta_richiesta", "rimborsata"]


class RegistrationRow(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone: str | None
    personal_code: str
    days: int
    evenings: int
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


class RefundOut(BaseModel):
    amount_cents: int
    refunded_on: date | None
    note: str | None


class HistoryEntry(BaseModel):
    at: datetime
    actor: str
    action: str
    detail: str


class RegistrationDetail(BaseModel):
    participant: ParticipantView
    booking: BookingView
    privacy: LegalAcceptance
    disclaimer: LegalAcceptance
    refund: RefundOut | None = None
    history: list[HistoryEntry] = []
    warning: str | None = None


class RefundIn(BaseModel):
    amount_cents: int = Field(ge=0, le=1_000_000)
    refunded_on: date | None = None
    note: str | None = Field(default=None, max_length=1000)


Text = Annotated[str, StringConstraints(strip_whitespace=True)]


class RegistrationPatch(BaseModel):
    """Fields left out stay as they are; phone and invited_by can be cleared with null or ''."""

    first_name: Annotated[Text, Field(min_length=1, max_length=100)] | None = None
    last_name: Annotated[Text, Field(min_length=1, max_length=100)] | None = None
    email: EmailStr | None = None
    phone: Annotated[Text, Field(max_length=50)] | None = None
    invited_by: Annotated[Text, Field(max_length=200)] | None = None
    can_bring: Annotated[Text, Field(min_length=1, max_length=2000)] | None = None
    # Without a time zone the value is read as Europe/Rome time.
    hold_expires_at: datetime | None = None


class PaymentIn(BaseModel):
    amount_cents: int = Field(gt=0, le=1_000_000)
    channel: Literal["revolut", "satispay", "paypal", "iban"]
    paid_on: date | None = None
    note: str | None = Field(default=None, max_length=1000)


def _evenings(booking: Booking, status: str) -> int:
    """Days on which the person is present in the evening, booked or derived (D-009)."""
    if not occupies_seats(status):
        return 0
    periods: dict[date, set[str]] = defaultdict(set)
    for slot in booking.slots:
        periods[slot.date].add(slot.period)
    return sum(1 for day_periods in periods.values() if has_evening(day_periods))


def _row(booking: Booking, now: datetime) -> RegistrationRow:
    view = booking_view(booking, now)
    participant = booking.participant
    return RegistrationRow(
        id=booking.id,
        first_name=participant.first_name,
        last_name=participant.last_name,
        email=participant.email,
        phone=participant.phone,
        personal_code=participant.personal_code,
        days=len({s.date for s in booking.slots}),
        evenings=_evenings(booking, view.status),
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
        refund=(
            RefundOut(
                amount_cents=booking.refund_cents,
                refunded_on=booking.refunded_on,
                note=booking.refund_note,
            )
            if booking.refund_cents is not None
            else None
        ),
        history=[
            HistoryEntry(
                at=entry.at,
                actor=f"{actor.first_name} {actor.last_name}".strip(),
                action=entry.action,
                detail=entry.detail,
            )
            for entry, actor in audit_service.history(db, booking.id)
        ],
        warning=warning,
    )


def _get_booking(db: Session, booking_id: int) -> Booking:
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Iscrizione non trovata")
    return booking


def _csv_rows(rows: list[RegistrationRow]):
    for row in rows:
        yield [
            row.first_name,
            row.last_name,
            row.email,
            row.phone,
            row.personal_code,
            row.days,
            row.evenings,
            status_label(row.status),
            Amount(row.amount_due_cents),
            Amount(row.paid_cents),
            Amount(row.balance_cents),
            row.hold_expires_at if row.status == "in_attesa_pagamento" else None,
            row.created_at,
        ]


CSV_HEADER = [
    "Nome",
    "Cognome",
    "Email",
    "Telefono",
    "Codice",
    "Giorni",
    "Sere",
    "Stato",
    "Dovuto",
    "Versato",
    "Saldo",
    "Scadenza blocco",
    "Iscritto il",
]


@router.get("", response_model=None)
def list_registrations(
    status: Status | None = None,
    q: str | None = Query(default=None, max_length=100),
    fmt: Literal["json", "csv"] = Query(default="json", alias="format"),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> list[RegistrationRow] | Response:
    expire_overdue(db, now)
    db.commit()
    edition = edition_service.get_active_edition(db)
    if edition is None:
        rows: list[RegistrationRow] = []
    else:
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
        rows = [_row(b, now) for b in db.scalars(query)]
    if fmt == "csv":
        return csv_response(csv_filename("persone", now), CSV_HEADER, _csv_rows(rows))
    return rows


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


@router.post("/{booking_id}/refund")
def add_refund(
    booking_id: int,
    body: RefundIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> RegistrationDetail:
    booking = _get_booking(db, booking_id)
    try:
        refund_service.record_refund(
            db,
            admin,
            booking,
            amount_cents=body.amount_cents,
            refunded_on=body.refunded_on or to_rome(now).date(),
            note=body.note,
        )
    except refund_service.NotRefundable as exc:
        raise HTTPException(
            status_code=409, detail="Si può registrare un rimborso solo su una disdetta richiesta"
        ) from exc
    except refund_service.RefundTooHigh as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Il rimborso non può superare quanto versato ({format_euro(exc.paid_cents)})",
        ) from exc
    db.refresh(booking)
    return _detail(db, booking, now)


@router.patch("/{booking_id}")
def edit_registration(
    booking_id: int,
    body: RegistrationPatch,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> RegistrationDetail:
    booking = _get_booking(db, booking_id)
    changes: dict[str, str | None] = {}
    for field in booking_admin_service.PERSON_FIELDS:
        if field not in body.model_fields_set:
            continue
        value = getattr(body, field)
        if value is None and field not in ("phone", "invited_by"):
            raise HTTPException(status_code=422, detail="Questo campo non può essere vuoto")
        optional = field in ("phone", "invited_by")
        changes[field] = (value or None) if optional else value
    new_expires = body.hold_expires_at
    if new_expires is not None and new_expires.tzinfo is None:
        new_expires = new_expires.replace(tzinfo=ROME)
    try:
        booking_admin_service.update_details(db, admin, booking, changes, new_expires, now)
    except booking_admin_service.EmailTaken as exc:
        raise HTTPException(
            status_code=409, detail="Questa email è già usata da un'altra persona"
        ) from exc
    except booking_admin_service.NotExtendable as exc:
        raise HTTPException(
            status_code=409, detail="Si può prorogare solo un blocco in attesa di pagamento"
        ) from exc
    except booking_admin_service.InvalidDeadline as exc:
        raise HTTPException(
            status_code=422, detail="La nuova scadenza deve essere successiva a quella attuale"
        ) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Questa email è già usata da un'altra persona"
        ) from exc
    db.refresh(booking)
    return _detail(db, booking, now)


@router.post("/{booking_id}/reactivate")
def reactivate_registration(
    booking_id: int,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
    now: datetime = Depends(get_now),
) -> RegistrationDetail:
    booking = _get_booking(db, booking_id)
    try:
        booking_admin_service.reactivate(db, sender, admin, booking, now)
    except booking_admin_service.NotExpired as exc:
        raise HTTPException(
            status_code=409, detail="Si può riattivare solo una prenotazione scaduta"
        ) from exc
    except SlotsFull as exc:
        db.rollback()
        labels = ", ".join(
            format_slot(s.date, s.period, s.start_time, s.end_time) for s in exc.slots
        )
        raise HTTPException(
            status_code=409, detail=f"Non c'è più posto in questi slot: {labels}"
        ) from exc
    db.refresh(booking)
    return _detail(db, booking, now)
