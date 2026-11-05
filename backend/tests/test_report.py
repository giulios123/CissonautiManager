import csv
import io
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import (
    CLOSE_PROMOTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    Activity,
    BookingMeal,
    Contribution,
    Slot,
)
from tests.helpers import d
from tests.test_auth import login
from tests.test_change_slots import pay


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


def parse(response):
    return list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))


@pytest.fixture
def camp(db, edition, make_participant, make_booking, add_entry, clock):
    """Ada confirmed and paid (whole Monday, both meals, a paid hike, vegan with an allergy);
    Bob still to pay (Monday morning and lunch); Cid expired with a partial payment; Eve waited
    and was promoted as a verified +1; Fay is still waiting."""
    hike = Activity(
        edition_id=edition.id,
        title="Trekking",
        date=d(13),
        period="morning",
        price_cents=1500,
        capacity=10,
    )
    db.add(hike)
    db.commit()

    ada = make_booking(
        make_participant("ada@example.com", first_name="Ada", last_name="Lovelace"),
        [slot(db, 13), slot(db, 13, "afternoon")],
        status=STATUS_CONFIRMED,
        amount_due_cents=4600,
    )
    ada.meals = [BookingMeal(date=d(13), kind="lunch"), BookingMeal(date=d(13), kind="dinner")]
    ada.activities = [hike]
    ada.diet, ada.allergies = "vegan", "Arachidi e noci"
    ada.contributions = [Contribution(kind="talk", title="Macchine")]
    db.commit()
    pay(db, ada, 4600)

    bob = make_booking(
        make_participant("bob@example.com", first_name="Bob", last_name="Neri"),
        [slot(db, 13)],
        status=STATUS_PENDING,
        amount_due_cents=1900,
    )
    bob.meals = [BookingMeal(date=d(13), kind="lunch")]
    db.commit()
    pay(db, bob, 500)

    cid = make_booking(
        make_participant("cid@example.com", first_name="Cid", last_name="Rossi"),
        [slot(db, 13)],
        status=STATUS_EXPIRED,
    )
    pay(db, cid, 300)

    eve = make_participant("eve@example.com", first_name="Eve", invited_by="Ada")
    eve.plus_one_verified_at = clock()
    promoted = add_entry(slot(db, 14), eve, clock() - timedelta(hours=3))
    promoted.closed_at, promoted.close_reason = clock(), CLOSE_PROMOTED
    add_entry(slot(db, 14), make_participant("fay@example.com", first_name="Fay"), clock())
    db.commit()
    return {"ada": ada, "bob": bob, "cid": cid}


def get(client, fmt=None):
    return client.get("/api/admin/views/report" + (f"?format={fmt}" if fmt else ""))


class TestJson:
    def test_enrollment_and_who_has_a_seat(self, admin_client, camp):
        report = get(admin_client).json()
        assert report["enrollment"]["by_status"]["confermata"] == 1
        assert report["enrollment"]["by_status"]["in_attesa_pagamento"] == 1
        assert report["enrollment"]["by_status"]["scaduta"] == 1
        assert report["enrollment"]["people_with_seat"] == 2

    def test_the_edition_is_named(self, admin_client, camp):
        assert get(admin_client).json()["edition"]["name"]

    def test_presence_agrees_with_the_week_view(self, admin_client, camp):
        report = get(admin_client).json()
        week = admin_client.get("/api/admin/views/week").json()["days"][0]
        monday = {
            s["period"]: s["present"]
            for s in report["presence"]["slots"]
            if s["day"] == "2026-07-13"
        }
        assert monday["morning"]["total"] == week["morning"] == 2
        assert monday["afternoon"]["total"] == week["afternoon"] == 1
        assert monday["evening"]["total"] == week["evening"] == 1
        assert monday["morning"] == {"confirmed": 1, "pending": 1, "total": 2}

    def test_the_derived_evening_is_flagged(self, admin_client, camp):
        slots = get(admin_client).json()["presence"]["slots"]
        evening = next(s for s in slots if s["day"] == "2026-07-13" and s["period"] == "evening")
        assert evening["derived"] == 1

    def test_meals_agree_with_the_meals_view(self, admin_client, camp):
        report = get(admin_client).json()["meals"]
        view = admin_client.get("/api/admin/views/meals").json()["days"][0]["meals"]
        lunch, dinner = view
        assert report["days"][0]["lunches"]["total"] == lunch["count"] == 2
        assert report["days"][0]["dinners"]["total"] == dinner["count"] == 1
        assert report["lunch_diets"]["vegan"] == lunch["diets"]["vegan"] == 1

    def test_allergies_are_only_a_number(self, admin_client, camp):
        response = get(admin_client)
        assert response.json()["meals"]["people_with_allergies"] == 1
        assert "Arachidi" not in response.text and "noci" not in response.text

    def test_activities_agree_with_the_activities_view(self, admin_client, camp):
        report = get(admin_client).json()["activities"]
        listed = admin_client.get("/api/admin/activities").json()
        assert report[0]["joined"]["total"] == listed[0]["joined"] == 1
        assert report[0]["expected_cents"] == 1500

    def test_contributions_and_waitlist(self, admin_client, camp):
        report = get(admin_client).json()
        assert report["contributions"] == {"talk": 1, "topic": 0, "skill": 0}
        assert report["waitlist"]["waiting"] == 1
        assert report["waitlist"]["promoted"] == 1
        assert report["waitlist"]["promoted_plus_one"] == 1

    def test_revenue_agrees_with_the_people_view(self, admin_client, camp):
        revenue = get(admin_client).json()["revenue"]
        rows = admin_client.get("/api/admin/registrations").json()
        seated = [r for r in rows if r["status"] in ("confermata", "in_attesa_pagamento")]
        assert revenue["due_cents"] == sum(r["amount_due_cents"] for r in seated) == 6500
        assert revenue["paid_cents"] == sum(r["paid_cents"] for r in rows) == 5400
        assert revenue["to_collect_cents"] == 1400
        assert revenue["paid_by_channel"]
        assert sum(revenue["paid_by_channel"].values()) == revenue["paid_cents"]
        parts = sum(
            revenue[k]
            for k in (
                "due_fee_cents",
                "due_meals_cents",
                "due_activities_cents",
                "due_difference_cents",
            )
        )
        assert parts == revenue["due_cents"]

    def test_a_voided_payment_does_not_count(self, admin_client, camp):
        before = get(admin_client).json()["revenue"]["paid_cents"]
        bob = camp["bob"]
        detail = admin_client.get(f"/api/admin/registrations/{bob.id}").json()
        payment_id = detail["booking"]["payments"][0]["id"]
        voided = admin_client.post(
            f"/api/admin/registrations/{bob.id}/payments/{payment_id}/void",
            json={"reason": "Errore di battitura"},
        )
        assert voided.status_code == 200, voided.text
        assert get(admin_client).json()["revenue"]["paid_cents"] == before - 500


