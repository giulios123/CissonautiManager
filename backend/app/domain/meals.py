"""Lunches and dinners: who can take part, and what happens when slots change. Pure functions.

Meals are (day, kind) pairs. Presence decides eligibility: any daytime slot allows lunch, and the
evening (booked, or derived from booking the whole day, D-009) allows dinner.
"""

from collections import Counter
from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.domain.presence import has_evening
from app.models import DIETS, MEAL_DINNER, MEAL_LUNCH, PERIOD_AFTERNOON, PERIOD_MORNING

Meal = tuple[date, str]
MealRefusal = Literal["not_allowed", "past_day"]
HealthRefusal = Literal["consent_required"]

NO_DIET = "none"


@dataclass(frozen=True)
class MealCheck:
    ok: bool
    reason: MealRefusal | None = None
    meals: tuple[Meal, ...] = ()


@dataclass(frozen=True)
class HealthData:
    ok: bool
    allergies: str | None = None
    reason: HealthRefusal | None = None


def meal_sort_key(meal: Meal) -> tuple[date, int]:
    """Chronological order: by day, lunch before dinner."""
    return (meal[0], 0 if meal[1] == MEAL_LUNCH else 1)


def can_have_lunch(periods: Collection[str]) -> bool:
    return PERIOD_MORNING in periods or PERIOD_AFTERNOON in periods


def can_have_dinner(periods: Collection[str]) -> bool:
    return has_evening(periods)


def periods_by_day(slots: Iterable[tuple[date, str]]) -> dict[date, set[str]]:
    result: dict[date, set[str]] = {}
    for day, period in slots:
        result.setdefault(day, set()).add(period)
    return result


def allowed_meals(periods: Mapping[date, Collection[str]]) -> set[Meal]:
    allowed: set[Meal] = set()
    for day, day_periods in periods.items():
        if can_have_lunch(day_periods):
            allowed.add((day, MEAL_LUNCH))
        if can_have_dinner(day_periods):
            allowed.add((day, MEAL_DINNER))
    return allowed


def meals_to_drop(meals: Iterable[Meal], periods: Mapping[date, Collection[str]]) -> set[Meal]:
    """Meals the person no longer has a right to after a change of slots."""
    allowed = allowed_meals(periods)
    return {meal for meal in meals if meal not in allowed}


def check_meal_change(
    current: Collection[Meal],
    wanted: Collection[Meal],
    allowed: Collection[Meal],
    past_days: Collection[date],
    allow_past: bool = False,
) -> MealCheck:
    """Whether the meals can go from `current` to `wanted`.

    Every wanted meal needs the presence that allows it. Meals of days already over cannot be
    added or removed, unless an admin makes the change.
    """
    not_allowed = tuple(sorted(m for m in wanted if m not in allowed))
    if not_allowed:
        return MealCheck(False, "not_allowed", not_allowed)
    if not allow_past:
        changed = set(current) ^ set(wanted)
        past = tuple(sorted(m for m in changed if m[0] in past_days))
        if past:
            return MealCheck(False, "past_day", past)
    return MealCheck(True)


def check_health_data(allergies: str | None, consent: bool) -> HealthData:
    """Allergies are health data: they are kept only with the specific consent.

    Without consent, any allergy text is refused; an empty field simply clears what was stored.
    """
    text = (allergies or "").strip() or None
    if not consent:
        if text is not None:
            return HealthData(False, reason="consent_required")
        return HealthData(True, allergies=None)
    return HealthData(True, allergies=text)


def diet_counts(diets: Iterable[str | None]) -> dict[str, int]:
    """How many people per diet, with those who did not say counted as `none`."""
    counted = Counter(diet if diet in DIETS else NO_DIET for diet in diets)
    return {key: counted.get(key, 0) for key in (*DIETS, NO_DIET)}


def meal_counts_by_day(meals: Iterable[Meal], days: Iterable[date]) -> dict[date, dict[str, int]]:
    """Lunches and dinners per day, every day of the edition listed (zero when nobody eats)."""
    counted = Counter(meals)
    return {
        day: {
            MEAL_LUNCH: counted.get((day, MEAL_LUNCH), 0),
            MEAL_DINNER: counted.get((day, MEAL_DINNER), 0),
        }
        for day in sorted(set(days))
    }
