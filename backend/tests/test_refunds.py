from datetime import date

import pytest
from sqlalchemy import select

from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_PENDING,
    STATUS_REFUNDED,
    AuditLog,
    Booking,
    Participant,
    Slot,
)
from tests.helpers import d
from tests.test_auth import login
from tests.test_change_slots import available_seats, pay


@pytest.fixture
def cancelled(db, edition, make_participant, make_booking, slot_ids, admin_client):
    """Ada cancelled a booking she had paid in full (11 euro)."""
    ada = make_participant("ada@example.com", first_name="Ada", last_name="Lovelace")
    booking = make_booking(
        ada, [db.get(Slot, slot_ids[(d(13), "morning")])], status=STATUS_CANCEL_REQUESTED
    )
    pay(db, booking, 1100)
    return booking


def refund(client, booking, **body):
    return client.post(f"/api/admin/registrations/{booking.id}/refund", json=body)


def test_a_refund_closes_the_cancellation_and_records_amount_date_and_note(
    admin_client, cancelled, db
):
    response = refund(
        admin_client, cancelled, amount_cents=1100, refunded_on="2026-07-03", note="Revolut"
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["booking"]["status"] == STATUS_REFUNDED
    assert data["refund"] == {"amount_cents": 1100, "refunded_on": "2026-07-03", "note": "Revolut"}
    db.expire_all()
    booking = db.get(Booking, cancelled.id)
    assert (booking.status, booking.refund_cents, booking.refunded_on) == (
        STATUS_REFUNDED,
        1100,
        date(2026, 7, 3),
    )
    assert booking.refunded_by_id is not None


def test_the_date_defaults_to_today_in_rome(admin_client, cancelled, clock):
    clock.advance(hours=14)  # 00:00 UTC on 2 July is 02:00 in Rome, still the 2nd
    data = refund(admin_client, cancelled, amount_cents=1100).json()
    assert data["refund"]["refunded_on"] == "2026-07-02"


def test_no_email_is_sent(admin_client, cancelled, outbox):
    refund(admin_client, cancelled, amount_cents=1100)
    assert outbox.sent == []


def test_a_partial_refund_is_allowed(admin_client, cancelled):
    data = refund(admin_client, cancelled, amount_cents=600).json()
    assert data["booking"]["status"] == STATUS_REFUNDED
    assert data["refund"]["amount_cents"] == 600


def test_a_cancellation_with_nothing_paid_is_closed_with_a_zero_refund(
    admin_client, db, edition, make_participant, make_booking, slot_ids
):
    bob = make_participant("bob@example.com")
    booking = make_booking(
        bob, [db.get(Slot, slot_ids[(d(13), "morning")])], status=STATUS_CANCEL_REQUESTED
    )
    data = refund(admin_client, booking, amount_cents=0).json()
    assert data["booking"]["status"] == STATUS_REFUNDED
    assert data["refund"]["amount_cents"] == 0


def test_a_refund_above_what_was_paid_is_refused_and_nothing_changes(admin_client, cancelled, db):
    response = refund(admin_client, cancelled, amount_cents=1101)
    assert response.status_code == 422
    assert "11,00" in response.json()["detail"]
    db.expire_all()
    assert db.get(Booking, cancelled.id).status == STATUS_CANCEL_REQUESTED


def test_payments_voided_by_mistake_do_not_raise_the_limit(admin_client, cancelled, db):
    mistaken = cancelled.payments[0]
    mistaken.voided_at = mistaken.created_at
    mistaken.voided_by_id = mistaken.recorded_by_id
    db.commit()
    assert refund(admin_client, cancelled, amount_cents=100).status_code == 422
    assert refund(admin_client, cancelled, amount_cents=0).status_code == 200


def test_a_negative_amount_is_refused(admin_client, cancelled):
    assert refund(admin_client, cancelled, amount_cents=-1).status_code == 422


@pytest.mark.parametrize("status", [STATUS_PENDING, STATUS_CONFIRMED, STATUS_REFUNDED])
def test_only_a_requested_cancellation_can_be_refunded(admin_client, cancelled, db, status):
    cancelled.status = status
    db.commit()
    response = refund(admin_client, cancelled, amount_cents=1100)
    assert response.status_code == 409
    db.expire_all()
    assert db.get(Booking, cancelled.id).refund_cents is None


def test_refunding_twice_is_refused(admin_client, cancelled):
    assert refund(admin_client, cancelled, amount_cents=1100).status_code == 200
    assert refund(admin_client, cancelled, amount_cents=1100).status_code == 409


def test_unknown_booking_is_404(admin_client):
    assert (
        admin_client.post(
            "/api/admin/registrations/999/refund", json={"amount_cents": 0}
        ).status_code
        == 404
    )


def test_the_refund_is_in_the_history_with_who_did_it(admin_client, cancelled, db):
    boss = db.scalar(select(Participant).where(Participant.email == "boss@example.com"))
    boss.first_name, boss.last_name = "Gina", "Organizer"
    db.commit()
    refund(admin_client, cancelled, amount_cents=1100, refunded_on="2026-07-03", note="Revolut")
    detail = admin_client.get(f"/api/admin/registrations/{cancelled.id}").json()
    assert len(detail["history"]) == 1
    entry = detail["history"][0]
    assert entry["action"] == "refund"
    assert entry["actor"] == "Gina Organizer"
    assert (
        "11,00" in entry["detail"]
        and "03/07/2026" in entry["detail"]
        and "Revolut" in entry["detail"]
    )
    log = db.scalar(select(AuditLog))
    assert log.booking_id == cancelled.id


def test_the_case_leaves_the_payments_to_review(admin_client, cancelled):
    def listed():
        return [
            r["booking_id"] for r in admin_client.get("/api/admin/views/payments-review").json()
        ]

    assert cancelled.id in listed()
    refund(admin_client, cancelled, amount_cents=1100)
    assert cancelled.id not in listed()


def test_the_seats_stay_free(admin_client, cancelled, client, slot_ids):
    refund(admin_client, cancelled, amount_cents=1100)
    assert available_seats(client)[slot_ids[(d(13), "morning")]] == 25


def test_only_admins_can_refund(client, outbox, make_participant, cancelled):
    assert refund(client, cancelled, amount_cents=0).status_code == 401
    make_participant("someone@example.com")
    login(client, outbox, email="someone@example.com")
    assert refund(client, cancelled, amount_cents=0).status_code == 403
