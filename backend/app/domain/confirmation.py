"""Fee thresholds used to confirm a booking under either edition policy."""

from app.models import (
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
)

POLICY_LEGACY_TOTAL = "legacy_total"
POLICY_REGISTRATION_FEE = "registration_fee"
CONFIRMATION_POLICIES = (POLICY_LEGACY_TOTAL, POLICY_REGISTRATION_FEE)


def confirmation_due_cents(
    policy: str, amount_due_cents: int, registration_fee_cents: int | None
) -> int | None:
    """Return the amount that secures a seat, or None if the new policy lacks a saved fee."""
    if policy == POLICY_LEGACY_TOTAL:
        return amount_due_cents
    if policy == POLICY_REGISTRATION_FEE:
        return registration_fee_cents
    raise ValueError(f"Unknown confirmation policy: {policy}")


def confirmation_balance_cents(
    status: str,
    policy: str,
    amount_due_cents: int,
    registration_fee_cents: int | None,
    paid_cents: int,
) -> int | None:
    """Return the operational remainder; it is zero when confirmed and absent when closed."""
    if status == STATUS_CONFIRMED:
        return 0
    if status not in (STATUS_PENDING, STATUS_EXPIRED):
        return None
    due = confirmation_due_cents(policy, amount_due_cents, registration_fee_cents)
    return None if due is None else max(0, due - paid_cents)
