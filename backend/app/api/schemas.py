from collections.abc import Iterable
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.domain.booking import (
    can_edit_slots,
    can_request_cancellation,
    effective_status,
    is_past_day,
)
from app.domain.confirmation import confirmation_balance_cents, confirmation_due_cents
from app.domain.fees import balance_cents
from app.domain.meals import allowed_meals, meal_sort_key, periods_by_day
from app.i18n import current_locale
from app.models import (
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    Booking,
    Edition,
    active_payments,
    slot_sort_key,
)
from app.services.amounts import activity_terms, meal_terms
from app.timefmt import format_activity, format_meal, format_slot


class SlotView(BaseModel):
    id: int
    date: date
    period: str
    label: str


class CollectionTerms(BaseModel):
    price_cents: int
    payment_mode: str
    payment_instructions: str | None
    collectable_cents: int


class ScheduleSlotView(BaseModel):
    date: date
    period: str
    start_time: time
    end_time: time


class MealView(CollectionTerms):
    date: date
    kind: str
    label: str
    # The day is over (Europe/Rome): only an admin can change this meal.
    past: bool = False


class ActivityView(CollectionTerms):
    id: int
    title: str
    description: str | None
    label: str
    date: date
    period: str
    time_label: str | None = None
    start_time: time | None = None
    end_time: time | None = None


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
    confirmation_policy: str
    registration_fee_cents: int | None
    confirmation_due_cents: int | None
    confirmation_balance_cents: int | None
    amount_due_cents: int
    paid_cents: int
    balance_cents: int
    hold_expires_at: datetime
    created_at: datetime
    editable: bool
    can_cancel: bool
    slots: list[SlotView]
    schedule: list[ScheduleSlotView] = []
    payments: list[PaymentView]
    meals: list[MealView] = []
    activities: list[ActivityView] = []
    # Meals the person's presence allows, whether chosen or not.
    allowed_meals: list[MealView] = []
    # After a change of slots: meals that went because the new slots no longer allow them.
    dropped_meals: list[str] = []
    dropped_activities: list[str] = []
    # Dietary needs. Allergies are health data: only the person and the admins see them.
    diet: str | None = None
    allergies: str | None = None
    health_consent_version: int | None = None


def booking_view(booking: Booking, now: datetime, include_notes: bool = False) -> BookingView:
    edition = booking.edition
    paid = sum(p.amount_cents for p in active_payments(booking))
    slots = sorted(booking.slots, key=slot_sort_key)
    booked_dates = {slot.date for slot in slots}
    status = effective_status(booking.status, booking.hold_expires_at, now)
    confirmation_due = (
        confirmation_due_cents(
            edition.confirmation_policy, booking.amount_due_cents, booking.registration_fee_cents
        )
        if status in (STATUS_PENDING, STATUS_CONFIRMED, STATUS_EXPIRED)
        else None
    )
    return BookingView(
        id=booking.id,
        status=status,
        confirmation_policy=edition.confirmation_policy,
        registration_fee_cents=booking.registration_fee_cents,
        confirmation_due_cents=confirmation_due,
        confirmation_balance_cents=confirmation_balance_cents(
            status,
            edition.confirmation_policy,
            booking.amount_due_cents,
            booking.registration_fee_cents,
            paid,
        ),
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
        schedule=[
            ScheduleSlotView(
                date=s.date,
                period=s.period,
                start_time=s.start_time,
                end_time=s.end_time,
            )
            for s in sorted(slots[0].edition.slots, key=slot_sort_key)
            if s.date in booked_dates
        ]
        if slots
        else [],
        diet=booking.diet,
        allergies=booking.allergies,
        health_consent_version=booking.health_consent.version if booking.health_consent else None,
        activities=[
            ActivityView(
                id=a.id,
                title=(a.title_it if current_locale() == "it" else a.title_en) or a.title,
                description=(
                    (a.description_it if current_locale() == "it" else a.description_en)
                    or a.description
                ),
                label=format_activity(
                    (a.title_it if current_locale() == "it" else a.title_en) or a.title,
                    a.date,
                    a.period,
                ),
                date=a.date,
                period=a.period,
                time_label=a.time_label,
                start_time=a.starts_at.astimezone(ZoneInfo("Europe/Rome")).time()
                if a.starts_at
                else None,
                end_time=a.ends_at.astimezone(ZoneInfo("Europe/Rome")).time()
                if a.ends_at
                else None,
                **activity_terms(a),
            )
            for a in booking.activities
        ],
        meals=_meal_views(((m.date, m.kind) for m in booking.meals), now, edition),
        allowed_meals=_meal_views(
            allowed_meals(periods_by_day((s.date, s.period) for s in booking.slots)), now, edition
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


def _meal_views(
    meals: Iterable[tuple[date, str]], now: datetime, edition: Edition
) -> list[MealView]:
    return [
        MealView(
            date=day,
            kind=kind,
            label=format_meal(day, kind),
            past=is_past_day(day, now),
            **meal_terms(edition, day, kind),
        )
        for day, kind in sorted(meals, key=meal_sort_key)
    ]


class ActivityOffer(CollectionTerms):
    id: int
    title: str
    description: str | None
    date: date
    period: str
    time_label: str | None
    start_time: time | None
    end_time: time | None
    capacity: int | None
    free: int | None
    joined: bool
    past: bool


def activity_offers(db: Session, booking: Booking, now: datetime) -> list[ActivityOffer]:
    """Activities the booking holds or that its presence allows, with free seats."""
    from app.services.activities import offers_for

    return [
        ActivityOffer(
            id=a.id,
            title=(a.title_it if current_locale() == "it" else a.title_en) or a.title,
            description=(a.description_it if current_locale() == "it" else a.description_en)
            if (a.description_it if current_locale() == "it" else a.description_en)
            else a.description,
            date=a.date,
            period=a.period,
            time_label=a.time_label,
            start_time=a.starts_at.astimezone(ZoneInfo("Europe/Rome")).time()
            if a.starts_at
            else None,
            end_time=a.ends_at.astimezone(ZoneInfo("Europe/Rome")).time() if a.ends_at else None,
            **activity_terms(a),
            capacity=a.capacity,
            free=free,
            joined=joined,
            past=past,
        )
        for a, free, joined, past in offers_for(db, booking, now)
    ]
