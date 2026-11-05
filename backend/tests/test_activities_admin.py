from sqlalchemy import select

from app.models import Activity, AuditLog, Slot
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


def put(client, booking_id, ids, force=False):
    return client.put(
        f"/api/admin/registrations/{booking_id}/activities",
        json={"activity_ids": ids, "force": force},
    )


def test_detail_offers_the_activities_where_the_person_is(
    admin_client, db, edition, make_participant, make_booking
):
    activity(db, edition, "Escursione", 13, "morning")
    activity(db, edition, "Yoga", 13, "evening")
    booking = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    offers = admin_client.get(f"/api/admin/registrations/{booking.id}").json()["activity_offers"]
    assert [o["title"] for o in offers] == ["Escursione"]


def test_admin_can_force_a_full_activity_and_it_is_flagged(
    admin_client, db, edition, make_participant, make_booking
):
    hike = activity(db, edition, "Escursione", 13, "morning", 1500, 1)
    other = make_booking(make_participant("bob@example.com"), [slot(db, 13)])
    other.activities = [hike]
    db.commit()
    booking = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    refused = put(admin_client, booking.id, [hike.id])
    assert refused.status_code == 409
    assert "Forza oltre la capienza" in refused.json()["detail"]
    forced = put(admin_client, booking.id, [hike.id], force=True)
    assert forced.status_code == 200
    body = forced.json()
    assert "capienza superata in Escursione" in body["warning"]
    assert body["booking"]["amount_due_cents"] == 1100 + 1500
    log = db.scalar(select(AuditLog).where(AuditLog.action == "activities_changed"))
    assert "Oltre la capienza: Escursione (lun 13/07 mattina)." in log.detail


def test_admin_can_change_past_days(
    admin_client, db, edition, make_participant, make_booking, clock
):
    hike = activity(db, edition, "Escursione", 13, "morning")
    booking = make_booking(make_participant("ada@example.com"), [slot(db, 13)], status="confermata")
    clock.advance(days=13)
    assert put(admin_client, booking.id, [hike.id]).status_code == 200


def test_presence_is_required_for_admins_too(
    admin_client, db, edition, make_participant, make_booking
):
    yoga = activity(db, edition, "Yoga", 13, "evening")
    booking = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    response = put(admin_client, booking.id, [yoga.id], force=True)
    assert response.status_code == 422
    assert "Aggiungi prima lo slot" in response.json()["detail"]


def test_participants_cannot_use_it(client, outbox, db, edition, make_participant, make_booking):
    booking = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    login(client, outbox)
    assert put(client, booking.id, []).status_code == 403
