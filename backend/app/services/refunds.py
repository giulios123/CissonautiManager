from datetime import date

from sqlalchemy.orm import Session

from app.domain.booking import can_refund
from app.models import STATUS_CANCEL_REQUESTED, STATUS_REFUNDED, Booking, Participant
from app.services import audit
from app.services.payments import paid_total
from app.timefmt import format_euro


class NotRefundable(Exception):
    """The booking has no requested cancellation to close."""


class RefundTooHigh(Exception):
    def __init__(self, paid_cents: int) -> None:
        self.paid_cents = paid_cents
        super().__init__(f"Refund above what was paid ({paid_cents})")


def record_refund(
    db: Session,
    admin: Participant,
    booking: Booking,
    amount_cents: int,
    refunded_on: date,
    note: str | None,
) -> Booking:
    """Close a requested cancellation: the refund itself happened outside the system.

    No email is sent: the admin writes to the person, as the domain rules say. The amount can be
    zero (a cancellation with nothing paid still has to be closed) but never above what was paid.
    """
    db.refresh(booking)
    if booking.status != STATUS_CANCEL_REQUESTED:
        raise NotRefundable()
    paid = paid_total(booking)
    if not can_refund(booking.status, paid, amount_cents):
        raise RefundTooHigh(paid)
    booking.status = STATUS_REFUNDED
    booking.refund_cents = amount_cents
    booking.refunded_on = refunded_on
    booking.refund_note = note or None
    booking.refunded_by_id = admin.id
    audit.log(
        db,
        admin,
        "refund",
        f"Rimborso registrato: {format_euro(amount_cents)} il {refunded_on:%d/%m/%Y}"
        + (f" ({note})" if note else ""),
        booking_id=booking.id,
    )
    db.commit()
    return booking
