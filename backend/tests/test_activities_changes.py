"""Activities follow the booking: slot changes, cancellations and reactivations."""

from datetime import timedelta

from sqlalchemy import select

from app.models import STATUS_EXPIRED, Activity, AuditLog, BookingActivity, Slot
from tests.helpers import d
from tests.test_auth import login


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


def activity(db, edition, title, day, period, price=0, capacity=None) -> Activity:
    a = Activity(
        edition_id=edition.id,
        title=title,
        date=d(day),
        period=period,
        price_cents=price,
        capacity=capacity,
    )
    db.add(a)
    db.commit()
    return a


def holding(db, booking, *activities):
    booking.activities = list(activities)
    db.commit()
    return booking


def test_dropping_the_slot_drops_the_activity_and_its_price(
    client, outbox, db, edition, make_participant, make_booking
):
    hike = activity(db, edition, "Escursione", 14, "morning", 1500)
    booking = make_booking(
        make_participant("ada@example.com"), [slot(db, 13), slot(db, 14)], amount_due_cents=2700
    )
    holding(db, booking, hike)
    login(client, outbox)
    body = client.put("/api/me/booking/slots", json={"slot_ids": [slot(db, 13).id]}).json()
    assert body["dropped_activities"] == ["Escursione (mar 14/07 mattina)"]
    assert body["amount_due_cents"] == 1100
    db.refresh(booking)
    assert booking.activities == []


def test_evening_activity_stays_with_the_whole_day(
    client, outbox, db, edition, make_participant, make_booking
):
    quiz = activity(db, edition, "Quiz", 13, "evening")
    monday = [slot(db, 13), slot(db, 13, "afternoon"), slot(db, 13, "evening")]
    booking = make_booking(make_participant("ada@example.com"), monday)
    holding(db, booking, quiz)
    login(client, outbox)
    ids = [s.id for s in monday[:2]]
    body = client.put("/api/me/booking/slots", json={"slot_ids": ids}).json()
    assert body["dropped_activities"] == []


def test_admin_slot_change_records_the_dropped_activities(
    admin_client, db, edition, make_participant, make_booking
):
    hike = activity(db, edition, "Escursione", 14, "morning")
    booking = make_booking(make_participant("ada@example.com"), [slot(db, 13), slot(db, 14)])
    holding(db, booking, hike)
    response = admin_client.put(
        f"/api/admin/registrations/{booking.id}/slots", json={"slot_ids": [slot(db, 13).id]}
    )
    assert "Tolte anche le attività senza più presenza: Escursione" in response.json()["warning"]
    log = db.scalar(select(AuditLog).where(AuditLog.action == "slots_changed"))
    assert "Tolte anche le attività: Escursione (mar 14/07 mattina)." in log.detail


def test_a_removed_booking_frees_its_activity_rows(
    client, outbox, db, edition, make_participant, make_booking
):
    hike = activity(db, edition, "Escursione", 13, "morning")
    booking = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    holding(db, booking, hike)
    login(client, outbox)
    assert client.post("/api/me/booking/cancel").json()["outcome"] == "removed"
    assert db.scalar(select(BookingActivity)) is None


def _expired_with_full_activity(db, edition, make_participant, make_booking, clock):
    hike = activity(db, edition, "Escursione", 13, "morning", 1500, 1)
    expired = make_booking(
        make_participant("ada@example.com"),
        [slot(db, 13)],
        status=STATUS_EXPIRED,
        hold_expires_at=clock() - timedelta(hours=1),
        amount_due_cents=2600,
    )
    holding(db, expired, hike)
    other = make_booking(make_participant("bob@example.com", first_name="Bob"), [slot(db, 13)])
    holding(db, other, hike)
    return expired


def test_admin_reactivation_drops_full_activities_with_a_warning(
    admin_client, db, edition, make_participant, make_booking, clock
):
    expired = _expired_with_full_activity(db, edition, make_participant, make_booking, clock)
    response = admin_client.post(f"/api/admin/registrations/{expired.id}/reactivate")
    assert response.status_code == 200
    body = response.json()
    assert body["booking"]["status"] == "in_attesa_pagamento"
    assert body["booking"]["activities"] == []
    assert body["booking"]["amount_due_cents"] == 1100
    assert "senza queste attività" in body["warning"]
    log = db.scalar(select(AuditLog).where(AuditLog.action == "reactivated"))
    assert "Escursione (lun 13/07 mattina)" in log.detail


def test_reactivation_by_payment_drops_full_activities_too(
    admin_client, db, edition, make_participant, make_booking, clock
):
    expired = _expired_with_full_activity(db, edition, make_participant, make_booking, clock)
    response = admin_client.post(
        f"/api/admin/registrations/{expired.id}/payments",
        json={"amount_cents": 1100, "channel": "iban"},
    )
    body = response.json()
    assert body["booking"]["status"] == "confermata"
    assert "senza queste attività" in body["warning"]


def test_reactivation_keeps_activities_with_seats(
    admin_client, db, edition, make_participant, make_booking, clock
):
    quiz = activity(db, edition, "Quiz", 13, "morning", 0, 5)
    expired = make_booking(
        make_participant("ada@example.com"),
        [slot(db, 13)],
        status=STATUS_EXPIRED,
        hold_expires_at=clock() - timedelta(hours=1),
    )
    holding(db, expired, quiz)
    body = admin_client.post(f"/api/admin/registrations/{expired.id}/reactivate").json()
    assert [a["title"] for a in body["booking"]["activities"]] == ["Quiz"]
    assert body["warning"] is None
