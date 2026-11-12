"""MVP 31: the day lists of Week, Days and slots and Meals come ordered today-first on screen;
the CSV files stay chronological."""

import csv
import io
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.models import STATUS_CONFIRMED, Slot
from tests.helpers import d

VIEWS = ["week", "slots", "meals"]
CHRONOLOGICAL = ["2026-07-13", "2026-07-14", "2026-07-15", "2026-07-16", "2026-07-17"]


def slot(db, day, period="morning"):
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


def parse(response):
    return list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))


@pytest.fixture
def camp(db, edition, make_participant, make_booking, admin_client):
    ada = make_participant("ada@example.com", first_name="Ada", last_name="Lovelace")
    make_booking(ada, [slot(db, 13), slot(db, 15), slot(db, 17)], status=STATUS_CONFIRMED)
    return admin_client


def at(client, clock, when):
    """Move the clock and sign in again: a session does not last for days."""
    clock.current = when
    response = client.post(
        "/api/auth/login", json={"email": "boss@example.com", "password": "admin-password-1"}
    )
    assert response.status_code == 200


def days(client, view, **params):
    response = client.get(f"/api/admin/views/{view}", params=params)
    assert response.status_code == 200
    body = response.json()
    return [day["date"] for day in body["days"]], body["today"]


@pytest.mark.parametrize("view", VIEWS)
def test_before_the_event_it_is_chronological_and_has_no_today(camp, view):
    assert days(camp, view) == (CHRONOLOGICAL, None)


@pytest.mark.parametrize("view", VIEWS)
def test_during_the_event_today_leads_then_the_future_then_the_past(camp, clock, view):
    at(camp, clock, datetime(2026, 7, 15, 10, 0, tzinfo=UTC))
    assert days(camp, view) == (
        ["2026-07-15", "2026-07-16", "2026-07-17", "2026-07-13", "2026-07-14"],
        "2026-07-15",
    )


@pytest.mark.parametrize("view", VIEWS)
def test_on_the_last_day_and_after_the_event(camp, clock, view):
    at(camp, clock, datetime(2026, 7, 17, 10, 0, tzinfo=UTC))
    assert days(camp, view)[0][0] == "2026-07-17"
    at(camp, clock, datetime(2026, 7, 18, 10, 0, tzinfo=UTC))
    assert days(camp, view) == (CHRONOLOGICAL, None)


@pytest.mark.parametrize("view", VIEWS)
def test_the_day_is_the_one_of_rome_not_of_utc(camp, clock, view):
    # 22:30 UTC on the 14th is already the 15th in Rome.
    at(camp, clock, datetime(2026, 7, 14, 22, 30, tzinfo=UTC))
    assert days(camp, view)[1] == "2026-07-15"
    # Midnight UTC on the 15th is 02:00 in Rome: still the 15th.
    at(camp, clock, datetime(2026, 7, 15, 0, 0, tzinfo=UTC))
    assert days(camp, view)[1] == "2026-07-15"
    # 21:59 UTC on the 14th is 23:59 in Rome: still the 14th.
    at(camp, clock, datetime(2026, 7, 14, 21, 59, tzinfo=UTC))
    assert days(camp, view)[1] == "2026-07-14"


def test_the_numbers_stay_with_their_date(camp, clock):
    before = {day["date"]: day for day in camp.get("/api/admin/views/week").json()["days"]}
    at(camp, clock, datetime(2026, 7, 15, 10, 0, tzinfo=UTC))
    body = camp.get("/api/admin/views/week").json()
    assert {day["date"]: day for day in body["days"]} == before
    assert body["total_people"] == 1
    assert [day["people"] for day in body["days"]] == [1, 0, 1, 1, 0]


@pytest.mark.parametrize("view", VIEWS)
def test_the_csv_is_chronological_whatever_today_is(camp, clock, view):
    def column(response):
        return [row[0] for row in parse(response)[1:] if row[0] and row[0][:2] == "20"]

    at(camp, clock, datetime(2026, 7, 1, 10, 0, tzinfo=UTC))
    before = camp.get(f"/api/admin/views/{view}", params={"format": "csv"})
    at(camp, clock, datetime(2026, 7, 15, 10, 0, tzinfo=UTC))
    during = camp.get(f"/api/admin/views/{view}", params={"format": "csv"})
    assert during.status_code == 200
    # Same content and same order; only the file name has a date, and it is the same day too.
    assert parse(during) == parse(before)
    dates = column(during)
    assert dates == sorted(dates)


@pytest.mark.parametrize("view", VIEWS)
def test_only_admins_see_the_views(client, make_participant, edition, view):
    assert client.get(f"/api/admin/views/{view}").status_code == 401
    make_participant("plain@example.com")
    client.post("/api/auth/login", json={"email": "plain@example.com", "password": "x"})
    assert client.get(f"/api/admin/views/{view}").status_code in (401, 403)


@pytest.mark.parametrize("view", VIEWS)
def test_an_edition_without_dates_is_chronological(camp, db, edition, clock, view):
    edition.start_date = None
    edition.end_date = None
    db.commit()
    at(camp, clock, datetime(2026, 7, 15, 10, 0, tzinfo=UTC))
    assert days(camp, view) == (CHRONOLOGICAL, None)
