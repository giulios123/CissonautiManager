"""Who is entitled to the benefits of the edition (MVP 30, D-121). Pure functions.

This is not the rule that confirms a place (base fee plus days, MVP 18): the base fee alone, or
being an internal person who does not pay, is what counts here.
"""

from app.models import CATEGORY_INTERNAL_NON_PAYING


def is_entitled(
    *,
    active: bool,
    category: str,
    fee_exempt: bool,
    net_paid_cents: int,
    base_fee_cents: int,
) -> bool:
    """An active booking (pending or confirmed) and at least one of:

    - the category is "internal, non paying" (a speaker);
    - the fee is exempted by an admin, even when the category stays "ordinary";
    - what was paid, net of refunds, covers the base fee. With a base fee of zero this alone is
      not enough, or everybody would be entitled.
    """
    if not active:
        return False
    if category == CATEGORY_INTERNAL_NON_PAYING or fee_exempt:
        return True
    return base_fee_cents > 0 and net_paid_cents >= base_fee_cents
