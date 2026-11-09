"""Refunds on a booking that is still active (MVP 25c).

A refund gives back credit: what was paid beyond the total due. It changes neither the status of
the place nor the payments, which stay on record, and sends no email. It is not the refund that
closes a cancellation (`app.services.refunds`). A mistaken refund is voided with a reason.
"""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.booking import effective_status, occupies_seats
from app.domain.exemptions import check_refund
from app.models import Booking, BookingRefund, Participant
from app.services import audit
from app.services.payments import paid_total
from app.services.seats import lock_booking, lock_edition
from app.timefmt import format_euro


class NotActive(Exception):
    """Only a pending or confirmed booking has an active refund."""


class RefundRefused(Exception):
    def __init__(self, reason: str):
        self.reason = reason  # "invalid_amount" or "refund_too_high"


class RequestConflict(Exception):
    """The same request key came back with different data."""


class RefundNotFound(Exception):
    pass


class AlreadyVoided(Exception):
    pass


def record(
    db: Session,
    admin: Participant,
    booking: Booking,
    amount_cents: int,
    channel: str,
    refunded_on: date,
    note: str | None,
    now: datetime,
    request_key: str | None = None,
) -> tuple[BookingRefund, bool]:
    """Record a refund up to the credit. Returns it and whether it was already recorded."""
    lock_edition(db, booking.edition_id)
    lock_booking(db, booking.id)
    db.refresh(booking)
    if request_key is not None:
        existing = db.scalar(select(BookingRefund).where(BookingRefund.request_key == request_key))
        if existing is not None:
            if (
                existing.booking_id != booking.id
                or existing.amount_cents != amount_cents
                or existing.channel != channel
                or existing.refunded_on != refunded_on
                or existing.note != (note or None)
                or existing.recorded_by_id != admin.id
            ):
                raise RequestConflict()
            return existing, True
    if not occupies_seats(effective_status(booking.status, booking.hold_expires_at, now)):
        raise NotActive()
    refusal = check_refund(amount_cents, paid_total(booking), booking.amount_due_cents)
    if refusal is not None:
        raise RefundRefused(refusal)
    refund = BookingRefund(
        booking_id=booking.id,
        amount_cents=amount_cents,
        channel=channel,
        refunded_on=refunded_on,
        note=note or None,
        recorded_by_id=admin.id,
        created_at=now,
        request_key=request_key,
    )
    db.add(refund)
    audit.log(
        db,
        admin,
        "booking_refund",
        f"Rimborso di {format_euro(amount_cents)} il {refunded_on:%d/%m/%Y} ({channel})"
        + (f": {note}" if note else ""),
        booking.id,
    )
    db.commit()
    return refund, False


def void(
    db: Session,
    admin: Participant,
    booking: Booking,
    refund_id: int,
    reason: str,
    now: datetime,
) -> BookingRefund:
    lock_edition(db, booking.edition_id)
    lock_booking(db, booking.id)
    db.refresh(booking)
    refund = db.get(BookingRefund, refund_id)
    if refund is None or refund.booking_id != booking.id:
        raise RefundNotFound()
    db.refresh(refund)
    if refund.voided_at is not None:
        raise AlreadyVoided()
    refund.voided_at = now
    refund.voided_by_id = admin.id
    refund.void_reason = reason
    audit.log(
        db,
        admin,
        "booking_refund_voided",
        f"Rimborso annullato: {format_euro(refund.amount_cents)} del "
        f"{refund.refunded_on:%d/%m/%Y}. Motivo: {reason}.",
        booking.id,
    )
    db.commit()
    return refund
