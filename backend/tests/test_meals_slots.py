"""Changing slots drops the meals the person no longer has a right to."""

from sqlalchemy import select

from app.models import AuditLog, BookingMeal, Slot
from tests.helpers import d
from tests.test_auth import login


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


def with_meals(db, booking, *meals):
    booking.meals = [BookingMeal(date=d(day), kind=kind) for day, kind in meals]
    db.commit()
    return booking


def test_dropping_the_morning_drops_the_lunch_and_lowers_the_amount(
    client, db, outbox, make_participant, make_booking
):
    ada = make_participant("ada@example.com")
    booking = make_booking(ada, [slot(db, 13), slot(db, 14)], amount_due_cents=1200 + 800)
    with_meals(db, booking, (13, "lunch"))
    login(client, outbox)
    response = client.put("/api/me/booking/slots", json={"slot_ids": [slot(db, 14).id]})
    assert response.status_code == 200
    body = response.json()
    assert body["dropped_meals"] == ["pranzo di lun 13/07"]
    assert body["amount_due_cents"] == 1100
    db.refresh(booking)
    assert booking.meals == []


def test_the_dinner_stays_with_the_whole_day(client, db, outbox, make_participant, make_booking):
    ada = make_participant("ada@example.com")
    monday = [slot(db, 13), slot(db, 13, "afternoon"), slot(db, 13, "evening")]
    booking = make_booking(ada, monday)
    with_meals(db, booking, (13, "lunch"), (13, "dinner"))
    login(client, outbox)
    ids = [s.id for s in monday[:2]]
    body = client.put("/api/me/booking/slots", json={"slot_ids": ids}).json()
    assert body["dropped_meals"] == []
    assert body["amount_due_cents"] == 1100 + 800 + 1200


def test_new_amounts_include_the_meals(client, db, outbox, make_participant, make_booking):
    ada = make_participant("ada@example.com")
    booking = make_booking(ada, [slot(db, 13), slot(db, 13, "evening")])
    with_meals(db, booking, (13, "dinner"))
    login(client, outbox)
    ids = [slot(db, 13).id, slot(db, 13, "evening").id, slot(db, 14).id]
    body = client.put("/api/me/booking/slots", json={"slot_ids": ids}).json()
    assert body["amount_due_cents"] == 1200 + 1200


def test_admin_change_records_the_dropped_meals(admin_client, db, make_participant, make_booking):
    ada = make_participant("ada@example.com")
    booking = make_booking(ada, [slot(db, 13, "evening"), slot(db, 14)])
    with_meals(db, booking, (13, "dinner"))
    response = admin_client.put(
        f"/api/admin/registrations/{booking.id}/slots", json={"slot_ids": [slot(db, 14).id]}
    )
    assert response.status_code == 200
    assert "cena di lun 13/07" in response.json()["warning"]
    log = db.scalar(select(AuditLog).where(AuditLog.action == "slots_changed"))
    assert "Tolti anche i pasti: cena di lun 13/07." in log.detail


def test_registration_amount_is_unchanged_without_meals(client, edition, slot_ids):
    from tests.helpers import payload

    response = client.post(
        "/api/public/registrations", json=payload([slot_ids[(d(13), "morning")]])
    )
    assert response.json()["booking"]["amount_due_cents"] == 1100
