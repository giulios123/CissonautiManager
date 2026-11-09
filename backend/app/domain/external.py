"""External guests: people without an account who take part in meals and activities.

Pure functions. An external guest is added by an admin with a minimal identity. They have no
booking and no coworking slot, so meals do not depend on presence (D-088), and a person counts once
per meal or activity whether they are a participant or a guest.
"""

from collections.abc import Collection, Iterable
from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.domain.meals import Meal
from app.models import MEAL_DINNER, MEAL_LUNCH

MealRefusal = Literal["unknown_kind", "outside_edition"]


@dataclass(frozen=True)
class Duplicate:
    """Someone already in the edition with the same name as a new guest."""

    kind: Literal["guest", "participant"]
    id: int
    first_name: str
    last_name: str


@dataclass(frozen=True)
class GuestMealCheck:
    ok: bool
    reason: MealRefusal | None = None
    meals: tuple[Meal, ...] = ()


def normalize_name(first_name: str, last_name: str) -> str:
    """Names compared without case and with spaces collapsed."""
    return " ".join(f"{first_name} {last_name}".split()).casefold()


def find_duplicates(
    first_name: str,
    last_name: str,
    guests: Iterable[tuple[int, str, str]],
    participants: Iterable[tuple[int, str, str]],
    *,
    ignore_guest_id: int | None = None,
) -> list[Duplicate]:
    """Guests and active participants with the same name.

    `guests` and `participants` are (id, first_name, last_name). When a guest is edited, pass its
    own id as `ignore_guest_id` so it does not clash with itself.
    """
    wanted = normalize_name(first_name, last_name)
    found: list[Duplicate] = []
    for guest_id, first, last in guests:
        if guest_id != ignore_guest_id and normalize_name(first, last) == wanted:
            found.append(Duplicate("guest", guest_id, first, last))
    for participant_id, first, last in participants:
        if normalize_name(first, last) == wanted:
            found.append(Duplicate("participant", participant_id, first, last))
    return found


def check_guest_meals(wanted: Collection[Meal], edition_days: Collection[date]) -> GuestMealCheck:
    """Guests may take any lunch or dinner on a day of the edition, even a past one.

    No presence is needed. This exception is for guests only: participants keep the rule that a
    meal needs the matching slot.
    """
    kinds = (MEAL_LUNCH, MEAL_DINNER)
    unknown = tuple(sorted(m for m in wanted if m[1] not in kinds))
    if unknown:
        return GuestMealCheck(False, "unknown_kind", unknown)
    outside = tuple(sorted(m for m in wanted if m[0] not in edition_days))
    if outside:
        return GuestMealCheck(False, "outside_edition", outside)
    return GuestMealCheck(True)


def participant_key(participant_id: int) -> str:
    return f"p:{participant_id}"


def guest_key(guest_id: int) -> str:
    return f"g:{guest_id}"


def merge_people(participant_ids: Iterable[int], guest_ids: Iterable[int]) -> set[str]:
    """One key per person. Participants and guests never share a key, and a repeated id counts
    once, so totals never count anyone twice."""
    return {participant_key(i) for i in participant_ids} | {guest_key(i) for i in guest_ids}
