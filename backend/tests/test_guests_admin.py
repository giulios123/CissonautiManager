import csv
import io

from sqlalchemy import func, select

from app.models import (
    Activity,
    AuditLog,
    Booking,
    ExternalGuest,
    ExternalGuestActivity,
    ExternalGuestMeal,
    Participant,
    Slot,
)
from tests.helpers import d
from tests.test_activities_me import activity
from tests.test_auth import login

URL = "/api/admin/guests"


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


def new_guest(client, first="Anna", last="Rossi", **extra):
    return client.post(URL, json={"first_name": first, "last_name": last, **extra})


def put_activities(client, guest_id, ids, force=False):
    return client.put(f"{URL}/{guest_id}/activities", json={"activity_ids": ids, "force": force})


class TestAccess:
    def test_guests_are_for_admins_only(self, client, outbox, make_participant, edition):
        make_participant("ada@example.com")
        login(client, outbox)
        assert client.get(URL).status_code == 403
        assert new_guest(client).status_code == 403
        assert client.get(f"{URL}?format=csv").status_code == 403

    def test_anonymous_is_refused(self, client, edition):
        assert client.get(URL).status_code == 401

    def test_participants_cannot_touch_a_guest(
        self, admin_client, client, outbox, make_participant, edition
    ):
        guest_id = new_guest(admin_client).json()["id"]
        make_participant("ada@example.com")
        login(client, outbox)
        for call in (
            client.get(f"{URL}/{guest_id}"),
            client.patch(f"{URL}/{guest_id}", json={"first_name": "X", "last_name": "Y"}),
            client.delete(f"{URL}/{guest_id}"),
            client.put(f"{URL}/{guest_id}/meals", json={"meals": []}),
            client.put(f"{URL}/{guest_id}/activities", json={"activity_ids": []}),
        ):
            assert call.status_code == 403


class TestCreate:
    def test_creates_a_guest_without_account_or_booking(self, admin_client, db, edition):
        people = db.scalar(select(func.count()).select_from(Participant))
        response = new_guest(admin_client, phone="333", reference="con Maria", payer="non_paying")
        assert response.status_code == 201
        body = response.json()
        assert (body["first_name"], body["payer"], body["reference"]) == (
            "Anna",
            "non_paying",
            "con Maria",
        )
        assert db.scalar(select(func.count()).select_from(Participant)) == people
        assert db.scalar(select(func.count()).select_from(Booking)) == 0
        guest = db.get(ExternalGuest, body["id"])
        assert guest.edition_id == edition.id

    def test_the_creation_is_recorded_in_the_history(self, admin_client, db, edition):
        new_guest(admin_client)
        log = db.scalar(select(AuditLog).where(AuditLog.action == "guest_created"))
        assert "Anna Rossi" in log.detail

    def test_requires_an_edition(self, admin_client):
        assert new_guest(admin_client).status_code == 404

    def test_a_name_is_required(self, admin_client, edition):
        assert new_guest(admin_client, first=" ").status_code == 422


