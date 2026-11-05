from datetime import date, timedelta

import pytest

from app.models import ROLE_ADMIN, Payment, Slot
from app.services.payments import paid_total
from tests.helpers import d
from tests.test_auth import login


@pytest.fixture
def booking(db, make_participant, make_booking, slot_ids):
    ada = make_participant("ada@example.com")
    return make_booking(ada, [db.get(Slot, slot_ids[(d(13), "morning")])], amount_due_cents=1100)


@pytest.fixture
def two_payments(db, booking, make_participant, clock):
    admin = make_participant("treasurer@example.com", role=ROLE_ADMIN)
    kept = Payment(
        booking_id=booking.id, amount_cents=400, channel="iban",
        paid_on=date(2026, 7, 2), recorded_by_id=admin.id,
    )  # fmt: skip
    mistaken = Payment(
        booking_id=booking.id, amount_cents=700, channel="revolut",
        paid_on=date(2026, 7, 2), recorded_by_id=admin.id, note="doppio",
        voided_at=clock() + timedelta(hours=1), voided_by_id=admin.id,
        void_reason="inserito due volte",
    )  # fmt: skip
    db.add_all([kept, mistaken])
    db.commit()
    db.refresh(booking)
    return kept, mistaken


def test_a_voided_payment_does_not_count_in_the_total(booking, two_payments):
    assert paid_total(booking) == 400


def test_participant_sees_only_the_payments_that_count(client, outbox, booking, two_payments):
    login(client, outbox)
    view = client.get("/api/me").json()["bookings"][0]
    assert (view["paid_cents"], view["balance_cents"]) == (400, 700)
    assert [p["amount_cents"] for p in view["payments"]] == [400]


def test_admin_sees_the_voided_payment_marked_with_its_reason(admin_client, booking, two_payments):
    data = admin_client.get(f"/api/admin/registrations/{booking.id}").json()["booking"]
    assert (data["paid_cents"], data["balance_cents"]) == (400, 700)
    by_amount = {p["amount_cents"]: p for p in data["payments"]}
    assert by_amount[400]["voided"] is False
    assert by_amount[700]["voided"] is True
    assert by_amount[700]["void_reason"] == "inserito due volte"
    assert by_amount[700]["id"] == two_payments[1].id


def test_admin_list_uses_the_same_total(admin_client, booking, two_payments):
    row = admin_client.get("/api/admin/registrations").json()[0]
    assert row["paid_cents"] == 400


def test_a_payment_that_only_matches_after_voiding_does_not_confirm(
    admin_client, booking, two_payments
):
    # 400 counted + a new 700 would cover 1100; the voided 700 must not have done it already
    data = admin_client.get(f"/api/admin/registrations/{booking.id}").json()
    assert data["booking"]["status"] == "in_attesa_pagamento"
