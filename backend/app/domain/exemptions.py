"""Exemptions and refunds on an active booking (MVP 25c). Pure functions.

A booking has a category and can have the fee and single meals or activities exempted by an admin.
An exempted item is worth zero; the others stay due. A refund on a booking that is still active
(pending or confirmed) never exceeds the credit, so it never takes away what covers the place.
"""

from collections.abc import Collection, Iterable
from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.models import MEAL_LUNCH

CATEGORY_ORDINARY = "ordinary"
CATEGORY_INTERNAL_NON_PAYING = "internal_non_paying"
CATEGORIES = (CATEGORY_ORDINARY, CATEGORY_INTERNAL_NON_PAYING)

Meal = tuple[date, str]
RefundRefusal = Literal["invalid_amount", "refund_too_high"]


@dataclass(frozen=True)
class Exemptions:
    """What an admin exempted: the fee and/or single meals and activities."""

    fee: bool = False
    meals: frozenset[Meal] = frozenset()
    activities: frozenset[int] = frozenset()

    @property
    def empty(self) -> bool:
        return not self.fee and not self.meals and not self.activities


def counted(collectable_cents: int, exempt: bool) -> int:
    """What an item adds to the amount due: nothing when it is exempt."""
    return 0 if exempt else collectable_cents


def included_meal(
    meals: Iterable[Meal],
    is_organizer: dict[Meal, bool],
    exempt: Collection[Meal],
    enabled: bool,
) -> Meal | None:
    """The meal the fee covers: the first one, lunch before dinner, that the organisation
    collects and that is not exempt (an exempt meal costs nothing, so covering it would waste
    the inclusion)."""
    if not enabled:
        return None
    ordered = sorted(meals, key=lambda meal: (meal[0], meal[1] != MEAL_LUNCH))
    return next((m for m in ordered if is_organizer.get(m, False) and m not in exempt), None)


def net_paid_cents(gross_paid_cents: int, active_refunds_cents: int) -> int:
    """What counts as paid: the payments that count minus the refunds that count."""
    return gross_paid_cents - active_refunds_cents


def credit_cents(net_paid: int, amount_due_cents: int) -> int:
    """What was paid beyond the total due, and so can be given back."""
    return max(net_paid - amount_due_cents, 0)


def check_refund(amount_cents: int, net_paid: int, amount_due_cents: int) -> RefundRefusal | None:
    if amount_cents <= 0:
        return "invalid_amount"
    if amount_cents > credit_cents(net_paid, amount_due_cents):
        return "refund_too_high"
    return None


def can_void_payment(payment_cents: int, gross_paid_cents: int, active_refunds_cents: int) -> bool:
    """A payment cannot be voided if the refunds on record would then exceed what remains."""
    return gross_paid_cents - payment_cents >= active_refunds_cents
