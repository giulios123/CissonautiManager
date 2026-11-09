from datetime import date

from app.domain.confirmation import (
    POLICY_LEGACY_TOTAL,
    POLICY_REGISTRATION_FEE,
    confirmation_balance_cents,
    confirmation_due_cents,
)
from app.models import Activity, BookingMeal, MealSetting, Slot
from app.services.amounts import calculate_amounts, recompute_amount


def test_registration_fee_is_base_plus_distinct_days_and_total_excludes_providers(
    db, edition, make_participant, make_booking
):
    slots = db.query(Slot).filter(Slot.date.in_([date(2026, 7, 13), date(2026, 7, 14)])).all()
    booking = make_booking(make_participant(), slots, amount_due_cents=0)
    booking.meals = [BookingMeal(date=date(2026, 7, 13), kind="lunch")]
    provider_meal = MealSetting(
        edition_id=edition.id,
        date=date(2026, 7, 14),
        kind="dinner",
        payment_mode="provider",
        price_cents=2400,
        payment_instructions="Pay the venue",
    )
    collected_activity = Activity(
        edition_id=edition.id,
        title="Workshop",
        date=date(2026, 7, 13),
        period="morning",
        payment_mode="organizer",
        price_cents=500,
    )
    provider_activity = Activity(
        edition_id=edition.id,
        title="Dinner",
        date=date(2026, 7, 14),
        period="evening",
        payment_mode="provider",
        price_cents=900,
    )
    booking.activities = [collected_activity, provider_activity]
    db.add(provider_meal)
    db.commit()
    db.refresh(edition)

    registration_fee, total_due = calculate_amounts(edition, booking)

    assert registration_fee == 1200  # Morning and afternoon on Monday count as one day.
    assert total_due == 2500  # One organiser lunch and workshop; direct provider costs stay out.
    assert recompute_amount(edition, booking) == total_due


def test_confirmation_threshold_and_remaining_amount_differ_from_total_balance():
    assert confirmation_due_cents(POLICY_LEGACY_TOTAL, 2400, 1200) == 2400
    assert confirmation_due_cents(POLICY_REGISTRATION_FEE, 2400, 1200) == 1200
    assert confirmation_due_cents(POLICY_REGISTRATION_FEE, 2400, None) is None
    assert (
        confirmation_balance_cents("in_attesa_pagamento", POLICY_REGISTRATION_FEE, 2400, 1200, 500)
        == 700
    )
    assert confirmation_balance_cents("confermata", POLICY_REGISTRATION_FEE, 2400, 1200, 500) == 0
    assert (
        confirmation_balance_cents("rimborsata", POLICY_REGISTRATION_FEE, 2400, 1200, 500) is None
    )


def test_first_organiser_meal_is_included_and_provider_meal_does_not_consume_it(
    db, edition, make_participant, make_booking
):
    edition.confirmation_policy = POLICY_REGISTRATION_FEE
    edition.included_meal_policy = "first_organizer_meal"
    booking = make_booking(make_participant(), [], amount_due_cents=0)
    booking.meals = [
        BookingMeal(date=date(2026, 7, 13), kind="lunch"),
        BookingMeal(date=date(2026, 7, 13), kind="dinner"),
    ]
    db.add(
        MealSetting(
            edition_id=edition.id,
            date=date(2026, 7, 13),
            kind="lunch",
            payment_mode="provider",
            price_cents=700,
            payment_instructions="Pay on site",
        )
    )
    db.commit()
    db.refresh(edition)

    registration_fee, total_due = calculate_amounts(edition, booking)

    assert registration_fee == 1000
    assert total_due == 1000
    assert next(meal for meal in booking.meals if meal.kind == "lunch").included_in_fee is False
    assert next(meal for meal in booking.meals if meal.kind == "dinner").included_in_fee is True
