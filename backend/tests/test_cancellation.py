import pytest
from sqlalchemy import func, select

from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_REFUNDED,
    Booking,
    BookingSlot,
    Participant,
    Slot,
)
from tests.helpers import d, payload
from tests.test_auth import login
from tests.test_change_slots import available_seats, pay

MORNING = "morning"


@pytest.fixture
def ada(make_participant):
    return make_participant("ada@example.com")


@pytest.fixture
def member(client, outbox, ada):
    login(client, outbox)
    outbox.sent.clear()
    return client


def cancel(client):
    return client.post("/api/me/booking/cancel")


def test_cancelling_with_payments_requests_a_refund_and_frees_the_seats(
    member, db, ada, outbox, make_booking, slot_ids, clock
):
    slot = db.get(Slot, slot_ids[(d(13), MORNING)])
    booking = make_booking(ada, [slot], status=STATUS_CONFIRMED)
    pay(db, booking, 1100)
    assert available_seats(member)[slot.id] == 24
    response = cancel(member)
    assert response.status_code == 200
    assert response.json() == {"outcome": "requested"}
    db.refresh(booking)
    assert booking.status == STATUS_CANCEL_REQUESTED
    assert booking.cancel_requested_at == clock()
    assert available_seats(member)[slot.id] == 25
    assert len(outbox.sent) == 1 and outbox.sent[0].to == "ada@example.com"
    assert "rimborso" in outbox.sent[0].body
    view = member.get("/api/me").json()["bookings"][0]
    assert view["status"] == STATUS_CANCEL_REQUESTED
    assert view["editable"] is False and view["can_cancel"] is False


def test_cancelling_without_payments_removes_the_booking_and_keeps_the_person(
    member, db, ada, outbox, make_booking, slot_ids
):
    slot = db.get(Slot, slot_ids[(d(13), MORNING)])
    make_booking(ada, [slot])
    assert cancel(member).json() == {"outcome": "removed"}
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(Booking)) == 0
    assert db.scalar(select(func.count()).select_from(BookingSlot)) == 0
    assert db.scalar(select(Participant).where(Participant.email == "ada@example.com"))
    assert available_seats(member)[slot.id] == 25
    assert member.get("/api/me").json()["bookings"] == []
    assert len(outbox.sent) == 1
    assert "rimborso" not in outbox.sent[0].body


@pytest.mark.parametrize("status", [STATUS_EXPIRED, STATUS_CANCEL_REQUESTED, STATUS_REFUNDED])
def test_booking_in_a_closed_status_cannot_be_cancelled(
    member, db, ada, outbox, make_booking, slot_ids, status
):
    make_booking(ada, [db.get(Slot, slot_ids[(d(13), MORNING)])], status=status)
    assert cancel(member).status_code == 409
    assert outbox.sent == []


def test_cancelling_twice_is_refused_and_sends_one_email(
    member, db, ada, outbox, make_booking, slot_ids
):
    booking = make_booking(ada, [db.get(Slot, slot_ids[(d(13), MORNING)])])
    pay(db, booking, 500)
    assert cancel(member).status_code == 200
    assert cancel(member).status_code == 409
    assert len(outbox.sent) == 1


@pytest.mark.parametrize("paid", [0, 500])
def test_after_cancelling_the_person_can_sign_up_again(
    member, client, db, ada, make_booking, slot_ids, paid
):
    booking = make_booking(ada, [db.get(Slot, slot_ids[(d(13), MORNING)])])
    if paid:
        pay(db, booking, paid)
    assert cancel(member).status_code == 200
    response = client.post("/api/public/registrations", json=payload([slot_ids[(d(14), MORNING)]]))
    assert response.status_code == 201
    assert response.json()["result"] == "created"


def test_cancelling_requires_a_session(client, edition):
    assert cancel(client).status_code == 401


def test_cancelling_without_a_booking_is_404(member, edition):
    assert cancel(member).status_code == 404
