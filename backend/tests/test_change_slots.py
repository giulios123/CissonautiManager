from datetime import date, timedelta

import pytest

from app.models import (
    ROLE_ADMIN,
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    STATUS_REFUNDED,
    Payment,
    Slot,
)
from tests.helpers import d
from tests.test_auth import login

MORNING = "morning"
AFTERNOON = "afternoon"


@pytest.fixture
def ada(make_participant):
    return make_participant("ada@example.com")


@pytest.fixture
def member(client, outbox, ada):
    login(client, outbox)
    outbox.sent.clear()
    return client


def put(client, ids):
    return client.put("/api/me/booking/slots", json={"slot_ids": ids})


def available_seats(client) -> dict[int, int | None]:
    days = client.get("/api/public/edition").json()["days"]
    return {slot["id"]: slot["available"] for day in days for slot in day["slots"]}


def pay(db, booking, cents):
    admin = db.query(type(booking.participant)).filter_by(role=ROLE_ADMIN).first()
    if admin is None:
        from app.models import Participant

        admin = Participant(
            first_name="Boss",
            last_name="Admin",
            email="boss-pay@example.com",
            personal_code="CSC-PAYY",
            role=ROLE_ADMIN,
        )
        db.add(admin)
        db.commit()
    db.add(
        Payment(
            booking_id=booking.id,
            amount_cents=cents,
            channel="iban",
            paid_on=date(2026, 7, 2),
            recorded_by_id=admin.id,
        )
    )
    db.commit()
    db.refresh(booking)


def test_add_a_slot_recomputes_the_amount_and_keeps_the_deadline(
    member, db, ada, make_booking, slot_ids
):
    booking = make_booking(ada, [db.get(Slot, slot_ids[(d(13), MORNING)])])
    deadline = booking.hold_expires_at
    response = put(member, [slot_ids[(d(13), MORNING)], slot_ids[(d(14), MORNING)]])
    assert response.status_code == 200, response.text
    view = response.json()
    assert view["amount_due_cents"] == 1200
    assert view["status"] == STATUS_PENDING
    assert len(view["slots"]) == 2
    db.refresh(booking)
    assert booking.hold_expires_at == deadline


def test_two_slots_on_the_same_day_count_the_day_once(member, db, ada, make_booking, slot_ids):
    make_booking(ada, [db.get(Slot, slot_ids[(d(13), MORNING)])])
    response = put(member, [slot_ids[(d(13), MORNING)], slot_ids[(d(13), AFTERNOON)]])
    assert response.json()["amount_due_cents"] == 1100


def test_removing_a_slot_lowers_the_amount_and_frees_the_seat(
    member, db, ada, make_booking, slot_ids
):
    make_booking(
        ada,
        [db.get(Slot, slot_ids[(d(13), MORNING)]), db.get(Slot, slot_ids[(d(14), MORNING)])],
        amount_due_cents=1200,
    )
    taken = {
        s["id"]: s for day in member.get("/api/public/edition").json()["days"] for s in day["slots"]
    }
    assert taken[slot_ids[(d(14), MORNING)]]["available"] == 24
    response = put(member, [slot_ids[(d(13), MORNING)]])
    assert response.json()["amount_due_cents"] == 1100
    free = {
        s["id"]: s for day in member.get("/api/public/edition").json()["days"] for s in day["slots"]
    }
    assert free[slot_ids[(d(14), MORNING)]]["available"] == 25


def test_adding_a_full_slot_is_refused_and_nothing_changes(
    member, db, ada, make_participant, make_booking, slot_ids
):
    full = db.get(Slot, slot_ids[(d(14), MORNING)])
    full.capacity = 1
    db.commit()
    make_booking(make_participant("bob@example.com"), [full])
    booking = make_booking(ada, [db.get(Slot, slot_ids[(d(13), MORNING)])])
    response = put(member, [slot_ids[(d(13), MORNING)], full.id])
    assert response.status_code == 409
    assert response.json()["full_slot_ids"] == [full.id]
    db.refresh(booking)
    assert [s.id for s in booking.slots] == [slot_ids[(d(13), MORNING)]]
    assert booking.amount_due_cents == 1100


def test_keeping_my_own_slot_in_a_full_slot_is_fine(member, db, ada, make_booking, slot_ids):
    mine = db.get(Slot, slot_ids[(d(13), MORNING)])
    mine.capacity = 1
    db.commit()
    make_booking(ada, [mine])
    response = put(member, [mine.id, slot_ids[(d(14), MORNING)]])
    assert response.status_code == 200


def test_the_evening_has_no_limit(member, db, ada, make_booking, slot_ids):
    make_booking(ada, [db.get(Slot, slot_ids[(d(13), MORNING)])])
    response = put(member, [slot_ids[(d(13), MORNING)], slot_ids[(d(13), "evening")]])
    assert response.status_code == 200


