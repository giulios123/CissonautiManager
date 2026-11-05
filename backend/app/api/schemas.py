from collections.abc import Iterable
from datetime import date, datetime

from pydantic import BaseModel

from app.domain.booking import (
    can_edit_slots,
    can_request_cancellation,
    effective_status,
    is_past_day,
)
from app.domain.fees import balance_cents
from app.domain.meals import allowed_meals, periods_by_day
from app.models import MEAL_DINNER, MEAL_LUNCH, Booking, active_payments, slot_sort_key
from app.timefmt import format_meal, format_slot


class SlotView(BaseModel):
    id: int
    date: date
    period: str
    label: str


class MealView(BaseModel):
    date: date
    kind: str
    label: str
    # The day is over (Europe/Rome): only an admin can change this meal.
    past: bool = False


class PaymentView(BaseModel):
    id: int
    amount_cents: int
    channel: str
    paid_on: date
    note: str | None = None
    voided: bool = False
    void_reason: str | None = None


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
    meals: list[MealView] = []
    # Meals the person's presence allows, whether chosen or not.
    allowed_meals: list[MealView] = []
    # After a change of slots: meals that went because the new slots no longer allow them.
    dropped_meals: list[str] = []


def booking_view(booking: Booking, now: datetime, include_notes: bool = False) -> BookingView:
    paid = sum(p.amount_cents for p in active_payments(booking))
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
        meals=_meal_views(((m.date, m.kind) for m in booking.meals), now),
        allowed_meals=_meal_views(
            allowed_meals(periods_by_day((s.date, s.period) for s in booking.slots)), now
        ),
        # Admins see voided payments too (struck through); participants only the ones that count.
        payments=[
            PaymentView(
                id=p.id,
                amount_cents=p.amount_cents,
                channel=p.channel,
                paid_on=p.paid_on,
                note=p.note if include_notes else None,
                voided=p.voided_at is not None,
                void_reason=p.void_reason if include_notes else None,
            )
            for p in (booking.payments if include_notes else active_payments(booking))
        ],
    )


MEAL_ORDER = {MEAL_LUNCH: 0, MEAL_DINNER: 1}


def _meal_views(meals: Iterable[tuple[date, str]], now: datetime) -> list[MealView]:
    return [
        MealView(date=day, kind=kind, label=format_meal(day, kind), past=is_past_day(day, now))
        for day, kind in sorted(meals, key=lambda m: (m[0], MEAL_ORDER.get(m[1], 9)))
    ]
