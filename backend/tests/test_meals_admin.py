from sqlalchemy import select

from app.models import STATUS_CONFIRMED, AuditLog, Slot
from tests.helpers import d
from tests.test_auth import login


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


def put(client, booking_id, *meals):
    return client.put(
        f"/api/admin/registrations/{booking_id}/meals",
        json={"meals": [{"date": f"2026-07-{day}", "kind": kind} for day, kind in meals]},
    )


def test_admin_changes_meals_even_on_past_days_with_history(
    admin_client, db, make_participant, make_booking, clock
):
    ada = make_participant("ada@example.com")
    booking = make_booking(ada, [slot(db, 13), slot(db, 13, "evening")], status=STATUS_CONFIRMED)
    clock.advance(days=13)  # 14 July: Monday is over
    response = put(admin_client, booking.id, (13, "lunch"), (13, "dinner"))
    assert response.status_code == 200
    detail = response.json()
    assert [m["label"] for m in detail["booking"]["meals"]] == [
        "pranzo di lun 13/07",
        "cena di lun 13/07",
    ]
    assert detail["booking"]["amount_due_cents"] == 1100 + 800 + 1200
    assert (detail["lunch_price_cents"], detail["dinner_price_cents"]) == (800, 1200)
    log = db.scalar(select(AuditLog).where(AuditLog.action == "meals_changed"))
    assert "Aggiunti: pranzo di lun 13/07, cena di lun 13/07." in log.detail


def test_presence_is_required_for_admins_too(admin_client, db, make_participant, make_booking):
    booking = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    response = put(admin_client, booking.id, (13, "dinner"))
    assert response.status_code == 422
    assert "aggiungi prima lo slot" in response.json()["detail"]


def test_admin_sees_diet_and_allergies(admin_client, db, make_participant, make_booking):
    booking = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    booking.diet, booking.allergies = "vegan", "Arachidi"
    db.commit()
    view = admin_client.get(f"/api/admin/registrations/{booking.id}").json()["booking"]
    assert (view["diet"], view["allergies"]) == ("vegan", "Arachidi")


def test_participants_cannot_use_the_admin_endpoint(
    client, outbox, db, make_participant, make_booking
):
    booking = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    login(client, outbox)
    assert put(client, booking.id, (13, "lunch")).status_code == 403
