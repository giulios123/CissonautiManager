"""The one place that computes what a booking owes."""

from datetime import date

from app.domain.collection import collectable
from app.domain.confirmation import confirmation_due_cents
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
    booking.registration_fee_cents, booking.amount_due_cents = calculate_amounts(edition, booking)
    return booking.amount_due_cents


def calculate_amounts(edition: Edition, booking: Booking) -> tuple[int, int]:
    """Calculate the base-plus-days registration fee and total organiser receivable."""
    registration_fee_cents = compute_fee(
        [s.date for s in booking.slots], edition.base_fee_cents, edition.per_day_fee_cents
    )
    meals = sorted(booking.meals, key=lambda meal: (meal.date, meal.kind != MEAL_LUNCH))
    included = None
    if (
        edition.confirmation_policy == "registration_fee"
        and edition.included_meal_policy == "first_organizer_meal"
    ):
        included = next(
            (
                meal
                for meal in meals
                if meal_terms(edition, meal.date, meal.kind)["payment_mode"] == "organizer"
            ),
            None,
        )
    for meal in meals:
        meal.included_in_fee = meal is included
    total_due_cents = registration_fee_cents + sum(
        0 if m.included_in_fee else meal_terms(edition, m.date, m.kind)["collectable_cents"]
        for m in meals
    )
    total_due_cents += sum(collectable(a.price_cents, a.payment_mode) for a in booking.activities)
    return registration_fee_cents, total_due_cents


def confirmation_due(edition: Edition, booking: Booking) -> int | None:
    """The saved amount a booking must cover to hold its place under this edition's policy."""
    return confirmation_due_cents(
        edition.confirmation_policy, booking.amount_due_cents, booking.registration_fee_cents
    )


def confirmation_covered(edition: Edition, booking: Booking, paid_cents: int) -> bool:
    due = confirmation_due(edition, booking)
    return due is not None and paid_cents >= due
