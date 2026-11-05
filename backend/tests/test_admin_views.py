import csv
import io
from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    STATUS_REFUNDED,
    Slot,
)
from tests.test_auth import login


def slot(db, day, period="morning"):
    return db.scalar(select(Slot).where(Slot.date == date(2026, 7, day), Slot.period == period))


def parse(response):
    return list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))


@pytest.fixture
def camp(db, edition, make_participant, make_booking, admin_client, clock):
    """Monday 13 July: a mix of bookings, some of which must not count as present."""

    def person(email, first, last):
        return make_participant(email, first_name=first, last_name=last)

    def book(who, slots, **kw):
        return make_booking(
            who, [slot(db, 13, p) if isinstance(p, str) else p for p in slots], **kw
        )

    ada = book(person("ada@example.com", "Ada", "Lovelace"), ["morning", "afternoon"])
    bob = book(person("bob@example.com", "Bob", "Builder"), ["evening"], status=STATUS_CONFIRMED)
    eve = book(person("eve@example.com", "Eve", "Adams"), ["morning"], status=STATUS_CONFIRMED)
    cara = book(person("cara@example.com", "Cara", "Expired"), ["morning"], status=STATUS_EXPIRED)
    dan = book(
        person("dan@example.com", "Dan", "Cancelled"), ["morning"], status=STATUS_CANCEL_REQUESTED
    )
    fay = book(person("fay@example.com", "Fay", "Refunded"), ["morning"], status=STATUS_REFUNDED)
    late = book(
        person("late@example.com", "Lia", "Late"),
        ["morning"],
        status=STATUS_PENDING,
        hold_expires_at=clock() - timedelta(minutes=1),
    )
    return dict(ada=ada, bob=bob, eve=eve, cara=cara, dan=dan, fay=fay, late=late)


def day_slots(response, day="2026-07-13"):
    days = {d["date"]: d for d in response.json()["days"]}
    return {s["period"]: s for s in days[day]["slots"]}


class TestSlotsView:
    def test_lists_every_day_and_slot_of_the_edition_even_when_empty(self, admin_client, edition):
        days = admin_client.get("/api/admin/views/slots").json()["days"]
        assert [d["date"] for d in days] == [f"2026-07-{n}" for n in range(13, 18)]
        assert all(
            [s["period"] for s in d["slots"]] == ["morning", "afternoon", "evening"] for d in days
        )
        assert all(s["present"] == 0 for d in days for s in d["slots"])

    def test_counts_capacity_and_free_seats(self, admin_client, camp):
        slots = day_slots(admin_client.get("/api/admin/views/slots"))
        assert (
            slots["morning"]["capacity"],
            slots["morning"]["present"],
            slots["morning"]["free"],
        ) == (25, 2, 23)
        assert (slots["afternoon"]["present"], slots["afternoon"]["free"]) == (1, 24)

    def test_names_are_listed_by_surname(self, admin_client, camp):
        morning = day_slots(admin_client.get("/api/admin/views/slots"))["morning"]
        assert [p["last_name"] for p in morning["people"]] == ["Adams", "Lovelace"]
        assert morning["people"][0]["email"] == "eve@example.com"

    def test_expired_cancelled_refunded_and_overdue_holds_are_not_present(self, admin_client, camp):
        morning = day_slots(admin_client.get("/api/admin/views/slots"))["morning"]
        names = {p["last_name"] for p in morning["people"]}
        assert names.isdisjoint({"Expired", "Cancelled", "Refunded", "Late"})

    def test_the_evening_includes_whoever_booked_the_whole_day_marked_as_derived(
        self, admin_client, camp
    ):
        evening = day_slots(admin_client.get("/api/admin/views/slots"))["evening"]
        by_name = {p["last_name"]: p for p in evening["people"]}
        assert set(by_name) == {"Builder", "Lovelace"}
        assert by_name["Lovelace"]["derived"] is True
        assert by_name["Builder"]["derived"] is False
        assert evening["present"] == 2

    def test_the_evening_has_no_limit(self, admin_client, camp):
        evening = day_slots(admin_client.get("/api/admin/views/slots"))["evening"]
        assert evening["capacity"] is None and evening["free"] is None

    def test_one_daytime_slot_does_not_imply_the_evening(self, admin_client, camp):
        evening = day_slots(admin_client.get("/api/admin/views/slots"))["evening"]
        assert "Adams" not in {p["last_name"] for p in evening["people"]}

    def test_other_days_are_untouched(self, admin_client, camp):
        assert (
            day_slots(admin_client.get("/api/admin/views/slots"), "2026-07-14")["morning"][
                "present"
            ]
            == 0
        )

    def test_csv_has_one_row_per_slot_and_person(self, admin_client, camp):
        response = admin_client.get("/api/admin/views/slots?format=csv")
        assert (
            response.headers["content-disposition"]
            == 'attachment; filename="giorni-slot-2026-07-01.csv"'
        )
        header, *rows = parse(response)
        assert header == [
            "Giorno",
            "Slot",
            "Orario",
            "Nome",
            "Cognome",
            "Email",
            "Stato",
            "Sera derivata",
        ]
        assert len(rows) == 2 + 1 + 2  # morning, afternoon, evening
        ada_evening = next(r for r in rows if r[3] == "Ada" and r[1] == "Sera")
        assert ada_evening[0] == "13/07/2026"
        assert ada_evening[2] == "19:00-00:00"
        assert ada_evening[6] == "In attesa di pagamento"
        assert ada_evening[7] == "sì"
        bob = next(r for r in rows if r[3] == "Bob")
        assert (bob[6], bob[7]) == ("Confermata", "no")

    def test_admins_only(self, client, outbox, make_participant, edition):
        assert client.get("/api/admin/views/slots").status_code == 401
        make_participant("ada@example.com")
        login(client, outbox)
        assert client.get("/api/admin/views/slots").status_code == 403
        assert client.get("/api/admin/views/slots?format=csv").status_code == 403

    def test_without_an_edition_it_is_empty(self, admin_client):
        assert admin_client.get("/api/admin/views/slots").json() == {"days": []}
