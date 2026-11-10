from datetime import timedelta

from sqlalchemy import select

from app.models import STATUS_CONFIRMED, STATUS_EXPIRED, Slot
from tests.helpers import d
from tests.test_activities_me import activity
from tests.test_auth import login
from tests.test_guests_views import add_guest, eat

DETAIL = "/api/admin/views/week/detail"
CELLS = {
    "morning": "morning",
    "afternoon": "afternoon",
    "evening": "evening",
    "people": "people",
    "lunch": "lunches",
    "dinner": "dinners",
    "activities": "activities",
}


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


def detail(client, metric, day=None):
    params = {"metric": metric}
    if day is not None:
        params["date"] = f"2026-07-{day}"
    response = client.get(DETAIL, params=params)
    assert response.status_code == 200, response.text
    return response.json()


def populate(admin_client, db, edition, make_participant, make_booking, clock):
    ada = make_booking(
        make_participant("ada@example.com", first_name="Ada", last_name="Lovelace"),
        [slot(db, 13, "morning"), slot(db, 13, "afternoon"), slot(db, 14)],
        status=STATUS_CONFIRMED,
    )
    bob = make_booking(
        make_participant("bob@example.com", first_name="Bob", last_name="Bianchi"),
        [slot(db, 13, "morning")],
    )
    make_booking(
        make_participant("old@example.com", first_name="Old", last_name="Expired"),
        [slot(db, 13, "morning")],
        status=STATUS_EXPIRED,
        hold_expires_at=clock() - timedelta(minutes=1),
    )
    eat(db, ada, 13, "lunch")
    eat(db, bob, 13, "lunch")
    hike = activity(db, edition, "Escursione", 13, "morning")
    yoga = activity(db, edition, "Yoga", 14, "morning")
    ada.activities = [hike, yoga]
    bob.activities = [hike]
    db.commit()
    add_guest(
        admin_client, "Anna", "Rossi", [(13, "lunch"), (13, "dinner")], activity_ids=[hike.id]
    )


def test_every_detail_matches_its_cell_of_the_week(
    admin_client, db, edition, make_participant, make_booking, clock
):
    populate(admin_client, db, edition, make_participant, make_booking, clock)
    week = admin_client.get("/api/admin/views/week").json()
    for day in week["days"]:
        for metric, cell in CELLS.items():
            result = detail(admin_client, metric, day["date"][-2:])
            assert result["count"] == day[cell], (day["date"], metric)
            assert len(result["rows"]) == day[cell]
    totals = {
        "people": week["total_people"],
        "lunch": week["total_lunches"],
        "dinner": week["total_dinners"],
        "activities": week["total_activities"],
    }
    for metric, total in totals.items():
        result = detail(admin_client, metric)
        assert result["date"] is None
        assert result["count"] == total


def test_the_derived_evening_is_marked(
    admin_client, db, edition, make_participant, make_booking, clock
):
    populate(admin_client, db, edition, make_participant, make_booking, clock)
    rows = detail(admin_client, "evening", "13")["rows"]
    assert [(r["name"], r["derived"]) for r in rows] == [("Ada Lovelace", True)]


def test_people_are_counted_once_and_expired_ones_are_left_out(
    admin_client, db, edition, make_participant, make_booking, clock
):
    populate(admin_client, db, edition, make_participant, make_booking, clock)
    monday = detail(admin_client, "people", "13")
    assert sorted(r["name"] for r in monday["rows"]) == ["Ada Lovelace", "Bob Bianchi"]
    week = detail(admin_client, "people")
    assert week["count"] == 2
    assert all(r["booking_id"] for r in week["rows"])


def test_meals_include_the_external_guests(
    admin_client, db, edition, make_participant, make_booking, clock
):
    populate(admin_client, db, edition, make_participant, make_booking, clock)
    rows = detail(admin_client, "lunch", "13")["rows"]
    assert [(r["name"], r["external"]) for r in rows] == [
        ("Ada Lovelace", False),
        ("Anna Rossi", True),
        ("Bob Bianchi", False),
    ]
    guest = next(r for r in rows if r["external"])
    assert guest["guest_id"] and guest["booking_id"] is None


def test_activities_count_sign_ups_and_distinct_people(
    admin_client, db, edition, make_participant, make_booking, clock
):
    populate(admin_client, db, edition, make_participant, make_booking, clock)
    week = detail(admin_client, "activities")
    # Ada is in two activities, Bob and the guest in one each.
    assert week["count"] == 4
    assert week["distinct_people"] == 3
    titles = sorted((r["name"], r["activity_title"]) for r in week["rows"])
    assert ("Ada Lovelace", "Escursione") in titles and ("Ada Lovelace", "Yoga") in titles
    assert detail(admin_client, "activities", "14")["count"] == 1


def test_a_day_without_anyone_is_empty(admin_client, db, edition):
    result = detail(admin_client, "lunch", "15")
    assert (result["count"], result["rows"]) == (0, [])


def test_no_contact_or_health_data_in_the_rows(
    admin_client, db, edition, make_participant, make_booking, clock
):
    populate(admin_client, db, edition, make_participant, make_booking, clock)
    admin_client.get("/api/admin/views/week")
    for metric in CELLS:
        for row in detail(admin_client, metric)["rows"]:
            assert not {"email", "phone", "diet", "allergies", "amount_due_cents"} & row.keys()
    assert "example.com" not in admin_client.get(DETAIL, params={"metric": "lunch"}).text


def test_invalid_input_is_refused(admin_client, edition):
    assert admin_client.get(DETAIL, params={"metric": "nothing"}).status_code == 422
    assert admin_client.get(DETAIL).status_code == 422
    bad = admin_client.get(DETAIL, params={"metric": "lunch", "date": "2030-01-01"})
    assert bad.status_code == 422


def test_admins_only(client, outbox, make_participant, edition):
    assert client.get(DETAIL, params={"metric": "lunch"}).status_code == 401
    make_participant("ada@example.com")
    login(client, outbox)
    assert client.get(DETAIL, params={"metric": "lunch"}).status_code == 403


def test_signups_of_the_week_use_the_same_list_as_the_count(
    admin_client, db, edition, make_participant, make_booking, clock
):
    from app.services import views as views_service

    populate(admin_client, db, edition, make_participant, make_booking, clock)
    now = clock()
    signups = views_service.activity_signups(db, now)
    assert sorted(views_service.activity_signup_days(db, now)) == sorted(s.day for s in signups)
