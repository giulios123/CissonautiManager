from datetime import date, datetime

from pydantic import BaseModel

from app.domain.booking import can_edit_slots, can_request_cancellation, effective_status
from app.domain.fees import balance_cents
from app.models import Booking, slot_sort_key
from app.timefmt import format_slot


class SlotView(BaseModel):
    id: int
    date: date
    period: str
    label: str


class PaymentView(BaseModel):
    amount_cents: int
    channel: str
    paid_on: date
    note: str | None = None


class BookingView(BaseModel):
    id: int
    status: str
    amount_due_cents: int
    paid_cents: int
    balance_cents: int
    hold_expires_at: datetime
    created_at: datetime
    editable: bool
    can_cancel: bool
    slots: list[SlotView]
    payments: list[PaymentView]


def booking_view(booking: Booking, now: datetime, include_notes: bool = False) -> BookingView:
    paid = sum(p.amount_cents for p in booking.payments)
    slots = sorted(booking.slots, key=slot_sort_key)
    status = effective_status(booking.status, booking.hold_expires_at, now)
    return BookingView(
        id=booking.id,
        status=status,
        amount_due_cents=booking.amount_due_cents,
        paid_cents=paid,
        balance_cents=balance_cents(booking.amount_due_cents, paid),
        hold_expires_at=booking.hold_expires_at,
        created_at=booking.created_at,
        editable=can_edit_slots(status),
        can_cancel=can_request_cancellation(status),
        slots=[
            SlotView(
                id=s.id,
                date=s.date,
                period=s.period,
                label=format_slot(s.date, s.period, s.start_time, s.end_time),
            )
            for s in slots
        ],
        payments=[
            PaymentView(
                amount_cents=p.amount_cents,
                channel=p.channel,
                paid_on=p.paid_on,
                note=p.note if include_notes else None,
            )
            for p in booking.payments
        ],
    )