class TestCsv:
    def test_it_opens_in_italian_excel_and_has_the_five_columns(self, admin_client, camp):
        response = get(admin_client, "csv")
        assert response.headers["content-type"].startswith("text/csv")
        assert response.content.startswith(b"\xef\xbb\xbf")
        assert response.headers["content-disposition"].startswith('attachment; filename="report-')
        header, *rows = parse(response)
        assert header == ["Sezione", "Voce", "Confermate", "In attesa di pagamento", "Totale"]
        sections = {r[0] for r in rows}
        assert sections == {
            "Iscrizioni",
            "Presenze",
            "Pasti",
            "Attività",
            "Contributi",
            "Lista d'attesa",
            "Incassi",
        }

    def test_amounts_use_the_decimal_comma_and_the_split_is_filled(self, admin_client, camp):
        _header, *rows = parse(get(admin_client, "csv"))
        due = next(r for r in rows if r[1] == "Totale dovuto")
        assert due[4] == "65,00" and due[2] == "" and due[3] == ""
        morning = next(r for r in rows if r[0] == "Presenze" and r[1] == "13/07/2026 mattina")
        assert morning[2:] == ["1", "1", "2"]

    def test_neither_names_nor_allergy_texts_are_in_the_file(self, admin_client, camp):
        text = get(admin_client, "csv").content.decode("utf-8-sig")
        for word in ("Ada", "Lovelace", "Bob", "Arachidi", "noci", "@example.com"):
            assert word not in text
        allergies = next(r for r in parse(get(admin_client, "csv"))[1:] if "allergie" in r[1])
        assert allergies[4] == "1"


class TestAccessAndEmpty:
    def test_an_edition_without_data_is_all_zeros(self, admin_client, edition):
        report = get(admin_client).json()
        assert report["revenue"]["due_cents"] == 0 and report["revenue"]["net_cents"] == 0
        assert report["enrollment"]["people_with_seat"] == 0
        assert report["presence"]["peak"] == 0
        assert all(s["present"]["total"] == 0 for s in report["presence"]["slots"])
        assert report["activities"] == []
        header, *rows = parse(get(admin_client, "csv"))
        assert header and rows

    def test_without_an_edition_it_does_not_fail(self, admin_client):
        report = get(admin_client).json()
        assert report["edition"] is None
        assert report["presence"]["slots"] == [] and report["revenue"]["due_cents"] == 0

    def test_a_participant_gets_403(self, client, outbox, make_participant, edition):
        make_participant("ada@example.com")
        login(client, outbox)
        assert get(client).status_code == 403
        assert get(client, "csv").status_code == 403

    def test_an_anonymous_visitor_is_refused(self, client, edition):
        assert get(client).status_code == 401
