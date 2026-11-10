import csv
import io

from sqlalchemy import select

from app.models import STATUS_CONFIRMED, Slot
from tests.helpers import d
from tests.test_activities_me import activity

GUESTS = "/api/admin/guests"


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


def parse(response):
    assert response.status_code == 200, response.text
    return list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))


def add_guest(client, first, last, meals=(), activity_ids=(), **extra):
    guest_id = client.post(GUESTS, json={"first_name": first, "last_name": last, **extra}).json()[
        "id"
    ]
    client.put(
        f"{GUESTS}/{guest_id}/meals",
        json={"meals": [{"date": f"2026-07-{day}", "kind": kind} for day, kind in meals]},
    )
    if activity_ids:
        client.put(f"{GUESTS}/{guest_id}/activities", json={"activity_ids": list(activity_ids)})
    return guest_id


def eat(db, booking, day, kind):
    from app.models import BookingMeal

    db.add(BookingMeal(booking_id=booking.id, date=d(day), kind=kind))
    db.commit()


def meal_of(view, day, kind):
    day_row = next(x for x in view["days"] if x["date"] == f"2026-07-{day}")
    return next(m for m in day_row["meals"] if m["kind"] == kind)


class TestMealsView:
    def test_guests_are_counted_with_the_participants(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        ada = make_booking(
            make_participant("ada@example.com", first_name="Ada", last_name="Lovelace"),
            [slot(db, 13)],
            status=STATUS_CONFIRMED,
        )
        eat(db, ada, 13, "lunch")
        add_guest(admin_client, "Anna", "Rossi", [(13, "lunch"), (13, "dinner")], diet="vegan")
        view = admin_client.get("/api/admin/views/meals").json()
        lunch = meal_of(view, "13", "lunch")
        assert lunch["count"] == 2
        assert lunch["diets"]["vegan"] == 1
        assert meal_of(view, "13", "dinner")["count"] == 1
        guest = next(p for p in lunch["people"] if p["external"])
        assert (guest["first_name"], guest["booking_id"], guest["email"]) == ("Anna", None, "")
        assert guest["guest_id"] is not None
        assert guest["collectable_cents"] == 0
        participant = next(p for p in lunch["people"] if not p["external"])
        assert participant["booking_id"] == ada.id

    def test_allergies_of_guests_are_in_the_admin_view_only(self, admin_client, edition):
        add_guest(
            admin_client,
            "Anna",
            "Rossi",
            [(13, "lunch")],
            allergies="noci",
            allergies_consent=True,
        )
        lunch = meal_of(admin_client.get("/api/admin/views/meals").json(), "13", "lunch")
        assert lunch["people"][0]["allergies"] == "noci"

    def test_meals_csv_has_one_row_per_person_and_a_type_column(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
        eat(db, ada, 13, "lunch")
        add_guest(admin_client, "Anna", "Rossi", [(13, "lunch")])
        header, *rows = parse(admin_client.get("/api/admin/views/meals?format=csv"))
        assert header[-1] == "Tipo"
        assert sorted(row[-1] for row in rows) == ["Esterno", "Iscritto"]
        english = parse(admin_client.get("/api/admin/views/meals?format=csv&lang=en"))
        assert english[0][-1] == "Type"
        assert sorted(row[-1] for row in english[1:]) == ["Guest", "Participant"]

    def test_a_guest_is_counted_once_per_meal(self, admin_client, edition):
        add_guest(admin_client, "Anna", "Rossi", [(13, "lunch"), (13, "lunch")])
        lunch = meal_of(admin_client.get("/api/admin/views/meals").json(), "13", "lunch")
        assert lunch["count"] == len(lunch["people"]) == 1

    def test_a_guest_without_meals_is_not_listed(self, admin_client, edition):
        add_guest(admin_client, "Anna", "Rossi")
        lunch = meal_of(admin_client.get("/api/admin/views/meals").json(), "13", "lunch")
        assert lunch["count"] == 0


class TestWeekView:
    def test_week_counts_guest_meals_and_activities_but_not_coworking(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        hike = activity(db, edition, "Escursione", 13, "morning")
        make_booking(make_participant("ada@example.com"), [slot(db, 13)])
        add_guest(
            admin_client,
            "Anna",
            "Rossi",
            [(13, "lunch"), (13, "dinner")],
            activity_ids=[hike.id],
        )
        week = admin_client.get("/api/admin/views/week").json()
        monday = next(x for x in week["days"] if x["date"] == "2026-07-13")
        assert (monday["lunches"], monday["dinners"], monday["activities"]) == (1, 1, 1)
        assert (monday["morning"], monday["people"]) == (1, 1)
        assert (week["total_lunches"], week["total_dinners"], week["total_activities"]) == (
            1,
            1,
            1,
        )

    def test_week_counts_a_person_once_across_participants_and_guests(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        ada = make_booking(
            make_participant("ada@example.com", first_name="Anna", last_name="Rossi"),
            [slot(db, 13)],
        )
        eat(db, ada, 13, "lunch")
        add_guest(admin_client, "Anna", "Rossi", [(13, "lunch")], confirm_duplicate=True)
        monday = next(
            x
            for x in admin_client.get("/api/admin/views/week").json()["days"]
            if x["date"] == "2026-07-13"
        )
        # Two different people with the same name: the admin said so, so both are counted.
        assert monday["lunches"] == 2


class TestActivityViews:
    def test_detail_lists_guests_apart_and_counts_them(self, admin_client, db, edition):
        hike = activity(db, edition, "Escursione", 13, "morning", capacity=3)
        add_guest(admin_client, "Anna", "Rossi", activity_ids=[hike.id], phone="333")
        detail = admin_client.get(f"/api/admin/activities/{hike.id}").json()
        assert detail["people"] == []
        assert [(g["first_name"], g["phone"], g["payer"]) for g in detail["guests"]] == [
            ("Anna", "333", "paying")
        ]
        assert (detail["joined"], detail["free"]) == (1, 2)

    def test_csv_rows_mark_the_type_of_each_person(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        hike = activity(db, edition, "Escursione", 13, "morning", capacity=5)
        ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
        ada.activities = [hike]
        db.commit()
        add_guest(admin_client, "Anna", "Rossi", activity_ids=[hike.id])
        header, *rows = parse(admin_client.get(f"/api/admin/activities/{hike.id}?format=csv"))
        assert header[-2:] == ["Tipo", "Nota interna"]
        assert sorted((r[4], r[-2]) for r in rows) == [("Ada", "Iscritto"), ("Anna", "Esterno")]
        english = parse(admin_client.get("/api/admin/activities?format=csv&lang=en"))
        assert sorted(r[-2] for r in english[1:]) == ["Guest", "Participant"]

    def test_an_activity_with_only_guests_still_has_rows(self, admin_client, db, edition):
        hike = activity(db, edition, "Escursione", 13, "morning")
        add_guest(admin_client, "Anna", "Rossi", activity_ids=[hike.id])
        rows = parse(admin_client.get("/api/admin/activities?format=csv"))[1:]
        assert [(r[4], r[-2]) for r in rows] == [("Anna", "Esterno")]

    def test_guests_change_no_money_in_any_view(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        hike = activity(db, edition, "Escursione", 13, "morning", price=1500)
        make_booking(make_participant("ada@example.com"), [slot(db, 13)])
        before = admin_client.get("/api/admin/views/to-collect").json()
        add_guest(admin_client, "Anna", "Rossi", [(13, "lunch")], activity_ids=[hike.id])
        assert admin_client.get("/api/admin/views/to-collect").json() == before