def test_an_empty_selection_is_refused(member, db, ada, make_booking, slot_ids):
    make_booking(ada, [db.get(Slot, slot_ids[(d(13), MORNING)])])
    response = put(member, [])
    assert response.status_code == 422
    assert "disdetta" in response.json()["detail"]


def test_unknown_slot_is_refused(member, db, ada, make_booking, slot_ids):
    make_booking(ada, [db.get(Slot, slot_ids[(d(13), MORNING)])])
    assert put(member, [slot_ids[(d(13), MORNING)], 999999]).status_code == 422


def test_confirmed_booking_stays_confirmed_with_a_balance_to_pay(
    member, db, ada, make_booking, slot_ids
):
    booking = make_booking(ada, [db.get(Slot, slot_ids[(d(13), MORNING)])], status=STATUS_CONFIRMED)
    pay(db, booking, 1100)
    view = put(member, [slot_ids[(d(13), MORNING)], slot_ids[(d(14), MORNING)]]).json()
    assert view["status"] == STATUS_CONFIRMED
    assert (view["amount_due_cents"], view["paid_cents"], view["balance_cents"]) == (
        1200,
        1100,
        100,
    )


def test_confirmed_booking_stays_confirmed_with_a_credit(member, db, ada, make_booking, slot_ids):
    booking = make_booking(
        ada,
        [db.get(Slot, slot_ids[(d(13), MORNING)]), db.get(Slot, slot_ids[(d(14), MORNING)])],
        status=STATUS_CONFIRMED,
        amount_due_cents=1200,
    )
    pay(db, booking, 1200)
    view = put(member, [slot_ids[(d(13), MORNING)]]).json()
    assert view["status"] == STATUS_CONFIRMED
    assert view["balance_cents"] == -100


def test_pending_booking_already_covered_by_the_new_amount_is_confirmed(
    member, db, ada, outbox, make_booking, slot_ids
):
    booking = make_booking(
        ada,
        [db.get(Slot, slot_ids[(d(13), MORNING)]), db.get(Slot, slot_ids[(d(14), MORNING)])],
        amount_due_cents=1200,
    )
    pay(db, booking, 1100)
    view = put(member, [slot_ids[(d(13), MORNING)]]).json()
    assert view["status"] == STATUS_CONFIRMED
    assert [m.subject for m in outbox.sent] == [
        "Pagamento ricevuto: sei dentro a Cissonauti Summer Camp 2026!"
    ]


@pytest.mark.parametrize("status", [STATUS_EXPIRED, STATUS_CANCEL_REQUESTED, STATUS_REFUNDED])
def test_booking_in_a_closed_status_cannot_be_edited(
    member, db, ada, make_booking, slot_ids, status
):
    make_booking(ada, [db.get(Slot, slot_ids[(d(13), MORNING)])], status=status)
    response = put(member, [slot_ids[(d(14), MORNING)]])
    assert response.status_code == 409


def test_booking_past_its_deadline_cannot_be_edited(member, db, ada, make_booking, slot_ids, clock):
    make_booking(
        ada,
        [db.get(Slot, slot_ids[(d(13), MORNING)])],
        hold_expires_at=clock() + timedelta(hours=1),
    )
    clock.advance(hours=2)
    assert put(member, [slot_ids[(d(14), MORNING)]]).status_code == 409


def test_past_days_cannot_be_added_or_removed_by_the_participant(
    member, db, ada, make_booking, slot_ids, clock
):
    clock.advance(days=13)  # 14 July, 12:00 in Rome: the 13th is over, today is still open
    make_booking(ada, [db.get(Slot, slot_ids[(d(13), MORNING)])])
    past_morning = slot_ids[(d(13), MORNING)]
    # removing a slot of a day that is over
    assert put(member, [slot_ids[(d(15), MORNING)]]).status_code == 422
    # adding another slot to a day that is over
    assert put(member, [past_morning, slot_ids[(d(13), AFTERNOON)]]).status_code == 422
    # keeping the past slot and adding a future one is fine, and so is today
    assert put(member, [past_morning, slot_ids[(d(15), MORNING)]]).status_code == 200
    assert put(member, [past_morning, slot_ids[(d(14), MORNING)]]).status_code == 200


def test_changing_slots_requires_a_session(client, edition):
    assert client.put("/api/me/booking/slots", json={"slot_ids": [1]}).status_code == 401


def test_changing_slots_without_a_booking_is_404(member, edition):
    assert put(member, [1]).status_code == 404


def test_me_exposes_what_the_page_can_do(member, db, ada, make_booking, slot_ids):
    make_booking(ada, [db.get(Slot, slot_ids[(d(13), MORNING)])])
    view = member.get("/api/me").json()["bookings"][0]
    assert view["editable"] is True and view["can_cancel"] is True
    assert view["slots"][0]["id"] == slot_ids[(d(13), MORNING)]


def test_public_edition_marks_past_days(client, edition, clock):
    clock.advance(days=14)  # 15 July
    days = client.get("/api/public/edition").json()["days"]
    assert [day["past"] for day in days] == [True, True, False, False, False]
