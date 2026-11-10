import csv
import io

import pytest
from sqlalchemy import select

from app.models import (
    STATUS_EXPIRED,
    Activity,
    ActivityNoteRevision,
    AuditLog,
    BookingActivity,
    Slot,
)
from tests.helpers import d
from tests.test_auth import login

HIKE = {
    "title": "Escursione",
    "description": "Sul monte",
    "title_it": "Escursione",
    "title_en": "Hike",
    "description_it": "Sul monte",
    "description_en": "On the mountain",
    "date": "2026-07-14",
    "period": "morning",
    "start_time": "09:30",
    "end_time": "12:00",
    "price_cents": 1500,
    "capacity": 2,
}


def parse(response):
    return list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


@pytest.fixture
def hike(admin_client, edition):
    response = admin_client.post("/api/admin/activities", json=HIKE)
    assert response.status_code == 201
    return response.json()


def join(db, booking, activity_id):
    booking.activities.append(db.get(Activity, activity_id))
    db.commit()


def test_create_and_list(admin_client, hike, db):
    assert (hike["joined"], hike["free"]) == (0, 2)
    listed = admin_client.get("/api/admin/activities").json()
    assert [a["title"] for a in listed] == ["Escursione"]
    log = db.scalar(select(AuditLog).where(AuditLog.action == "activity_created"))
    assert log.detail == "Attività creata: Escursione (mar 14/07 mattina), 15,00 €, 2 posti"


def test_day_outside_the_edition_is_refused(admin_client, edition):
    response = admin_client.post("/api/admin/activities", json=dict(HIKE, date="2026-08-01"))
    assert response.status_code == 422
    assert "date dell'edizione" in response.json()["detail"]


def test_free_activity_without_limit(admin_client, edition):
    body = dict(HIKE, price_cents=0, capacity=None)
    created = admin_client.post("/api/admin/activities", json=body).json()
    assert (created["price_cents"], created["capacity"], created["free"]) == (0, None, None)


def test_without_people_everything_can_change(admin_client, hike):
    changed = dict(
        HIKE,
        price_cents=2000,
        date="2026-07-15",
        period="afternoon",
        start_time="14:30",
        end_time="16:00",
        capacity=1,
    )
    response = admin_client.patch(f"/api/admin/activities/{hike['id']}", json=changed)
    assert response.status_code == 200
    assert response.json()["price_cents"] == 2000


def test_with_people_day_and_part_of_day_are_fixed(
    admin_client, hike, db, make_participant, make_booking
):
    booking = make_booking(make_participant("ada@example.com"), [slot(db, 14)])
    join(db, booking, hike["id"])
    url = f"/api/admin/activities/{hike['id']}"
    for change in (
        {"date": "2026-07-15"},
        {"period": "afternoon", "start_time": "14:00", "end_time": "16:00"},
    ):
        response = admin_client.patch(url, json=dict(HIKE, **change))
        assert response.status_code == 409
        assert "Con persone già iscritte" in response.json()["detail"]
    ok = admin_client.patch(
        url,
        json=dict(
            HIKE,
            title_it="Escursione al lago",
            title_en="Lake hike",
            description_it="Sul monte",
            description_en="On the mountain",
            capacity=5,
        ),
    )
    assert ok.status_code == 200
    assert (ok.json()["title"], ok.json()["joined"]) == ("Escursione al lago", 1)


def test_capacity_cannot_drop_below_the_people(
    admin_client, hike, db, make_participant, make_booking
):
    for email in ("ada@example.com", "bob@example.com"):
        join(db, make_booking(make_participant(email), [slot(db, 14)]), hike["id"])
    response = admin_client.patch(
        f"/api/admin/activities/{hike['id']}", json=dict(HIKE, capacity=1)
    )
    assert response.status_code == 409
    assert "sotto il numero di iscritti" in response.json()["detail"]


def test_delete_only_without_people(admin_client, hike, db, make_participant, make_booking, clock):
    booking = make_booking(
        make_participant("ada@example.com"),
        [slot(db, 14)],
        status=STATUS_EXPIRED,
        hold_expires_at=clock(),
    )
    join(db, booking, hike["id"])
    url = f"/api/admin/activities/{hike['id']}"
    assert admin_client.delete(url).status_code == 409
    booking.activities = []
    db.commit()
    assert admin_client.delete(url).status_code == 204
    assert admin_client.get(url).status_code == 404
    assert db.scalar(select(AuditLog).where(AuditLog.action == "activity_deleted")) is not None


