from app.models import Edition


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
