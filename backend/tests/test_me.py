from datetime import date

from sqlalchemy import select

from app.models import STATUS_CONFIRMED, Payment, Slot
from tests.test_auth import login


def slot_on(db, day, period="morning"):
    return db.scalar(select(Slot).where(Slot.date == date(2026, 7, day), Slot.period == period))


def add_payment(db, booking, admin, cents, note=None):
    db.add(
        Payment(
            booking_id=booking.id,
            amount_cents=cents,
            channel="iban",
            paid_on=date(2026, 7, 2),
            note=note,
            recorded_by_id=admin.id,
        )
    )
    db.commit()


def test_me_without_booking_has_empty_list(client, outbox, make_participant, edition):
    make_participant("ada@example.com")
    login(client, outbox)
    data = client.get("/api/me").json()
    assert data["bookings"] == []


def test_me_shows_balance_deadline_and_slots(
    client, db, outbox, make_participant, make_booking, clock, admin_client
):
    ada = make_participant("ada@example.com")
    booking = make_booking(
        ada, [slot_on(db, 13), slot_on(db, 14, "afternoon")], amount_due_cents=1200
    )
    login(client, outbox)
    data = client.get("/api/me").json()
    view = data["bookings"][0]
    assert view["id"] == booking.id
    assert view["status"] == "in_attesa_pagamento"
    assert (view["amount_due_cents"], view["paid_cents"], view["balance_cents"]) == (1200, 0, 1200)
    assert view["hold_expires_at"].startswith("2026-07-04T10:00:00")
    assert [s["label"] for s in view["slots"]] == [
        "lun 13/07 mattina (09:00-13:00)",
        "mar 14/07 pomeriggio (14:00-18:00)",
    ]


def test_balance_is_due_minus_payments(
    client, db, outbox, make_participant, make_booking, admin_client
):
    from app.models import Participant

    ada = make_participant("ada@example.com")
    booking = make_booking(ada, [slot_on(db, 13)], amount_due_cents=1100)
    admin = db.scalar(select(Participant).where(Participant.email == "boss@example.com"))
    add_payment(db, booking, admin, 400, note="internal remark")
    add_payment(db, booking, admin, 300)
    login(client, outbox)
    view = client.get("/api/me").json()["bookings"][0]
    assert (view["paid_cents"], view["balance_cents"]) == (700, 400)
    assert len(view["payments"]) == 2


def test_internal_notes_are_not_shown_to_the_participant(
    client, db, outbox, make_participant, make_booking, admin_client
):
    from app.models import Participant

    ada = make_participant("ada@example.com")
    booking = make_booking(ada, [slot_on(db, 13)])
    admin = db.scalar(select(Participant).where(Participant.email == "boss@example.com"))
    add_payment(db, booking, admin, 400, note="internal remark")
    login(client, outbox)
    assert "internal remark" not in client.get("/api/me").text


def test_overpaid_balance_is_negative(
    client, db, outbox, make_participant, make_booking, admin_client
):
    from app.models import Participant

    ada = make_participant("ada@example.com")
    booking = make_booking(ada, [slot_on(db, 13)], status=STATUS_CONFIRMED, amount_due_cents=1100)
    admin = db.scalar(select(Participant).where(Participant.email == "boss@example.com"))
    add_payment(db, booking, admin, 1500)
    login(client, outbox)
    assert client.get("/api/me").json()["bookings"][0]["balance_cents"] == -400


def test_overdue_booking_is_shown_as_expired(
    client, db, outbox, make_participant, make_booking, clock
):
    ada = make_participant("ada@example.com")
    make_booking(ada, [slot_on(db, 13)])
    login(client, outbox)
    clock.advance(days=3)
    assert client.get("/api/me").json()["bookings"][0]["status"] == "scaduta"


def test_me_only_shows_own_bookings(client, db, outbox, make_participant, make_booking):
    ada = make_participant("ada@example.com")
    grace = make_participant("grace@example.com")
    make_booking(ada, [slot_on(db, 13)])
    make_booking(grace, [slot_on(db, 14)])
    login(client, outbox, "grace@example.com")
    bookings = client.get("/api/me").json()["bookings"]
    assert len(bookings) == 1
    assert bookings[0]["slots"][0]["date"] == "2026-07-14"


def test_me_lists_enabled_payment_channels(client, outbox, make_participant, edition, admin_client):
    admin_client.put(
        "/api/admin/payment-channels",
        json=[{"code": "paypal", "instructions": "paypal.me/cisonauti", "enabled": True}],
    )
    make_participant("ada@example.com")
    login(client, outbox)
    channels = client.get("/api/me").json()["payment_channels"]
    assert [c["code"] for c in channels] == ["paypal"]
