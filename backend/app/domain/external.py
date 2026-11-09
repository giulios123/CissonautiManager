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
from app.models import MEAL_DINNER, MEAL_LUNCH, PAYER_PAYING

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


# --- Money (MVP 25b) -------------------------------------------------------------------------
# A guest has no booking: what they owe is read from the current prices of their meals and
# activities, and what they paid sits in a register apart from the payments of the bookings.

MOVEMENT_PAYMENT = "payment"
MOVEMENT_REFUND = "refund"
MOVEMENT_KINDS = (MOVEMENT_PAYMENT, MOVEMENT_REFUND)


@dataclass(frozen=True)
class Movement:
    kind: str
    amount_cents: int
    voided: bool = False


@dataclass(frozen=True)
class GuestAccount:
    due_cents: int
    paid_cents: int  # payments that count
    refunded_cents: int  # refunds that count

    @property
    def net_cents(self) -> int:
        """What the organisation keeps from this guest."""
        return self.paid_cents - self.refunded_cents

    @property
    def balance_cents(self) -> int:
        """Still to pay when positive, credit when negative."""
        return self.due_cents - self.net_cents

    @property
    def credit_cents(self) -> int:
        return max(-self.balance_cents, 0)

    @property
    def to_collect_cents(self) -> int:
        return max(self.balance_cents, 0)


def guest_due_cents(payer: str, collectable_cents: Iterable[int]) -> int:
    """The sum of the items the organisation collects. A non-paying guest owes nothing. There is
    no registration fee and no meal covered by it for guests."""
    return sum(collectable_cents) if payer == PAYER_PAYING else 0


def guest_account(due_cents: int, movements: Iterable[Movement]) -> GuestAccount:
    active = [m for m in movements if not m.voided]
    return GuestAccount(
        due_cents=due_cents,
        paid_cents=sum(m.amount_cents for m in active if m.kind == MOVEMENT_PAYMENT),
        refunded_cents=sum(m.amount_cents for m in active if m.kind == MOVEMENT_REFUND),
    )


MovementRefusal = Literal["invalid_amount", "refund_too_high"]


def check_movement(kind: str, amount_cents: int, account: GuestAccount) -> MovementRefusal | None:
    """Whether a payment or refund can be recorded now. A refund never exceeds the credit."""
    if amount_cents <= 0:
        return "invalid_amount"
    if kind == MOVEMENT_REFUND and amount_cents > account.credit_cents:
        return "refund_too_high"
    return None


def can_void(kind: str, amount_cents: int, account: GuestAccount) -> bool:
    """Voiding a payment must not leave more refunded than paid: void the refund first."""
    if kind == MOVEMENT_REFUND:
        return True
    return account.paid_cents - amount_cents >= account.refunded_cents
