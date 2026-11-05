from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import STATUS_CONFIRMED, STATUS_EXPIRED, Activity, Slot
from app.services.activities import activities_for_update
from tests.helpers import d
from tests.test_auth import login
from tests.test_change_slots import pay


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


@pytest.fixture
def ada(make_participant):
    return make_participant("ada@example.com")


@pytest.fixture
def booking(db, ada, make_booking):
    """Monday morning and afternoon (so the evening too), Tuesday morning."""
    return make_booking(
        ada, [slot(db, 13), slot(db, 13, "afternoon"), slot(db, 14)], amount_due_cents=1200
    )


@pytest.fixture
def member(client, outbox, booking):
    login(client, outbox)
    outbox.sent.clear()
    return client


def put(client, *activities):
    return client.put(
        "/api/me/booking/activities", json={"activity_ids": [a.id for a in activities]}
    )


def test_me_offers_only_activities_where_i_am_present(member, db, edition):
    activity(db, edition, "Escursione", 14, "morning", 1500, 2)
    activity(db, edition, "Quiz", 13, "evening")
    activity(db, edition, "Yoga", 14, "evening")
    offers = member.get("/api/me").json()["activities"]
    assert [(o["title"], o["free"], o["joined"]) for o in offers] == [
        ("Quiz", None, False),
        ("Escursione", 2, False),
    ]


def test_joining_a_paid_activity_raises_the_amount(member, db, edition, booking):
    hike = activity(db, edition, "Escursione", 14, "morning", 1500, 2)
    response = put(member, hike)
    assert response.status_code == 200
    body = response.json()
    assert body["amount_due_cents"] == 1200 + 1500
    assert [a["label"] for a in body["activities"]] == ["Escursione (mar 14/07 mattina)"]
    offers = member.get("/api/me").json()["activities"]
    assert (offers[0]["joined"], offers[0]["free"]) == (True, 1)


def test_leaving_lowers_the_amount_and_frees_the_seat(member, db, edition):
    hike = activity(db, edition, "Escursione", 14, "morning", 1500, 2)
    put(member, hike)
    body = put(member).json()
    assert body["amount_due_cents"] == 1200
    assert member.get("/api/me").json()["activities"][0]["free"] == 2


def test_a_full_activity_is_refused(member, db, edition, make_participant, make_booking):
    hike = activity(db, edition, "Escursione", 14, "morning", 0, 1)
    other = make_booking(make_participant("bob@example.com"), [slot(db, 14)])
    other.activities = [hike]
    db.commit()
    response = put(member, hike)
    assert response.status_code == 409
    assert "al completo: Escursione" in response.json()["detail"]


def test_seats_of_expired_bookings_do_not_count(
    member, db, edition, make_participant, make_booking, clock
):
    hike = activity(db, edition, "Escursione", 14, "morning", 0, 1)
    other = make_booking(
        make_participant("bob@example.com"),
        [slot(db, 14)],
        status=STATUS_EXPIRED,
        hold_expires_at=clock() - timedelta(hours=1),
    )
    other.activities = [hike]
    db.commit()
    assert put(member, hike).status_code == 200


def test_without_presence_joining_is_refused(member, db, edition):
    yoga = activity(db, edition, "Yoga", 14, "evening")
    response = put(member, yoga)
    assert response.status_code == 422
    assert "presente" in response.json()["detail"]


def test_pending_booking_covered_becomes_confirmed(member, db, edition, booking, outbox):
    hike = activity(db, edition, "Escursione", 14, "morning", 1500)
    put(member, hike)
    pay(db, booking, 1200)
    body = put(member).json()
    assert body["status"] == STATUS_CONFIRMED


def test_past_day_refused_and_today_allowed(member, db, edition, booking, clock):
    booking.status = STATUS_CONFIRMED
    db.commit()
    monday = activity(db, edition, "Quiz", 13, "evening")
    tuesday = activity(db, edition, "Escursione", 14, "morning")
    clock.advance(days=13)  # 14 July
    assert put(member, monday).status_code == 422
    assert put(member, tuesday).status_code == 200


def test_unknown_activity_is_rejected(member):
    response = member.put("/api/me/booking/activities", json={"activity_ids": [99999]})
    assert response.status_code == 422


def test_activity_rows_are_locked_on_sql_server():
    sql = str(activities_for_update([1], 1).compile(dialect=_mssql()))
    assert "UPDLOCK" in sql


def _mssql():
    from sqlalchemy.dialects import mssql

    return mssql.dialect()


def test_reactivation_locks_the_activity_rows(
    monkeypatch, db, edition, make_participant, make_booking, clock
):
    """Reactivation counts activity seats under the same row locks as a sign-up."""
    from app.services import payments

    calls = []
    original = payments.activities_for_update

    def spy(ids, edition_id):
        calls.append(list(ids))
        return original(ids, edition_id)

    monkeypatch.setattr(payments, "activities_for_update", spy)
    hike = activity(db, edition, "Escursione", 13, "morning", 0, 2)
    booking = make_booking(
        make_participant("ada@example.com"),
        [slot(db, 13)],
        status=STATUS_EXPIRED,
        hold_expires_at=clock() - timedelta(hours=1),
    )
    booking.activities = [hike]
    db.commit()
    assert payments.revive_expired(db, booking, clock()) == payments.REVIVED
    assert calls == [[hike.id]]
