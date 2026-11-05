from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models import ROLE_ADMIN, ROLE_PARTICIPANT, AuditLog, Booking, Participant, Slot
from app.services.passwords import hash_password
from tests.test_auth import login


@pytest.fixture
def seed(app):
    """boss@example.com is the admin set by ADMIN_EMAIL."""
    app.state.settings.admin_email = "boss@example.com"


@pytest.fixture
def second_client(app, make_participant) -> TestClient:
    """A second admin, already signed in."""
    make_participant(
        "second@example.com",
        role=ROLE_ADMIN,
        first_name="Second",
        last_name="Admin",
        password_hash=hash_password("second-password-1"),
    )
    client = TestClient(app, base_url="https://testserver")
    response = client.post(
        "/api/auth/login", json={"email": "second@example.com", "password": "second-password-1"}
    )
    assert response.status_code == 200
    return client


def by_email(client):
    return {a["email"]: a for a in client.get("/api/admin/admins").json()}


def add(client, email, **names):
    return client.post("/api/admin/admins", json={"email": email, **names})


def test_list_shows_admins_and_marks_the_one_you_are(admin_client):
    admins = by_email(admin_client)
    assert list(admins) == ["boss@example.com"]
    assert admins["boss@example.com"]["is_you"] is True


def test_you_and_the_seed_admin_cannot_be_removed_and_the_list_says_why(
    admin_client, second_client, seed
):
    mine = by_email(admin_client)["boss@example.com"]
    assert mine["removable"] is False
    assert "te stesso" in mine["blocked_reason"]
    seen_by_second = by_email(second_client)
    assert seen_by_second["boss@example.com"]["removable"] is False
    assert "ADMIN_EMAIL" in seen_by_second["boss@example.com"]["blocked_reason"]
    assert seen_by_second["second@example.com"]["is_you"] is True
    assert by_email(admin_client)["second@example.com"]["removable"] is True


def test_a_registered_person_is_promoted_and_keeps_their_booking(
    admin_client, client, outbox, db, edition, make_participant, make_booking, slot_ids
):
    ada = make_participant("ada@example.com", first_name="Ada", last_name="Lovelace")
    make_booking(ada, [db.get(Slot, slot_ids[(date(2026, 7, 13), "morning")])])
    response = add(admin_client, "ada@example.com")
    assert response.status_code == 201
    assert response.json()["created"] is False
    assert response.json()["first_name"] == "Ada"
    db.expire_all()
    assert db.get(Participant, ada.id).role == ROLE_ADMIN
    assert db.scalar(select(Booking).where(Booking.participant_id == ada.id)) is not None
    login(client, outbox)  # she signs in with her usual link and now reaches the panel
    assert client.get("/api/admin/registrations").status_code == 200


def test_the_email_is_matched_ignoring_case_and_spaces(admin_client, make_participant, db):
    ada = make_participant("ada@example.com")
    assert add(admin_client, "  ADA@Example.com ").json()["created"] is False
    db.expire_all()
    assert db.get(Participant, ada.id).role == ROLE_ADMIN


def test_a_new_person_needs_a_name_and_can_then_sign_in_as_admin(admin_client, client, outbox, db):
    refused = add(admin_client, "newbie@example.com")
    assert refused.status_code == 422
    assert "nome e cognome" in refused.json()["detail"]
    assert (
        add(admin_client, "newbie@example.com", first_name="Nina", last_name="").status_code == 422
    )
    assert db.scalar(select(Participant).where(Participant.email == "newbie@example.com")) is None

    created = add(admin_client, "Newbie@Example.com", first_name=" Nina ", last_name="Newbie")
    assert created.status_code == 201
    assert created.json()["created"] is True
    person = db.scalar(select(Participant).where(Participant.email == "newbie@example.com"))
    assert (person.first_name, person.last_name, person.role) == ("Nina", "Newbie", ROLE_ADMIN)
    assert person.personal_code.startswith("CSC-")
    login(client, outbox, email="newbie@example.com")
    assert client.get("/api/admin/admins").status_code == 200


