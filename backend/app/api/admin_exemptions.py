"""Category, exemptions and refunds of credit on an active booking (MVP 25c). Admins only."""

from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy.orm import Session

from app.api.admin_registrations import RegistrationDetail, _detail, _get_booking
from app.db import get_db
from app.deps import get_email_sender, get_now, require_admin
from app.email import EmailSender
from app.i18n import t
from app.models import Participant
from app.services import booking_refunds
from app.services import exemptions as exemption_service
from app.services.payments import send_transition_confirmation
from app.timefmt import to_rome

router = APIRouter(
    prefix="/api/admin/registrations", tags=["admin"], dependencies=[Depends(require_admin)]
)

Text = Annotated[str, StringConstraints(strip_whitespace=True)]


class MealRef(BaseModel):
    date: date
    kind: Literal["lunch", "dinner"]


class CategoryIn(BaseModel):
    category: Literal["ordinary", "internal_non_paying"]


class ExemptionsIn(BaseModel):
    category: Literal["ordinary", "internal_non_paying"] = "ordinary"
    fee_exempt: bool = False
    meals: list[MealRef] = Field(default=[], max_length=200)
    activity_ids: list[int] = Field(default=[], max_length=200)

    def change(self) -> exemption_service.Change:
        return exemption_service.Change(
            category=self.category,
            fee_exempt=self.fee_exempt,
            meals=frozenset((m.date, m.kind) for m in self.meals),
            activities=frozenset(self.activity_ids),
        )


class ApplyIn(ExemptionsIn):
    preview_token: Annotated[str, Field(min_length=64, max_length=64)]


class RefundCreditIn(BaseModel):
    amount_cents: int = Field(gt=0, le=1_000_000)
    channel: Literal["revolut", "satispay", "paypal", "iban"]
    refunded_on: date | None = None
    note: Annotated[Text, Field(max_length=1000)] | None = None
    # The same request sent twice (double click, retry) is recorded once.
    request_key: UUID | None = None


class VoidIn(BaseModel):
    reason: Annotated[Text, Field(min_length=1, max_length=500)]


@router.put("/{booking_id}/category")
def set_category(
    booking_id: int,
    body: CategoryIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> RegistrationDetail:
    booking = _get_booking(db, booking_id)
    exemption_service.set_category(db, admin, booking, body.category)
    db.refresh(booking)
    return _detail(db, booking, now)


@router.post("/{booking_id}/exemptions/preview")
def preview_exemptions(
    booking_id: int,
    body: ExemptionsIn,
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> dict:
    booking = _get_booking(db, booking_id)
    try:
        return exemption_service.preview(db, booking, body.change(), now)
    except exemption_service.NotActive as exc:
        raise HTTPException(status_code=409, detail=t("exemptions.not_active")) from exc
    except exemption_service.InvalidChange as exc:
        raise HTTPException(status_code=422, detail=t("exemptions.invalid")) from exc


@router.post("/{booking_id}/exemptions/apply")
def apply_exemptions(
    booking_id: int,
    body: ApplyIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
    now: datetime = Depends(get_now),
) -> RegistrationDetail:
    booking = _get_booking(db, booking_id)
    try:
        result = exemption_service.apply(db, admin, booking, body.change(), body.preview_token, now)
    except exemption_service.NotActive as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=t("exemptions.not_active")) from exc
    except exemption_service.InvalidChange as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=t("exemptions.invalid")) from exc
    except exemption_service.PreviewChanged as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=t("exemptions.preview_changed")) from exc
    if result.confirmed_now:
        send_transition_confirmation(db, sender, booking, result.paid_cents, now)
    db.refresh(booking)
    return _detail(db, booking, now)


@router.post("/{booking_id}/refunds", status_code=201)
def add_credit_refund(
    booking_id: int,
    body: RefundCreditIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> RegistrationDetail:
    booking = _get_booking(db, booking_id)
    try:
        booking_refunds.record(
            db,
            admin,
            booking,
            body.amount_cents,
            body.channel,
            body.refunded_on or to_rome(now).date(),
            body.note,
            now,
            request_key=str(body.request_key) if body.request_key else None,
        )
    except booking_refunds.RequestConflict as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"code": "payment_request_conflict", "message": t("payment.retry_conflict")},
        ) from exc
    except booking_refunds.NotActive as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=t("booking_refund.not_active")) from exc
    except booking_refunds.RefundRefused as exc:
        db.rollback()
        key = (
            "booking_refund.too_high"
            if exc.reason == "refund_too_high"
            else "booking_refund.invalid_amount"
        )
        raise HTTPException(status_code=422, detail=t(key)) from exc
    db.refresh(booking)
    return _detail(db, booking, now)


@router.post("/{booking_id}/refunds/{refund_id}/void")
def void_credit_refund(
    booking_id: int,
    refund_id: int,
    body: VoidIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> RegistrationDetail:
    booking = _get_booking(db, booking_id)
    try:
        booking_refunds.void(db, admin, booking, refund_id, body.reason, now)
    except booking_refunds.RefundNotFound as exc:
        raise HTTPException(status_code=404, detail=t("booking_refund.not_found")) from exc
    except booking_refunds.AlreadyVoided as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=t("booking_refund.already_voided")) from exc
    db.refresh(booking)
    return _detail(db, booking, now)
