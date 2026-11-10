from datetime import date

import pytest

from app.domain.external import (
    Movement,
    can_void,
    check_guest_meals,
    check_movement,
    find_duplicates,
    guest_account,
    guest_due_cents,
    guest_key,
    merge_people,
    normalize_name,
    participant_key,
)

DAYS = {date(2026, 7, 13), date(2026, 7, 14)}


@pytest.mark.parametrize(
    ("first", "last", "expected"),
    [
        ("Anna", "Rossi", "anna rossi"),
        ("  ANNA ", "rossi  ", "anna rossi"),
        ("Anna Maria", "De  Luca", "anna maria de luca"),
    ],
)
def test_normalize_name(first, last, expected):
    assert normalize_name(first, last) == expected


def test_duplicates_among_guests_and_participants():
    found = find_duplicates(
        "anna",
        " Rossi",
        guests=[(1, "Anna", "Rossi"), (2, "Luca", "Bianchi")],
        participants=[(7, "ANNA", "ROSSI"), (8, "Marta", "Verdi")],
    )
    assert [(d.kind, d.id) for d in found] == [("guest", 1), ("participant", 7)]


def test_no_duplicates_for_different_names():
    assert find_duplicates("Anna", "Rossi", [(1, "Anna", "Rossa")], [(2, "Anne", "Rossi")]) == []


def test_editing_a_guest_does_not_clash_with_itself():
    guests = [(1, "Anna", "Rossi")]
    assert find_duplicates("Anna", "Rossi", guests, [], ignore_guest_id=1) == []
    assert len(find_duplicates("Anna", "Rossi", guests, [])) == 1


def test_guest_meals_need_no_presence_and_may_be_past():
    wanted = {(date(2026, 7, 13), "lunch"), (date(2026, 7, 14), "dinner")}
    assert check_guest_meals(wanted, DAYS).ok


def test_guest_meals_outside_the_edition_are_refused():
    outside = (date(2026, 7, 20), "lunch")
    check = check_guest_meals({outside, (date(2026, 7, 13), "lunch")}, DAYS)
    assert not check.ok
    assert check.reason == "outside_edition"
    assert check.meals == (outside,)


def test_guest_meals_with_unknown_kind_are_refused():
    check = check_guest_meals({(date(2026, 7, 13), "brunch")}, DAYS)
    assert check.reason == "unknown_kind"


def test_empty_selection_is_fine():
    assert check_guest_meals(set(), DAYS).ok


def test_people_are_counted_once_and_participants_never_clash_with_guests():
    keys = merge_people([1, 2, 2], [1, 3])
    assert keys == {participant_key(1), participant_key(2), guest_key(1), guest_key(3)}
    assert len(keys) == 4


class TestMoney:
    def test_a_paying_guest_owes_the_sum_of_what_the_organisation_collects(self):
        assert guest_due_cents("paying", [800, 0, 1500]) == 2300

    def test_provider_items_are_zero_in_the_collectable_amounts_so_they_add_nothing(self):
        # `collectable` already turns a provider price into 0 before it gets here.
        assert guest_due_cents("paying", [0, 800]) == 800

    def test_a_non_paying_guest_owes_nothing(self):
        assert guest_due_cents("non_paying", [800, 1200]) == 0

    def test_no_items_no_due(self):
        assert guest_due_cents("paying", []) == 0

    def test_balance_and_credit(self):
        owed = guest_account(800, [Movement("payment", 600)])
        assert (owed.balance_cents, owed.to_collect_cents, owed.credit_cents) == (200, 200, 0)
        over = guest_account(800, [Movement("payment", 1000)])
        assert (over.balance_cents, over.to_collect_cents, over.credit_cents) == (-200, 0, 200)

    def test_voided_movements_do_not_count(self):
        account = guest_account(
            800, [Movement("payment", 800, voided=True), Movement("payment", 300)]
        )
        assert (account.paid_cents, account.balance_cents) == (300, 500)

    def test_refunds_reduce_what_the_organisation_keeps(self):
        account = guest_account(0, [Movement("payment", 800), Movement("refund", 300)])
        assert (account.net_cents, account.credit_cents) == (500, 500)

    def test_switching_to_non_paying_after_a_payment_makes_the_payment_a_credit(self):
        before = guest_account(guest_due_cents("paying", [800]), [Movement("payment", 800)])
        after = guest_account(guest_due_cents("non_paying", [800]), [Movement("payment", 800)])
        assert (before.credit_cents, after.credit_cents) == (0, 800)

    @pytest.mark.parametrize(
        ("kind", "amount", "expected"),
        [
            ("payment", 100, None),
            ("payment", 0, "invalid_amount"),
            ("payment", -5, "invalid_amount"),
            ("refund", 200, None),
            ("refund", 201, "refund_too_high"),
            ("refund", 0, "invalid_amount"),
        ],
    )
    def test_checks_on_a_new_movement(self, kind, amount, expected):
        account = guest_account(800, [Movement("payment", 1000)])  # credit of 200
        assert check_movement(kind, amount, account) == expected

    def test_a_refund_with_no_credit_is_refused(self):
        account = guest_account(800, [Movement("payment", 800)])
        assert check_movement("refund", 1, account) == "refund_too_high"

    def test_a_payment_cannot_be_voided_if_a_refund_relies_on_it(self):
        account = guest_account(0, [Movement("payment", 800), Movement("refund", 500)])
        assert not can_void("payment", 800, account)
        assert can_void("refund", 500, account)

    def test_a_payment_can_be_voided_if_enough_stays(self):
        account = guest_account(
            0, [Movement("payment", 800), Movement("payment", 700), Movement("refund", 500)]
        )
        assert can_void("payment", 700, account)
