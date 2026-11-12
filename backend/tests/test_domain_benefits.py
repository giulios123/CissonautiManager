import pytest

from app.domain.benefits import is_entitled
from app.models import CATEGORY_INTERNAL_NON_PAYING, CATEGORY_ORDINARY


def entitled(**overrides) -> bool:
    values = dict(
        active=True,
        category=CATEGORY_ORDINARY,
        fee_exempt=False,
        net_paid_cents=0,
        base_fee_cents=1000,
    )
    values.update(overrides)
    return is_entitled(**values)


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"net_paid_cents": 1000}, True),  # the base fee exactly
        ({"net_paid_cents": 1500}, True),  # more than the base fee
        ({"net_paid_cents": 999}, False),  # one cent short
        ({"net_paid_cents": 0}, False),
        ({"category": CATEGORY_INTERNAL_NON_PAYING}, True),  # a speaker, nothing paid
        ({"fee_exempt": True}, True),  # ordinary, but the fee is exempted
        ({"category": CATEGORY_INTERNAL_NON_PAYING, "net_paid_cents": 5000}, True),
        ({"base_fee_cents": 0}, False),  # a free base fee does not entitle by itself
        ({"base_fee_cents": 0, "net_paid_cents": 700}, False),
        ({"base_fee_cents": 0, "fee_exempt": True}, True),
        ({"base_fee_cents": 0, "category": CATEGORY_INTERNAL_NON_PAYING}, True),
        ({"net_paid_cents": 1200, "base_fee_cents": 1000}, True),
        # A refund brings the net below the base fee: no longer entitled.
        ({"net_paid_cents": 400}, False),
    ],
)
def test_entitlement(overrides, expected):
    assert entitled(**overrides) is expected


@pytest.mark.parametrize(
    "overrides",
    [
        {"net_paid_cents": 5000},
        {"category": CATEGORY_INTERNAL_NON_PAYING},
        {"fee_exempt": True},
    ],
)
def test_a_booking_that_is_not_active_has_no_entitlement(overrides):
    # Expired, cancellation requested or refunded: never, whatever else is true.
    assert entitled(active=False, **overrides) is False
