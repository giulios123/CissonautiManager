from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import STATUS_CONFIRMED, STATUS_EXPIRED, STATUS_PENDING, BookingMeal, Slot
from app.services.amounts import recompute_amount
from tests.helpers import d
from tests.test_auth import login
from tests.test_change_slots import pay


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


@pytest.fixture
def ada(make_participant):
    return make_participant("ada@example.com")


@pytest.fixture
def booking(db, ada, make_booking):
    """Monday morning and Tuesday evening: lunch on Monday, dinner on Tuesday."""
    return make_booking(ada, [slot(db, 13), slot(db, 14, "evening")], amount_due_cents=1200)


@pytest.fixture
def member(client, outbox, booking):
    login(client, outbox)
    outbox.sent.clear()
    return client


def put(client, *meals):
    return client.put(
        "/api/me/booking/meals",
        json={"meals": [{"date": f"2026-07-{day}", "kind": kind} for day, kind in meals]},
    )


def test_me_lists_allowed_meals_and_prices(member):
    data = member.get("/api/me").json()
    assert (data["lunch_price_cents"], data["dinner_price_cents"]) == (800, 1200)
    allowed = data["bookings"][0]["allowed_meals"]
    assert [(m["date"], m["kind"], m["label"]) for m in allowed] == [
        ("2026-07-13", "lunch", "pranzo di lun 13/07"),
        ("2026-07-14", "dinner", "cena di mar 14/07"),
    ]
    assert data["bookings"][0]["meals"] == []


def test_included_meal_is_reflected_on_selected_and_allowed_views(member, db, booking, edition):
    edition.confirmation_policy = "registration_fee"
    edition.included_meal_policy = "first_organizer_meal"
    booking.meals = [BookingMeal(date=d(13), kind="lunch")]
    recompute_amount(edition, booking)
    db.commit()

    response = member.get("/api/me").json()["bookings"][0]
    selected = response["meals"][0]
    allowed = response["allowed_meals"][0]
    assert selected["included_in_fee"] is True
    assert selected["collectable_cents"] == 0
    assert allowed["included_in_fee"] is True
    assert allowed["price_cents"] == 800
    assert allowed["collectable_cents"] == 0


def test_server_preview_uses_included_meal_calculation_without_saving(member, db, booking, edition):
    edition.confirmation_policy = "registration_fee"
    edition.included_meal_policy = "first_organizer_meal"
    booking.meals = [BookingMeal(date=d(13), kind="lunch")]
    recompute_amount(edition, booking)
    db.commit()

    response = member.post(
        "/api/me/booking/meals/preview",
        json={"meals": [{"date": "2026-07-14", "kind": "dinner"}]},
    )
    assert response.status_code == 200
    assert response.json() == {
        "registration_fee_cents": 1200,
        "amount_due_cents": 1200,
        "included_meals": [["2026-07-14", "dinner"]],
    }
    db.refresh(booking)
    assert {(meal.date, meal.kind) for meal in booking.meals} == {(d(13), "lunch")}


def test_joining_meals_updates_the_amount(member, db, booking):
    response = put(member, (13, "lunch"), (14, "dinner"))
    assert response.status_code == 200
    body = response.json()
    assert [m["label"] for m in body["meals"]] == ["pranzo di lun 13/07", "cena di mar 14/07"]
    assert body["amount_due_cents"] == 1200 + 800 + 1200
    assert body["status"] == STATUS_PENDING
    old_deadline = booking.hold_expires_at
    db.refresh(booking)
    assert booking.hold_expires_at == old_deadline


def test_leaving_a_meal_lowers_the_amount(member):
    put(member, (13, "lunch"), (14, "dinner"))
    body = put(member, (14, "dinner")).json()
    assert body["amount_due_cents"] == 1200 + 1200


def test_pending_booking_covered_by_payments_becomes_confirmed(member, db, booking, outbox):
    put(member, (13, "lunch"))
    pay(db, booking, 1200)
    outbox.sent.clear()
    body = put(member).json()
    assert body["status"] == STATUS_CONFIRMED
    assert [m.subject for m in outbox.sent] == [
        "Pagamento ricevuto: sei dentro al Cissonauti Summer Camp 2026!"
    ]


def test_confirmed_booking_stays_confirmed_with_a_balance(member, db, booking):
    pay(db, booking, 1200)
    booking.status = STATUS_CONFIRMED
    db.commit()
    body = put(member, (13, "lunch")).json()
    assert body["status"] == STATUS_CONFIRMED
    assert body["balance_cents"] == 800


def test_meal_without_presence_is_refused(member):
    response = put(member, (13, "dinner"))
    assert response.status_code == 422
    assert "presente" in response.json()["detail"]


def test_past_day_refused_but_today_allowed(member, db, booking, clock):
    booking.status = STATUS_CONFIRMED
    db.commit()
    clock.advance(days=13)  # 14 July in Rome
    assert put(member, (14, "dinner")).status_code == 200
    response = put(member, (13, "lunch"), (14, "dinner"))
    assert response.status_code == 422
    assert "passati" in response.json()["detail"]


def test_expired_booking_cannot_change_meals(member, db, booking, clock):
    booking.status = STATUS_EXPIRED
    booking.hold_expires_at = clock() - timedelta(hours=1)
    db.commit()
    assert put(member, (13, "lunch")).status_code == 409


def test_unknown_meal_kind_is_rejected(member):
    response = member.put(
        "/api/me/booking/meals", json={"meals": [{"date": "2026-07-13", "kind": "breakfast"}]}
    )
    assert response.status_code == 422


def test_cancelling_without_payments_removes_the_meals(member, db, booking):
    put(member, (13, "lunch"))
    assert member.post("/api/me/booking/cancel").json()["outcome"] == "removed"
    from app.models import BookingMeal

    assert db.scalar(select(BookingMeal)) is None
