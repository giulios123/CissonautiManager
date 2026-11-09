from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.dialects import mssql

from app.domain.collection import collectable
from app.models import Activity, AuditLog, BookingMeal, Participant, Slot
from app.services.amounts import recompute_amount
from app.services.seats import lock_edition
from tests.helpers import d, payload
from tests.test_auth import login
from tests.test_change_slots import pay

HIKE = dict(
    title="Hike",
    title_it="Escursione",
    title_en="Hike",
    description_it="Escursione guidata.",
    description_en="Guided hike.",
    date="2026-07-13",
    period="morning",
    start_time="09:30",
    end_time="12:00",
    price_cents=1500,
)
DIRECT = dict(
    payment_mode="provider",
    price_cents=2300,
    payment_instructions="Pay the restaurant by card on arrival",
)


def slot(db, period="morning"):
    return db.scalar(select(Slot).where(Slot.date == d(13), Slot.period == period))


@pytest.mark.parametrize("value", [None, "", "   "])
def test_phone_is_required(client, slot_ids, value):
    body = payload([slot_ids[(d(13), "morning")]], phone=value)
    assert client.post("/api/public/registrations", json=body).status_code == 422
    del body["phone"]
    assert client.post("/api/public/registrations", json=body).status_code == 422


def test_phone_is_required_for_waitlist_only(client, slot_ids):
    body = payload([], waitlist_slot_ids=[slot_ids[(d(13), "morning")]])
    del body["phone"]
    assert client.post("/api/public/registrations", json=body).status_code == 422


@pytest.mark.parametrize("mode,expected", [("organizer", 1500), ("provider", 0)])
def test_collectable(mode, expected):
    assert collectable(1500, mode) == expected


def test_activity_times_are_stored_in_utc(admin_client, edition, db):
    response = admin_client.post("/api/admin/activities", json=HIKE)
    assert response.status_code == 201, response.text
    result = response.json()
    assert (result["start_time"], result["end_time"], result["time_label"]) == (
        "09:30",
        "12:00",
        "09:30-12:00",
    )
    activity = db.get(Activity, result["id"])
    assert activity.starts_at == datetime(2026, 7, 13, 7, 30, tzinfo=UTC)


@pytest.mark.parametrize(
    "changes",
    [
        dict(start_time=None),
        dict(end_time="09:00"),
        dict(start_time="08:00"),
        dict(end_time="14:00"),
        dict(end_time="12:00:01"),
    ],
)
def test_invalid_activity_times(admin_client, edition, changes):
    assert admin_client.post("/api/admin/activities", json=HIKE | changes).status_code == 422


def test_evening_can_end_at_midnight(admin_client, edition, db):
    response = admin_client.post(
        "/api/admin/activities",
        json=HIKE | dict(period="evening", start_time="21:00", end_time="00:00"),
    )
    assert response.status_code == 201
    activity = db.get(Activity, response.json()["id"])
    assert activity.ends_at == datetime(2026, 7, 13, 22, tzinfo=UTC)


def test_new_activity_requires_structured_times(admin_client, edition):
    body = dict(HIKE)
    del body["start_time"], body["end_time"]
    body["time_label"] = "some free text"
    assert admin_client.post("/api/admin/activities", json=body).status_code == 422


def test_activity_time_edits_are_audited(admin_client, edition, db):
    activity = admin_client.post("/api/admin/activities", json=HIKE).json()
    response = admin_client.patch(
        f"/api/admin/activities/{activity['id']}", json=HIKE | dict(start_time="10:00")
    )
    assert response.status_code == 200
    log = db.scalar(select(AuditLog).where(AuditLog.action == "activity_updated"))
    assert "09:30-12:00 → 10:00-12:00" in log.detail


@pytest.mark.parametrize(
    "endpoint,body",
    [
        ("/api/admin/activities", HIKE | dict(payment_mode="provider")),
        ("/api/admin/meals/2026-07-13/lunch", dict(payment_mode="provider", price_cents=1000)),
    ],
)
def test_direct_payment_needs_instructions(admin_client, edition, endpoint, body):
    method = admin_client.post if endpoint.endswith("activities") else admin_client.put
    assert method(endpoint, json=body).status_code == 422


def test_direct_activity_does_not_increase_camp_fee(
    admin_client, client, outbox, db, edition, make_participant, make_booking
):
    created = admin_client.post("/api/admin/activities", json=HIKE | DIRECT).json()
    make_booking(make_participant("ada@example.com"), [slot(db)])
    login(client, outbox)
    response = client.put("/api/me/booking/activities", json={"activity_ids": [created["id"]]})
    assert response.status_code == 200
    me = client.get("/api/me").json()
    assert me["bookings"][0]["amount_due_cents"] == 1100
    assert me["bookings"][0]["activities"][0]["collectable_cents"] == 0
    assert me["activities"][0]["payment_instructions"] == DIRECT["payment_instructions"]
    report = admin_client.get("/api/admin/views/report").json()
    assert report["revenue"]["due_activities_cents"] == 0
    assert report["activities"][0]["expected_cents"] == 0


