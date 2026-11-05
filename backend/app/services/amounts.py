"""The one place that computes what a booking owes."""

from app.domain.fees import compute_amount_due
from app.models import MEAL_DINNER, MEAL_LUNCH, Booking, Edition


def recompute_amount(edition: Edition, booking: Booking) -> int:
    """Set the amount due from the booking's slots and meals, at the edition's current prices
    (D-017), and return it."""
    kinds = [meal.kind for meal in booking.meals]
    booking.amount_due_cents = compute_amount_due(
        [s.date for s in booking.slots],
        kinds.count(MEAL_LUNCH),
        kinds.count(MEAL_DINNER),
        edition.base_fee_cents,
        edition.per_day_fee_cents,
        edition.lunch_price_cents,
        edition.dinner_price_cents,
    )
    return booking.amount_due_cents
