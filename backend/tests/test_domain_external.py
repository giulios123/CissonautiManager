from datetime import date

import pytest

from app.domain.external import (
    check_guest_meals,
    find_duplicates,
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