def test_adding_someone_who_is_already_admin_is_refused(admin_client, second_client):
    response = add(admin_client, "second@example.com")
    assert response.status_code == 409
    assert "già admin" in response.json()["detail"]


def test_an_invalid_email_is_refused(admin_client):
    assert add(admin_client, "not-an-email").status_code == 422


def test_there_is_no_limit_to_the_number_of_admins(admin_client):
    for n in range(5):
        assert (
            add(
                admin_client, f"extra{n}@example.com", first_name="Extra", last_name=str(n)
            ).status_code
            == 201
        )
    assert len(by_email(admin_client)) == 6


def test_removing_an_admin_keeps_the_person_and_their_booking(
    admin_client, second_client, db, edition, make_booking, slot_ids
):
    second = db.scalar(select(Participant).where(Participant.email == "second@example.com"))
    booking = make_booking(second, [db.get(Slot, slot_ids[(date(2026, 7, 13), "morning")])])
    assert admin_client.delete(f"/api/admin/admins/{second.id}").status_code == 204
    db.expire_all()
    assert db.get(Participant, second.id).role == ROLE_PARTICIPANT
    assert db.get(Booking, booking.id) is not None
    assert "second@example.com" not in by_email(admin_client)


def test_a_removed_admin_loses_access_at_once_even_with_a_session_open(
    admin_client, second_client, db
):
    assert second_client.get("/api/admin/registrations").status_code == 200
    second = db.scalar(select(Participant).where(Participant.email == "second@example.com"))
    admin_client.delete(f"/api/admin/admins/{second.id}")
    assert second_client.get("/api/admin/registrations").status_code == 403
    assert second_client.get("/api/me").status_code == 200  # still a normal participant


def test_you_cannot_remove_yourself(admin_client, second_client, db):
    boss = db.scalar(select(Participant).where(Participant.email == "boss@example.com"))
    response = admin_client.delete(f"/api/admin/admins/{boss.id}")
    assert response.status_code == 409
    assert "te stesso" in response.json()["detail"]
    db.expire_all()
    assert db.get(Participant, boss.id).role == ROLE_ADMIN


def test_the_seed_admin_cannot_be_removed_by_another_admin(admin_client, second_client, seed, db):
    boss = db.scalar(select(Participant).where(Participant.email == "boss@example.com"))
    response = second_client.delete(f"/api/admin/admins/{boss.id}")
    assert response.status_code == 409
    assert "ADMIN_EMAIL" in response.json()["detail"]


def test_removing_someone_who_is_not_an_admin_or_does_not_exist_is_404(
    admin_client, make_participant
):
    ada = make_participant("ada@example.com")
    assert admin_client.delete(f"/api/admin/admins/{ada.id}").status_code == 404
    assert admin_client.delete("/api/admin/admins/99999").status_code == 404


def test_adding_and_removing_leave_a_trace(admin_client, db):
    add(admin_client, "newbie@example.com", first_name="Nina", last_name="Newbie")
    person = db.scalar(select(Participant).where(Participant.email == "newbie@example.com"))
    admin_client.delete(f"/api/admin/admins/{person.id}")
    entries = db.scalars(select(AuditLog).order_by(AuditLog.id)).all()
    assert [e.action for e in entries] == ["admin_added", "admin_removed"]
    assert "newbie@example.com" in entries[0].detail
    assert "newbie@example.com" in entries[1].detail
    boss = db.scalar(select(Participant).where(Participant.email == "boss@example.com"))
    assert all(e.actor_id == boss.id and e.booking_id is None for e in entries)


def test_only_admins_can_manage_admins(client, outbox, make_participant):
    assert client.get("/api/admin/admins").status_code == 401
    assert add(client, "x@example.com").status_code == 401
    assert client.delete("/api/admin/admins/1").status_code == 401
    make_participant("ada@example.com")
    login(client, outbox)
    assert client.get("/api/admin/admins").status_code == 403
    assert add(client, "x@example.com").status_code == 403
    assert client.delete("/api/admin/admins/1").status_code == 403
