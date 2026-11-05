from datetime import date

import pytest

from app.domain.fees import compute_amount_due, compute_fee
from app.domain.meals import (
    allowed_meals,
    can_have_dinner,
    can_have_lunch,
    check_health_data,
    check_meal_change,
    diet_counts,
    meal_counts_by_day,
    meals_to_drop,
    periods_by_day,
)
from app.models import MEAL_DINNER, MEAL_LUNCH

MON, TUE = date(2026, 7, 13), date(2026, 7, 14)


@pytest.mark.parametrize(
    ("periods", "lunch", "dinner"),
    [
        ({"morning"}, True, False),
        ({"afternoon"}, True, False),
        ({"evening"}, False, True),
        ({"morning", "afternoon"}, True, True),  # whole day: derived evening (D-009)
        ({"morning", "evening"}, True, True),
        (set(), False, False),
    ],
)
def test_presence_decides_lunch_and_dinner(periods, lunch, dinner):
    assert can_have_lunch(periods) is lunch
    assert can_have_dinner(periods) is dinner


def test_allowed_meals_per_day():
    periods = periods_by_day([(MON, "morning"), (TUE, "evening")])
    assert allowed_meals(periods) == {(MON, MEAL_LUNCH), (TUE, MEAL_DINNER)}


def test_dropping_a_slot_drops_the_meals_it_allowed():
    meals = {(MON, MEAL_LUNCH), (MON, MEAL_DINNER)}
    assert meals_to_drop(meals, periods_by_day([(MON, "evening")])) == {(MON, MEAL_LUNCH)}
    assert meals_to_drop(meals, {}) == meals


def test_dinner_stays_when_the_explicit_evening_goes_but_the_whole_day_remains():
    meals = {(MON, MEAL_LUNCH), (MON, MEAL_DINNER)}
    periods = periods_by_day([(MON, "morning"), (MON, "afternoon")])
    assert meals_to_drop(meals, periods) == set()


def test_meal_change_needs_presence():
    check = check_meal_change(set(), {(MON, MEAL_DINNER)}, {(MON, MEAL_LUNCH)}, set())
    assert (check.ok, check.reason, check.meals) == (False, "not_allowed", ((MON, MEAL_DINNER),))


def test_meal_change_on_a_past_day_only_for_admins():
    allowed = {(MON, MEAL_LUNCH), (TUE, MEAL_LUNCH)}
    current = {(MON, MEAL_LUNCH)}
    removing_past = check_meal_change(current, set(), allowed, {MON})
    assert (removing_past.ok, removing_past.reason) == (False, "past_day")
    adding_today = check_meal_change(current, current | {(TUE, MEAL_LUNCH)}, allowed, {MON})
    assert adding_today.ok
    assert check_meal_change(current, set(), allowed, {MON}, allow_past=True).ok


def test_allergies_need_the_consent():
    refused = check_health_data("Arachidi", consent=False)
    assert (refused.ok, refused.reason) == (False, "consent_required")
    saved = check_health_data("  Arachidi  ", consent=True)
    assert (saved.ok, saved.allergies) == (True, "Arachidi")


def test_withdrawing_the_consent_clears_the_allergies():
    cleared = check_health_data("", consent=False)
    assert (cleared.ok, cleared.allergies) == (True, None)
    assert check_health_data(None, consent=True).allergies is None


def test_diet_counts_include_who_did_not_say():
    counts = diet_counts(["vegan", "omnivore", None, "omnivore", "something else"])
    assert counts == {"omnivore": 2, "vegetarian": 0, "vegan": 1, "none": 2}


def test_meal_counts_list_every_day():
    counts = meal_counts_by_day(
        [(MON, MEAL_LUNCH), (MON, MEAL_LUNCH), (MON, MEAL_DINNER)], [TUE, MON]
    )
    assert counts == {MON: {"lunch": 2, "dinner": 1}, TUE: {"lunch": 0, "dinner": 0}}


def test_amount_due_adds_the_meals_to_the_fee():
    days = [MON, TUE]
    assert compute_amount_due(days, 0, 0, 1000, 100, 800, 1200) == compute_fee(days, 1000, 100)
    assert compute_amount_due(days, 2, 1, 1000, 100, 800, 1200) == 1200 + 1600 + 1200
