from datetime import timedelta

from app.models import STATUS_PENDING, Edition, Slot
from tests.helpers import d
from tests.test_change_slots import pay


def test_included_meal_policy_requires_registration_fee_confirmation(admin_client, edition, db):
    response = admin_client.post(
        "/api/admin/edition/included-meals/preview",
        json={"policy": "first_organizer_meal"},
    )
    assert response.status_code == 409

    edition.confirmation_policy = "registration_fee"
    db.commit()
    response = admin_client.post(
        "/api/admin/edition/included-meals/preview",
        json={"policy": "first_organizer_meal"},
    )
    assert response.status_code == 200
    token = response.json()["preview_token"]
    applied = admin_client.post(
        "/api/admin/edition/included-meals/apply",
        json={"policy": "first_organizer_meal", "preview_token": token},
    )
    assert applied.status_code == 200
    db.refresh(edition)
    assert edition.included_meal_policy == "first_organizer_meal"

    retried = admin_client.post(
        "/api/admin/edition/included-meals/apply",
        json={"policy": "first_organizer_meal", "preview_token": token},
    )
    assert retried.status_code == 200
    assert retried.json()["already_applied"] is True


def test_included_meal_preview_rejects_old_snapshot(admin_client, edition, db):
    edition.confirmation_policy = "registration_fee"
    db.commit()
    preview = admin_client.post(
        "/api/admin/edition/included-meals/preview",
        json={"policy": "first_organizer_meal"},
    ).json()
    edition = db.get(Edition, edition.id)
    edition.base_fee_cents += 100
    db.commit()

    response = admin_client.post(
        "/api/admin/edition/included-meals/apply",
        json={
            "policy": "first_organizer_meal",
            "preview_token": preview["preview_token"],
        },
    )

    assert response.status_code == 409


def test_preview_uses_recalculated_registration_fee_for_confirmation(
    admin_client, edition, db, make_participant, make_booking, clock
):
    slot = db.query(Slot).filter_by(date=d(13), period="morning").one()
    booking = make_booking(make_participant("fee@example.com"), [slot], amount_due_cents=1600)
    edition.confirmation_policy = "registration_fee"
    booking.registration_fee_cents = 500
    db.commit()
    pay(db, booking, 800)

    response = admin_client.post(
        "/api/admin/edition/included-meals/preview",
        json={"policy": "first_organizer_meal"},
    )

    assert response.status_code == 200
    row = next(row for row in response.json()["rows"] if row["booking_id"] == booking.id)
    assert row["registration_fee_cents"] == 1100
    assert row["status_before"] == STATUS_PENDING
    assert row["status_after"] == STATUS_PENDING


def test_preview_fingerprint_changes_when_effective_status_expires(
    admin_client, edition, db, make_participant, make_booking, clock
):
    slot = db.query(Slot).filter_by(date=d(13), period="morning").one()
    make_booking(
        make_participant("expires@example.com"),
        [slot],
        hold_expires_at=clock() + timedelta(days=1),
    )
    edition.confirmation_policy = "registration_fee"
    db.commit()
    first = admin_client.post(
        "/api/admin/edition/included-meals/preview",
        json={"policy": "first_organizer_meal"},
    ).json()

    clock.advance(days=2)
    second = admin_client.post(
        "/api/admin/edition/included-meals/preview",
        json={"policy": "first_organizer_meal"},
    ).json()

    assert second["preview_token"] != first["preview_token"]
