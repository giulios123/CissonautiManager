"""The one place that computes what a booking owes."""

from app.domain.fees import compute_amount_due
from app.models import MEAL_DINNER, MEAL_LUNCH, Booking, Edition


def recompute_amount(edition: Edition, booking: Booking) -> int:
    """Set the amount due from the booking's slots, meals and paid activities, at the current
    prices (D-017), and return it."""
    kinds = [meal.kind for meal in booking.meals]
    booking.amount_due_cents = compute_amount_due(
        [s.date for s in booking.slots],
        kinds.count(MEAL_LUNCH),
        kinds.count(MEAL_DINNER),
        edition.base_fee_cents,
        edition.per_day_fee_cents,
        edition.lunch_price_cents,
        edition.dinner_price_cents,
        sum(activity.price_cents for activity in booking.activities),
    )
    return booking.amount_due_cents