class TestDuplicates:
    def test_same_name_as_another_guest_needs_confirmation(self, admin_client, edition):
        new_guest(admin_client)
        refused = new_guest(admin_client, first=" ANNA", last="rossi")
        assert refused.status_code == 409
        assert "Anna Rossi" in refused.json()["detail"]
        assert new_guest(admin_client, confirm_duplicate=True).status_code == 201

    def test_same_name_as_an_active_participant_needs_confirmation(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        ada = make_participant("ada@example.com", first_name="Ada", last_name="Lovelace")
        make_booking(ada, [slot(db, 13)])
        assert new_guest(admin_client, "Ada", "Lovelace").status_code == 409
        assert new_guest(admin_client, "Ada", "Lovelace", confirm_duplicate=True).status_code == 201

    def test_a_participant_without_active_booking_is_not_a_duplicate(
        self, admin_client, edition, make_participant
    ):
        make_participant("ada@example.com", first_name="Ada", last_name="Lovelace")
        assert new_guest(admin_client, "Ada", "Lovelace").status_code == 201

    def test_editing_a_guest_does_not_clash_with_itself(self, admin_client, edition):
        guest_id = new_guest(admin_client).json()["id"]
        response = admin_client.patch(
            f"{URL}/{guest_id}", json={"first_name": "Anna", "last_name": "Rossi", "phone": "1"}
        )
        assert response.status_code == 200
        assert response.json()["phone"] == "1"


class TestMeals:
    def test_a_guest_takes_meals_without_any_slot(self, admin_client, db, edition):
        guest_id = new_guest(admin_client).json()["id"]
        response = admin_client.put(
            f"{URL}/{guest_id}/meals",
            json={
                "meals": [
                    {"date": "2026-07-13", "kind": "lunch"},
                    {"date": "2026-07-14", "kind": "dinner"},
                ]
            },
        )
        assert response.status_code == 200
        assert [(m["date"], m["kind"]) for m in response.json()["meals"]] == [
            ("2026-07-13", "lunch"),
            ("2026-07-14", "dinner"),
        ]
        assert db.scalar(select(func.count()).select_from(ExternalGuestMeal)) == 2

    def test_past_days_are_allowed(self, admin_client, clock, edition):
        clock.advance(days=13)
        guest_id = new_guest(admin_client).json()["id"]
        response = admin_client.put(
            f"{URL}/{guest_id}/meals", json={"meals": [{"date": "2026-07-13", "kind": "lunch"}]}
        )
        assert response.status_code == 200

    def test_a_day_outside_the_edition_is_refused(self, admin_client, edition):
        guest_id = new_guest(admin_client).json()["id"]
        response = admin_client.put(
            f"{URL}/{guest_id}/meals", json={"meals": [{"date": "2026-07-25", "kind": "lunch"}]}
        )
        assert response.status_code == 422

    def test_the_same_meal_twice_counts_once(self, admin_client, db, edition):
        guest_id = new_guest(admin_client).json()["id"]
        meal = {"date": "2026-07-13", "kind": "lunch"}
        admin_client.put(f"{URL}/{guest_id}/meals", json={"meals": [meal, meal]})
        assert db.scalar(select(func.count()).select_from(ExternalGuestMeal)) == 1

    def test_removing_a_meal_is_recorded(self, admin_client, db, edition):
        guest_id = new_guest(admin_client).json()["id"]
        meal = {"date": "2026-07-13", "kind": "lunch"}
        admin_client.put(f"{URL}/{guest_id}/meals", json={"meals": [meal]})
        admin_client.put(f"{URL}/{guest_id}/meals", json={"meals": []})
        details = [
            log.detail
            for log in db.scalars(select(AuditLog).where(AuditLog.action == "guest_meals_changed"))
        ]
        assert len(details) == 2
        assert "aggiunti" in details[0]
        assert "tolti" in details[1]


class TestActivities:
    def test_a_guest_takes_a_seat_of_the_capacity(self, admin_client, db, edition):
        hike = activity(db, edition, "Escursione", 13, "morning", capacity=1)
        first = new_guest(admin_client).json()["id"]
        second = new_guest(admin_client, "Luca", "Bianchi").json()["id"]
        assert put_activities(admin_client, first, [hike.id]).status_code == 200
        refused = put_activities(admin_client, second, [hike.id])
        assert refused.status_code == 409
        assert "Forza oltre la capienza" in refused.json()["detail"]

    def test_force_goes_over_capacity_with_a_warning(self, admin_client, db, edition):
        hike = activity(db, edition, "Escursione", 13, "morning", capacity=1)
        first = new_guest(admin_client).json()["id"]
        second = new_guest(admin_client, "Luca", "Bianchi").json()["id"]
        put_activities(admin_client, first, [hike.id])
        forced = put_activities(admin_client, second, [hike.id], force=True)
        assert forced.status_code == 200
        assert "capienza superata in Escursione" in forced.json()["warning"]

    def test_a_guest_needs_no_presence(self, admin_client, db, edition):
        evening = activity(db, edition, "Quiz", 13, "evening")
        guest_id = new_guest(admin_client).json()["id"]
        assert put_activities(admin_client, guest_id, [evening.id]).status_code == 200

    def test_an_unknown_activity_is_refused(self, admin_client, edition):
        guest_id = new_guest(admin_client).json()["id"]
        assert put_activities(admin_client, guest_id, [99999]).status_code == 422

    def test_leaving_frees_the_seat(self, admin_client, db, edition):
        hike = activity(db, edition, "Escursione", 13, "morning", capacity=1)
        first = new_guest(admin_client).json()["id"]
        second = new_guest(admin_client, "Luca", "Bianchi").json()["id"]
        put_activities(admin_client, first, [hike.id])
        put_activities(admin_client, first, [])
        assert put_activities(admin_client, second, [hike.id]).status_code == 200

    def test_guests_fill_the_activity_for_participants(
        self, admin_client, client, outbox, db, edition, make_participant, make_booking
    ):
        hike = activity(db, edition, "Escursione", 13, "morning", capacity=1)
        ada = make_participant("ada@example.com")
        make_booking(ada, [slot(db, 13)], amount_due_cents=1100)
        guest_id = new_guest(admin_client).json()["id"]
        put_activities(admin_client, guest_id, [hike.id])
        login(client, outbox)
        offer = client.get("/api/me").json()["activities"][0]
        assert (offer["free"], offer["joined"]) == (0, False)
        refused = client.put("/api/me/booking/activities", json={"activity_ids": [hike.id]})
        assert refused.status_code == 409

    def test_the_admin_sees_guests_in_the_activity_headcount(self, admin_client, db, edition):
        hike = activity(db, edition, "Escursione", 13, "morning", capacity=3)
        guest_id = new_guest(admin_client).json()["id"]
        put_activities(admin_client, guest_id, [hike.id])
        listed = admin_client.get("/api/admin/activities").json()[0]
        assert (listed["joined"], listed["free"]) == (1, 2)

    def test_capacity_cannot_drop_below_the_guests(self, admin_client, db, edition):
        hike = activity(db, edition, "Escursione", 13, "morning", capacity=3)
        for name in ("Anna", "Luca"):
            guest_id = new_guest(admin_client, name, "Test").json()["id"]
            put_activities(admin_client, guest_id, [hike.id])
        response = admin_client.patch(
            f"/api/admin/activities/{hike.id}", json=_activity_body(hike, capacity=1)
        )
        assert response.status_code == 409

    def test_an_activity_with_guests_is_fixed_and_cannot_be_deleted(
        self, admin_client, db, edition
    ):
        hike = activity(db, edition, "Escursione", 13, "morning")
        guest_id = new_guest(admin_client).json()["id"]
        put_activities(admin_client, guest_id, [hike.id])
        moved = admin_client.patch(
            f"/api/admin/activities/{hike.id}", json=_activity_body(hike, period="afternoon")
        )
        assert moved.status_code == 409
        assert admin_client.delete(f"/api/admin/activities/{hike.id}").status_code == 409


def _activity_body(activity: Activity, **changes) -> dict:
    body = {
        "title": activity.title,
        "date": activity.date.isoformat(),
        "period": activity.period,
        "price_cents": activity.price_cents,
        "capacity": activity.capacity,
        "payment_mode": "organizer",
    }
    body.update(changes)
    return body


class TestHealthData:
    def test_allergies_need_the_collected_consent(self, admin_client, edition):
        refused = new_guest(admin_client, allergies="noci")
        assert refused.status_code == 422

    def test_allergies_are_saved_with_consent_and_the_author_is_kept(
        self, admin_client, db, edition
    ):
        response = new_guest(admin_client, allergies="noci", allergies_consent=True, diet="vegan")
        body = response.json()
        assert (body["allergies"], body["diet"]) == ("noci", "vegan")
        assert body["allergies_consent_at"] is not None
        guest = db.get(ExternalGuest, body["id"])
        boss = db.scalar(select(Participant).where(Participant.email == "boss@example.com"))
        assert guest.allergies_consent_by_id == boss.id

    def test_removing_the_consent_erases_the_allergies(self, admin_client, db, edition):
        guest_id = new_guest(admin_client, allergies="noci", allergies_consent=True).json()["id"]
        response = admin_client.patch(
            f"{URL}/{guest_id}",
            json={"first_name": "Anna", "last_name": "Rossi", "allergies_consent": False},
        )
        body = response.json()
        assert (body["allergies"], body["allergies_consent_at"]) == (None, None)

    def test_a_consent_that_stays_keeps_its_original_date(self, admin_client, clock, edition):
        created = new_guest(admin_client, allergies="noci", allergies_consent=True).json()
        clock.advance(days=1)
        again = admin_client.patch(
            f"{URL}/{created['id']}",
            json={
                "first_name": "Anna",
                "last_name": "Rossi",
                "allergies": "noci e latte",
                "allergies_consent": True,
            },
        ).json()
        assert again["allergies"] == "noci e latte"
        assert again["allergies_consent_at"] == created["allergies_consent_at"]


class TestDelete:
    def test_deleting_removes_the_guest_and_the_sign_ups(self, admin_client, db, edition):
        hike = activity(db, edition, "Escursione", 13, "morning", capacity=1)
        guest_id = new_guest(admin_client).json()["id"]
        admin_client.put(
            f"{URL}/{guest_id}/meals", json={"meals": [{"date": "2026-07-13", "kind": "lunch"}]}
        )
        put_activities(admin_client, guest_id, [hike.id])
        assert admin_client.delete(f"{URL}/{guest_id}").status_code == 204
        assert db.scalar(select(func.count()).select_from(ExternalGuest)) == 0
        assert db.scalar(select(func.count()).select_from(ExternalGuestMeal)) == 0
        assert db.scalar(select(func.count()).select_from(ExternalGuestActivity)) == 0
        log = db.scalar(select(AuditLog).where(AuditLog.action == "guest_deleted"))
        assert "Anna Rossi" in log.detail

    def test_unknown_guest_is_not_found(self, admin_client, edition):
        assert admin_client.get(f"{URL}/999").status_code == 404


class TestCsv:
    def test_csv_lists_guests_in_the_language_of_the_app(self, admin_client, db, edition):
        hike = activity(db, edition, "Escursione", 13, "morning")
        guest_id = new_guest(admin_client, diet="vegan", allergies="noci", allergies_consent=True)
        guest_id = guest_id.json()["id"]
        admin_client.put(
            f"{URL}/{guest_id}/meals", json={"meals": [{"date": "2026-07-13", "kind": "lunch"}]}
        )
        put_activities(admin_client, guest_id, [hike.id])
        response = admin_client.get(f"{URL}?format=csv&lang=en")
        rows = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))
        assert rows[0][:3] == ["Last name", "First name", "Paying"]
        assert rows[1][0:2] == ["Rossi", "Anna"]
        assert "noci" not in response.text
        assert "guests-" in response.headers["content-disposition"]
