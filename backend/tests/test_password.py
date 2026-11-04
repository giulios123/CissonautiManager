from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import create_app
from app.models import ROLE_ADMIN, Participant
from app.services.passwords import hash_password, verify_password
from tests.test_auth import login

GOOD = "correct horse battery"


def test_hash_and_verify():
    stored = hash_password(GOOD)
    assert stored != GOOD
    assert verify_password(stored, GOOD)
    assert not verify_password(stored, "wrong password!!")


def test_verify_without_stored_hash_is_false():
    assert not verify_password(None, GOOD)


def test_verify_with_garbage_hash_is_false():
    assert not verify_password("not-a-hash", GOOD)


def test_set_password_requires_login(client):
    assert client.put("/api/me/password", json={"password": GOOD}).status_code == 401


def test_short_password_is_rejected(client, outbox, make_participant):
    make_participant("ada@example.com")
    login(client, outbox)
    assert client.put("/api/me/password", json={"password": "short"}).status_code == 422
    assert client.get("/api/me").json()["has_password"] is False


def test_set_password_then_login_with_it(client, outbox, db, make_participant):
    make_participant("ada@example.com")
    login(client, outbox)
    assert client.put("/api/me/password", json={"password": GOOD}).status_code == 204
    assert client.get("/api/me").json()["has_password"] is True
    stored = db.scalar(select(Participant.password_hash))
    assert stored and GOOD not in stored

    fresh = TestClient(client.app, base_url="https://testserver")
    response = fresh.post("/api/auth/login", json={"email": "ada@example.com", "password": GOOD})
    assert response.status_code == 200
    assert response.json()["redirect"] == "/io"
    assert fresh.get("/api/me").status_code == 200
    assert "csc_session" in response.headers["set-cookie"]


def test_wrong_unknown_and_missing_password_give_the_same_error(client, make_participant):
    make_participant("with@example.com", password_hash=hash_password(GOOD))
    make_participant("without@example.com")
    attempts = [
        {"email": "with@example.com", "password": "wrong password!!"},
        {"email": "without@example.com", "password": GOOD},
        {"email": "nobody@example.com", "password": GOOD},
    ]
    responses = [client.post("/api/auth/login", json=a) for a in attempts]
    assert {r.status_code for r in responses} == {401}
    assert len({r.text for r in responses}) == 1
    assert client.get("/api/me").status_code == 401


def test_admin_login_with_password_goes_to_admin_panel(client, make_participant):
    make_participant("boss@example.com", role=ROLE_ADMIN, password_hash=hash_password(GOOD))
    response = client.post("/api/auth/login", json={"email": "boss@example.com", "password": GOOD})
    assert response.json() == {"role": ROLE_ADMIN, "redirect": "/admin"}


def test_admin_password_from_env_lets_first_admin_in(settings, engine):
    settings.admin_email = "boss@example.com"
    settings.admin_password = GOOD
    with TestClient(create_app(settings), base_url="https://testserver") as client:
        response = client.post(
            "/api/auth/login", json={"email": "boss@example.com", "password": GOOD}
        )
    assert response.status_code == 200


def test_admin_password_from_env_does_not_overwrite_chosen_password(settings, engine, db):
    settings.admin_email = "boss@example.com"
    settings.admin_password = "initial password from env"
    with TestClient(create_app(settings)):
        pass
    admin = db.scalar(select(Participant))
    admin.password_hash = hash_password("the one the admin chose")
    db.commit()
    with TestClient(create_app(settings)):
        pass
    db.expire_all()
    assert verify_password(db.scalar(select(Participant.password_hash)), "the one the admin chose")