def test_detail_and_csv_list_the_people(
    admin_client, hike, db, make_participant, make_booking, clock
):
    ada = make_booking(make_participant("ada@example.com", phone="+39 333"), [slot(db, 14)])
    gone = make_booking(
        make_participant("bob@example.com", first_name="Bob"),
        [slot(db, 14)],
        status=STATUS_EXPIRED,
        hold_expires_at=clock(),
    )
    join(db, ada, hike["id"])
    join(db, gone, hike["id"])
    detail = admin_client.get(f"/api/admin/activities/{hike['id']}").json()
    assert [p["first_name"] for p in detail["people"]] == ["Ada"]
    assert (detail["joined"], detail["free"]) == (1, 1)
    header, *rows = parse(admin_client.get(f"/api/admin/activities/{hike['id']}?format=csv"))
    assert header[:4] == ["Giorno", "Fascia", "Attività", "Prezzo"]
    assert rows == [
        [
            "14/07/2026",
            "Mattina",
            "Escursione",
            "15,00",
            "Ada",
            "Lovelace",
            "ada@example.com",
            "+39 333",
            "In attesa di pagamento",
            "Organizzatori",
            "",
            "Iscritto",
            "",
        ]
    ]
    all_rows = parse(admin_client.get("/api/admin/activities?format=csv"))[1:]
    assert all_rows == rows


def test_bilingual_content_and_private_note_history(admin_client, hike, db):
    response = admin_client.patch(
        f"/api/admin/activities/{hike['id']}",
        json=dict(
            HIKE,
            title_it="Escursione",
            title_en="Hike",
            description_it="Sul monte",
            description_en="In the mountains",
        ),
    )
    assert response.status_code == 200
    detail = admin_client.get(f"/api/admin/activities/{hike['id']}").json()
    assert detail["title_it"] == "Escursione"
    assert detail["title_en"] == "Hike"

    saved = admin_client.put(
        f"/api/admin/activities/{hike['id']}/note", json={"note": "Portare acqua"}
    )
    assert saved.status_code == 200
    detail = admin_client.get(f"/api/admin/activities/{hike['id']}").json()
    assert detail["internal_note"] == "Portare acqua"
    assert detail["note_history"][0]["note"] == "Portare acqua"

    csv_rows = parse(admin_client.get("/api/admin/activities?format=csv"))
    assert csv_rows[1][-1] == "Portare acqua"

    db.query(BookingActivity).filter_by(activity_id=hike["id"]).delete()
    db.commit()


def test_activity_note_is_exported_once_and_revisions_cascade_on_delete(
    admin_client, hike, db, make_participant, make_booking
):
    for email in ("ada@example.com", "bob@example.com"):
        join(db, make_booking(make_participant(email), [slot(db, 14)]), hike["id"])
    admin_client.put(f"/api/admin/activities/{hike['id']}/note", json={"note": "Portare acqua"})
    rows = parse(admin_client.get(f"/api/admin/activities/{hike['id']}?format=csv"))[1:]
    assert [row[-1] for row in rows] == ["Portare acqua", ""]

    empty = admin_client.post(
        "/api/admin/activities",
        json=dict(
            HIKE,
            date="2026-07-15",
            period="afternoon",
            start_time="14:30",
            end_time="16:00",
        ),
    ).json()
    admin_client.put(f"/api/admin/activities/{empty['id']}/note", json={"note": "Da comprare"})
    assert admin_client.delete(f"/api/admin/activities/{empty['id']}").status_code == 204
    assert db.query(ActivityNoteRevision).filter_by(activity_id=empty["id"]).count() == 0


def test_creation_and_content_changes_require_all_translations(admin_client, hike):
    legacy = admin_client.post(
        "/api/admin/activities",
        json={
            key: value
            for key, value in HIKE.items()
            if key not in {"title_it", "title_en", "description_it", "description_en"}
        },
    )
    assert legacy.status_code == 422

    partial = admin_client.patch(
        f"/api/admin/activities/{hike['id']}",
        json={
            **{
                key: value
                for key, value in HIKE.items()
                if key not in {"title_it", "title_en", "description_it", "description_en"}
            },
            "title_it": "Nuovo titolo",
        },
    )
    assert partial.status_code == 422

    blank_description = admin_client.patch(
        f"/api/admin/activities/{hike['id']}",
        json=dict(HIKE, description_it="", description_en="A description"),
    )
    assert blank_description.status_code == 422


def test_operational_update_preserves_missing_legacy_translations(admin_client, hike, db):
    activity = db.get(Activity, hike["id"])
    activity.title_it = None
    activity.title_en = None
    activity.description_it = None
    activity.description_en = None
    db.commit()

    response = admin_client.patch(
        f"/api/admin/activities/{hike['id']}",
        json={
            **{
                key: value
                for key, value in HIKE.items()
                if not key.startswith(("title_", "description_"))
            },
            "price_cents": 1900,
        },
    )
    assert response.status_code == 200
    db.refresh(activity)
    assert activity.title_it is None and activity.title_en is None
    assert activity.description_it is None and activity.description_en is None
    assert activity.price_cents == 1900


def test_empty_activity_csv_contains_note(admin_client, hike):
    admin_client.put(f"/api/admin/activities/{hike['id']}/note", json={"note": "Solo admin"})
    rows = parse(admin_client.get("/api/admin/activities?format=csv"))
    assert rows[1][2] == "Escursione"
    assert rows[1][-1] == "Solo admin"


def test_participants_cannot_manage_activities(client, outbox, make_participant, edition):
    make_participant("ada@example.com")
    login(client, outbox)
    assert client.get("/api/admin/activities").status_code == 403
    assert client.post("/api/admin/activities", json=HIKE).status_code == 403
