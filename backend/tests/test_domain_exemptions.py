from datetime import date

import pytest

from app.domain.exemptions import (
    Exemptions,
    can_void_payment,
    check_refund,
    counted,
    credit_cents,
    included_meal,
    net_paid_cents,
)

MON, TUE = date(2026, 7, 13), date(2026, 7, 14)
ORGANIZER = {
    (MON, "lunch"): True,
    (MON, "dinner"): True,
    (TUE, "lunch"): True,
}


class TestCounted:
    @pytest.mark.parametrize(
        ("cents", "exempt", "expected"), [(800, False, 800), (800, True, 0), (0, True, 0)]
    )
    def test_an_exempt_item_is_worth_zero(self, cents, exempt, expected):
        assert counted(cents, exempt) == expected

    def test_nothing_exempt_by_default(self):
        assert Exemptions().empty
        assert not Exemptions(fee=True).empty
        assert not Exemptions(activities=frozenset({3})).empty


class TestIncludedMeal:
    meals = [(TUE, "lunch"), (MON, "dinner"), (MON, "lunch")]

    def test_the_first_meal_lunch_before_dinner(self):
        assert included_meal(self.meals, ORGANIZER, frozenset(), True) == (MON, "lunch")

    def test_it_skips_an_exempt_meal(self):
        exempt = {(MON, "lunch")}
        assert included_meal(self.meals, ORGANIZER, exempt, True) == (MON, "dinner")

    def test_it_skips_a_provider_meal(self):
        assert included_meal(
            self.meals, {**ORGANIZER, (MON, "lunch"): False}, frozenset(), True
        ) == (MON, "dinner")

    def test_nothing_is_covered_when_every_meal_is_exempt(self):
        assert included_meal(self.meals, ORGANIZER, set(self.meals), True) is None

    def test_disabled_policy_covers_nothing(self):
        assert included_meal(self.meals, ORGANIZER, frozenset(), False) is None

    def test_no_meals_no_inclusion(self):
        assert included_meal([], ORGANIZER, frozenset(), True) is None


class TestNetAndCredit:
    def test_net_paid(self):
        assert net_paid_cents(1000, 0) == 1000
        assert net_paid_cents(1000, 300) == 700

    @pytest.mark.parametrize(
        ("net", "due", "credit"), [(1000, 800, 200), (800, 800, 0), (500, 800, 0), (0, 0, 0)]
    )
    def test_credit_is_what_exceeds_the_due(self, net, due, credit):
        assert credit_cents(net, due) == credit


class TestRefundCheck:
    @pytest.mark.parametrize(
        ("amount", "net", "due", "expected"),
        [
            (200, 1000, 800, None),
            (201, 1000, 800, "refund_too_high"),
            (1, 800, 800, "refund_too_high"),
            (0, 1000, 800, "invalid_amount"),
            (-5, 1000, 800, "invalid_amount"),
            (500, 500, 0, None),  # everything exempted: all that was paid is credit
            (501, 500, 0, "refund_too_high"),
        ],
    )
    def test_a_refund_never_exceeds_the_credit(self, amount, net, due, expected):
        assert check_refund(amount, net, due) == expected

    def test_a_refund_up_to_the_credit_keeps_what_the_due_needs(self):
        net, due = 1000, 800
        credit = credit_cents(net, due)
        assert check_refund(credit, net, due) is None
        assert net_paid_cents(1000, credit) >= due


class TestVoidingAPayment:
    def test_blocked_when_refunds_would_exceed_what_remains(self):
        assert not can_void_payment(800, gross_paid_cents=1000, active_refunds_cents=300)

    def test_allowed_when_enough_remains(self):
        assert can_void_payment(300, gross_paid_cents=1000, active_refunds_cents=300)

    def test_allowed_without_refunds(self):
        assert can_void_payment(1000, gross_paid_cents=1000, active_refunds_cents=0)
