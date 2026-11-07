"""The one place that computes what a booking owes."""

from datetime import date

from app.domain.collection import collectable
from app.domain.fees import compute_fee
from app.models import MEAL_LUNCH, Activity, Booking, Edition


def meal_terms(edition: Edition, day: date, kind: str) -> dict:
    setting = next((m for m in edition.meal_settings if (m.date, m.kind) == (day, kind)), None)
    mode = setting.payment_mode if setting else "organizer"
    price = edition.lunch_price_cents if kind == MEAL_LUNCH else edition.dinner_price_cents
    if setting is not None and setting.price_cents is not None:
        price = setting.price_cents
    return dict(
        payment_mode=mode,
        price_cents=price,
        collectable_cents=collectable(price, mode),
        payment_instructions=setting.payment_instructions if setting else None,
    )


def activity_terms(activity: Activity) -> dict:
    return dict(
        payment_mode=activity.payment_mode,
        price_cents=activity.price_cents,
        collectable_cents=collectable(activity.price_cents, activity.payment_mode),
        payment_instructions=activity.payment_instructions,
    )


def recompute_amount(edition: Edition, booking: Booking) -> int:
    """Set the amount due from the booking's slots, meals and paid activities, at the current
    prices (D-017), and return it."""
    _, booking.amount_due_cents = calculate_amounts(edition, booking)
    return booking.amount_due_cents


def calculate_amounts(edition: Edition, booking: Booking) -> tuple[int, int]:
    """Calculate the base-plus-days registration fee and total organiser receivable."""
    registration_fee_cents = compute_fee(
        [s.date for s in booking.slots], edition.base_fee_cents, edition.per_day_fee_cents
    )
    total_due_cents = registration_fee_cents + sum(
        meal_terms(edition, m.date, m.kind)["collectable_cents"] for m in booking.meals
    )
    total_due_cents += sum(collectable(a.price_cents, a.payment_mode) for a in booking.activities)
    return registration_fee_cents, total_due_cents
