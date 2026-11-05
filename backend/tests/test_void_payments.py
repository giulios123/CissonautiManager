from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    AuditLog,
    Booking,
    Payment,
    Slot,
)
from tests.helpers import d
from tests.test_auth import login
from tests.test_change_slots import available_seats, pay


@pytest.fixture
def booking(db, edition, make_participant, make_booking, slot_ids, admin_client):
    """Pending booking of 11 euro for Ada."""
    ada = make_participant("ada@example.com", first_name="Ada", last_name="Lovelace")
    return make_booking(ada, [db.get(Slot, slot_ids[(d(13), "morning")])])


def void(client, booking, payment, reason="inserito per errore"):
    return client.post(
        f"/api/admin/registrations/{booking.id}/payments/{payment.id}/void", json={"reason": reason}
    )


def add_payment(db, booking, cents):
    pay(db, booking, cents)
    return booking.payments[-1]


def test_a_voided_payment_stays_visible_with_its_reason_and_stops_counting(
    admin_client, booking, db, clock
):
    wrong = add_payment(db, booking, 400)
    right = add_payment(db, booking, 300)
    data = void(admin_client, booking, wrong, "doppio").json()["booking"]
    assert (data["paid_cents"], data["balance_cents"]) == (300, 800)
    by_id = {p["id"]: p for p in data["payments"]}
    assert by_id[wrong.id]["voided"] is True and by_id[wrong.id]["void_reason"] == "doppio"
    assert by_id[right.id]["voided"] is False
    db.expire_all()
    stored = db.get(Payment, wrong.id)
    assert stored.voided_at == clock() and stored.voided_by_id is not None


def test_a_reason_is_required(admin_client, booking, db):
    payment = add_payment(db, booking, 400)
    assert void(admin_client, booking, payment, reason="").status_code == 422
    assert void(admin_client, booking, payment, reason="   ").status_code == 422
    assert (
        admin_client.post(
            f"/api/admin/registrations/{booking.id}/payments/{payment.id}/void", json={}
        ).status_code
        == 422
    )
    db.expire_all()
    assert db.get(Payment, payment.id).voided_at is None


def test_a_confirmed_booking_no_longer_covered_goes_back_to_pending_with_a_new_hold(
    admin_client, booking, db, clock, client, slot_ids, outbox
):
    payment = add_payment(db, booking, 1100)
    booking.status = STATUS_CONFIRMED
    booking.reminder_mid_sent_at = clock()
    db.commit()
    clock.advance(days=2)
    data = void(admin_client, booking, payment).json()
    assert data["booking"]["status"] == STATUS_PENDING
    db.expire_all()
    refreshed = db.get(Booking, booking.id)
    assert refreshed.hold_started_at == clock()
    assert refreshed.hold_expires_at == clock() + timedelta(days=3)
    assert refreshed.reminder_mid_sent_at is None
    assert available_seats(client)[slot_ids[(d(13), "morning")]] == 24  # still holds its seat
    assert "Confermata → In attesa di pagamento" in data["history"][0]["detail"]
    assert outbox.sent == []


def test_a_confirmed_booking_that_stays_covered_stays_confirmed(admin_client, booking, db):
    extra = add_payment(db, booking, 500)
    add_payment(db, booking, 1100)
    booking.status = STATUS_CONFIRMED
    db.commit()
    data = void(admin_client, booking, extra).json()
    assert data["booking"]["status"] == STATUS_CONFIRMED
    assert "Stato:" not in data["history"][0]["detail"]


def test_a_pending_booking_keeps_its_deadline(admin_client, booking, db):
    payment = add_payment(db, booking, 400)
    deadline = booking.hold_expires_at
    assert void(admin_client, booking, payment).json()["booking"]["status"] == STATUS_PENDING
    db.expire_all()
    assert db.get(Booking, booking.id).hold_expires_at == deadline


@pytest.mark.parametrize("status", [STATUS_EXPIRED, STATUS_CANCEL_REQUESTED])
def test_other_statuses_are_left_alone(admin_client, booking, db, status):
    payment = add_payment(db, booking, 400)
    booking.status = status
    db.commit()
    assert void(admin_client, booking, payment).json()["booking"]["status"] == status


def test_voiding_twice_is_refused(admin_client, booking, db):
    payment = add_payment(db, booking, 400)
    assert void(admin_client, booking, payment).status_code == 200
    assert void(admin_client, booking, payment).status_code == 409


def test_a_payment_of_another_booking_or_an_unknown_one_is_404(
    admin_client, booking, db, make_participant, make_booking, slot_ids
):
    other = make_booking(
        make_participant("bob@example.com"), [db.get(Slot, slot_ids[(d(14), "morning")])]
    )
    foreign = add_payment(db, other, 400)
    assert void(admin_client, booking, foreign).status_code == 404
    assert (
        admin_client.post(
            f"/api/admin/registrations/{booking.id}/payments/99999/void", json={"reason": "x"}
        ).status_code
        == 404
    )
    assert (
        admin_client.post(
            "/api/admin/registrations/999/payments/1/void", json={"reason": "x"}
        ).status_code
        == 404
    )
    db.expire_all()
    assert db.get(Payment, foreign.id).voided_at is None


def test_the_history_records_amount_date_channel_reason_and_author(admin_client, booking, db):
    payment = add_payment(db, booking, 400)
    data = void(admin_client, booking, payment, "inserito per errore").json()
    entry = data["history"][0]
    assert entry["action"] == "payment_voided"
    assert "4,00" in entry["detail"] and "02/07/2026" in entry["detail"]
    assert "Bonifico (IBAN)" in entry["detail"] and "inserito per errore" in entry["detail"]
    assert db.scalar(select(AuditLog)).booking_id == booking.id


def test_after_voiding_a_correct_payment_confirms_again(admin_client, booking, db):
    wrong = add_payment(db, booking, 1100)
    booking.status = STATUS_CONFIRMED
    db.commit()
    void(admin_client, booking, wrong)
    response = admin_client.post(
        f"/api/admin/registrations/{booking.id}/payments",
        json={"amount_cents": 1100, "channel": "revolut"},
    )
    assert response.json()["booking"]["status"] == STATUS_CONFIRMED
    assert response.json()["booking"]["paid_cents"] == 1100


def test_the_participant_page_no_longer_shows_it(client, outbox, admin_client, booking, db):
    payment = add_payment(db, booking, 400)
    void(admin_client, booking, payment)
    login(client, outbox)
    view = client.get("/api/me").json()["bookings"][0]
    assert (view["paid_cents"], view["payments"]) == (0, [])


def test_admins_only(client, outbox, make_participant, booking, db):
    payment = add_payment(db, booking, 400)
    assert void(client, booking, payment).status_code == 401
    make_participant("someone@example.com")
    login(client, outbox, email="someone@example.com")
    assert void(client, booking, payment).status_code == 403
