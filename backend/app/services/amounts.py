"""The one place that computes what a booking owes."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import object_session

from app.domain.collection import collectable
from app.domain.confirmation import confirmation_due_cents
from app.domain.exemptions import Exemptions, counted, included_meal
from app.domain.fees import compute_fee
from app.models import MEAL_LUNCH, Activity, Booking, BookingActivity, Edition


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
    meals = [(meal.date, meal.kind) for meal in booking.meals]
    registration_fee_cents, total_due_cents, included = calculate_meal_selection(
        edition, booking, meals
    )
    for meal in booking.meals:
        meal.included_in_fee = (meal.date, meal.kind) == included
    return registration_fee_cents, total_due_cents


def exemptions_of(booking: Booking) -> Exemptions:
    """What is exempted on the booking now (MVP 25c)."""
    return Exemptions(
        fee=booking.fee_exempt,
        meals=frozenset((m.date, m.kind) for m in booking.meals if m.exempt),
        activities=frozenset(link.activity_id for link in _activity_links(booking) if link.exempt),
    )


def _activity_links(booking: Booking):
    """The association rows of the booking's activities. A booking not saved yet has none."""
    if booking.id is None:
        return []
    session = object_session(booking)
    if session is None:
        return []
    return session.scalars(select(BookingActivity).where(BookingActivity.booking_id == booking.id))


def calculate_meal_selection(
    edition: Edition,
    booking: Booking,
    selected: list[tuple[date, str]],
    exemptions: Exemptions | None = None,
) -> tuple[int, int, tuple[date, str] | None]:
    """Calculate fee, total due, and included meal for a proposed selection.

    `exemptions` defaults to what is saved on the booking; the preview of an exemption change
    passes the proposed ones. An exempt item is worth zero and the others stay due.
    """
    exempt = exemptions if exemptions is not None else exemptions_of(booking)
    registration_fee_cents = counted(
        compute_fee(
            [s.date for s in booking.slots], edition.base_fee_cents, edition.per_day_fee_cents
        ),
        exempt.fee,
    )
    meals = sorted(selected, key=lambda meal: (meal[0], meal[1] != MEAL_LUNCH))
    included = included_meal(
        meals,
        {m: meal_terms(edition, m[0], m[1])["payment_mode"] == "organizer" for m in meals},
        exempt.meals,
        enabled=(
            edition.confirmation_policy == "registration_fee"
            and edition.included_meal_policy == "first_organizer_meal"
        ),
    )
    total_due_cents = registration_fee_cents + sum(
        0
        if (day, kind) == included
        else counted(
            meal_terms(edition, day, kind)["collectable_cents"], (day, kind) in exempt.meals
        )
        for day, kind in meals
    )
    total_due_cents += sum(
        counted(collectable(a.price_cents, a.payment_mode), a.id in exempt.activities)
        for a in booking.activities
    )
    return registration_fee_cents, total_due_cents, included


def confirmation_due(edition: Edition, booking: Booking) -> int | None:
    """The saved amount a booking must cover to hold its place under this edition's policy."""
    return confirmation_due_cents(
        edition.confirmation_policy, booking.amount_due_cents, booking.registration_fee_cents
    )


def confirmation_covered(edition: Edition, booking: Booking, paid_cents: int) -> bool:
    due = confirmation_due(edition, booking)
    return due is not None and paid_cents >= due