def test_meal_change_reprices_only_affected_active_bookings(
    admin_client, db, edition, make_participant, make_booking, clock
):
    booking = make_booking(
        make_participant("ada@example.com"), [slot(db)], status="confermata", amount_due_cents=1900
    )
    booking.meals = [BookingMeal(date=d(13), kind="lunch")]
    db.commit()
    pay(db, booking, 1900)
    other = make_booking(make_participant("bob@example.com"), [slot(db)], amount_due_cents=777)
    expired = make_booking(
        make_participant("cid@example.com"), [slot(db)], status="scaduta", amount_due_cents=1900
    )
    expired.meals = [BookingMeal(date=d(13), kind="lunch")]
    db.commit()
    hold = booking.hold_expires_at
    response = admin_client.put("/api/admin/meals/2026-07-13/lunch", json=DIRECT)
    assert response.status_code == 200, response.text
    detail = admin_client.get(f"/api/admin/registrations/{booking.id}").json()["booking"]
    assert (detail["amount_due_cents"], detail["paid_cents"], detail["balance_cents"]) == (
        1100,
        1900,
        -800,
    )
    assert detail["registration_fee_cents"] == 1100
    assert detail["status"] == "confermata"
    assert detail["meals"][0]["price_cents"] == 2300
    db.refresh(booking)
    db.refresh(other)
    db.refresh(expired)
    assert booking.hold_expires_at == hold
    assert other.amount_due_cents == 777
    assert (expired.status, expired.amount_due_cents) == ("scaduta", 1900)
    assert db.scalar(select(AuditLog).where(AuditLog.action == "pricing_changed")) is not None
    assert (
        admin_client.put(
            "/api/admin/meals/2026-07-13/lunch", json={"payment_mode": "organizer"}
        ).status_code
        == 200
    )
    db.refresh(booking)
    assert booking.amount_due_cents == 1900


def test_pending_booking_is_confirmed_when_new_price_is_covered(
    admin_client, db, edition, make_participant, make_booking, outbox
):
    activity_id = admin_client.post("/api/admin/activities", json=HIKE).json()["id"]
    booking = make_booking(make_participant("ada@example.com"), [slot(db)], amount_due_cents=2600)
    booking.activities = [db.get(Activity, activity_id)]
    db.commit()
    pay(db, booking, 1100)
    response = admin_client.patch(f"/api/admin/activities/{activity_id}", json=HIKE | DIRECT)
    assert response.status_code == 200
    db.refresh(booking)
    assert (booking.amount_due_cents, booking.status) == (1100, "confermata")
    assert len(outbox.sent) == 1
    assert admin_client.patch(f"/api/admin/activities/{activity_id}", json=HIKE).status_code == 200
    db.refresh(booking)
    assert (booking.amount_due_cents, booking.status) == (2600, "confermata")


def test_mixed_meals_and_activity_use_camp_collectable_total(
    admin_client, client, outbox, db, edition, make_participant, make_booking
):
    assert admin_client.put("/api/admin/meals/2026-07-13/lunch", json=DIRECT).status_code == 200
    booking = make_booking(make_participant("ada@example.com"), [slot(db), slot(db, "afternoon")])
    booking.meals = [BookingMeal(date=d(13), kind="lunch"), BookingMeal(date=d(13), kind="dinner")]
    db.commit()
    db.refresh(edition)
    assert recompute_amount(edition, booking) == 2300
    db.commit()
    login(client, outbox)
    meals = client.get("/api/me").json()["bookings"][0]["allowed_meals"]
    assert [(m["kind"], m["collectable_cents"]) for m in meals] == [("lunch", 0), ("dinner", 1200)]
    report = admin_client.get("/api/admin/views/report").json()
    assert (report["revenue"]["due_meals_cents"], report["revenue"]["due_difference_cents"]) == (
        1200,
        0,
    )
    assert "Erogatore" in admin_client.get("/api/admin/views/meals?format=csv").text


def test_legacy_time_label_is_retained_on_update(admin_client, edition, db):
    activity = Activity(
        edition_id=edition.id, title="Legacy", date=d(13), period="morning", time_label="around ten"
    )
    db.add(activity)
    db.commit()
    body = dict(HIKE)
    del body["start_time"], body["end_time"]
    response = admin_client.patch(f"/api/admin/activities/{activity.id}", json=body)
    assert response.status_code == 200
    assert response.json()["time_label"] == "around ten"
    assert response.json()["start_time"] is None


def test_edition_lock_uses_sql_server_update_and_hold_locks():
    class RecordingSession:
        def execute(self, statement):
            sql = str(statement.compile(dialect=mssql.dialect()))
            assert "WITH (UPDLOCK, HOLDLOCK)" in sql

    lock_edition(RecordingSession(), 1)


def test_meal_configuration_is_admin_only(client, edition):
    assert client.put("/api/admin/meals/2026-07-13/lunch", json=DIRECT).status_code == 401


def test_expired_booking_uses_new_terms_when_explicitly_reactivated(
    admin_client, db, edition, make_participant, make_booking, outbox, clock
):
    from app.services.payments import record_payment

    booking = make_booking(
        make_participant("ada@example.com"),
        [slot(db)],
        status="scaduta",
        hold_expires_at=clock(),
        amount_due_cents=1900,
    )
    booking.meals = [BookingMeal(date=d(13), kind="lunch")]
    db.commit()
    assert admin_client.put("/api/admin/meals/2026-07-13/lunch", json=DIRECT).status_code == 200
    db.refresh(booking)
    assert booking.amount_due_cents == 1900
    admin = db.scalar(select(Participant).where(Participant.role == "admin"))
    record_payment(db, outbox, booking, admin, 1100, "iban", d(1), None, clock())
    assert (booking.status, booking.amount_due_cents) == ("confermata", 1100)
