import re

from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.deps import require_admin
from app.main import create_app
from app.models import ROLE_ADMIN, ROLE_PARTICIPANT, Participant


def token_from(outbox) -> str:
    match = re.search(r"token=([\w-]+)", outbox.sent[-1].body)
    assert match, outbox.sent[-1].body
    return match.group(1)


def login(client, outbox, email="ada@example.com") -> None:
    client.post("/api/auth/magic-link", json={"email": email})
    response = client.post("/api/auth/verify", json={"token": token_from(outbox)})
    assert response.status_code == 200


class TestMagicLinkRequest:
    def test_unknown_email_gets_neutral_answer_and_no_email(self, client, outbox):
        response = client.post("/api/auth/magic-link", json={"email": "nobody@example.com"})
        assert response.status_code == 200
        assert outbox.sent == []

    def test_known_and_unknown_email_get_identical_responses(
        self, client, outbox, make_participant
    ):
        make_participant("ada@example.com")
        known = client.post("/api/auth/magic-link", json={"email": "ada@example.com"})
        unknown = client.post("/api/auth/magic-link", json={"email": "nobody@example.com"})
        assert known.status_code == unknown.status_code
        assert known.json() == unknown.json()

    def test_known_email_receives_link_with_token(self, client, outbox, make_participant):
        make_participant("ada@example.com")
        client.post("/api/auth/magic-link", json={"email": "ada@example.com"})
        assert len(outbox.sent) == 1
        assert outbox.sent[0].to == "ada@example.com"
        assert "https://camp.example.org/accedi/verifica?token=" in outbox.sent[0].body

    def test_email_lookup_ignores_case_and_spaces(self, client, outbox, make_participant):
        make_participant("ada@example.com")
        client.post("/api/auth/magic-link", json={"email": "Ada@Example.com"})
        assert len(outbox.sent) == 1

    def test_invalid_email_is_rejected(self, client):
        response = client.post("/api/auth/magic-link", json={"email": "not-an-email"})
        assert response.status_code == 422


class TestVerify:
    def test_valid_token_logs_in_and_sets_cookie(self, client, outbox, make_participant):
        make_participant("ada@example.com")
        client.post("/api/auth/magic-link", json={"email": "ada@example.com"})
        response = client.post("/api/auth/verify", json={"token": token_from(outbox)})
        assert response.status_code == 200
        assert response.json() == {"role": ROLE_PARTICIPANT, "redirect": "/io"}
        cookie = response.headers["set-cookie"].lower()
        assert "csc_session=" in cookie
        assert "httponly" in cookie
        assert "secure" in cookie
        assert "samesite=lax" in cookie
        assert f"max-age={14 * 24 * 3600}" in cookie

    def test_admin_lands_on_their_own_page(self, client, outbox, make_participant):
        make_participant("boss@example.com", role=ROLE_ADMIN)
        client.post("/api/auth/magic-link", json={"email": "boss@example.com"})
        response = client.post("/api/auth/verify", json={"token": token_from(outbox)})
        assert response.json() == {"role": ROLE_ADMIN, "redirect": "/io"}

    def test_token_can_be_reused_until_it_expires(self, client, outbox, clock, make_participant):
        make_participant("ada@example.com")
        client.post("/api/auth/magic-link", json={"email": "ada@example.com"})
        token = token_from(outbox)
        assert client.post("/api/auth/verify", json={"token": token}).status_code == 200
        clock.advance(minutes=5)
        assert client.post("/api/auth/verify", json={"token": token}).status_code == 200

    def test_first_use_is_recorded_once(self, client, outbox, clock, db, make_participant):
        from app.models import MagicLinkToken

        make_participant("ada@example.com")
        client.post("/api/auth/magic-link", json={"email": "ada@example.com"})
        token = token_from(outbox)
        client.post("/api/auth/verify", json={"token": token})
        first = db.scalar(select(MagicLinkToken)).used_at
        clock.advance(minutes=2)
        client.post("/api/auth/verify", json={"token": token})
        db.expire_all()
        assert db.scalar(select(MagicLinkToken)).used_at == first

    def test_token_valid_until_10_minutes(self, client, outbox, clock, make_participant):
        make_participant("ada@example.com")
        client.post("/api/auth/magic-link", json={"email": "ada@example.com"})
        clock.advance(minutes=9, seconds=59)
        response = client.post("/api/auth/verify", json={"token": token_from(outbox)})
        assert response.status_code == 200

    def test_token_expires_after_10_minutes(self, client, outbox, clock, make_participant):
        make_participant("ada@example.com")
        client.post("/api/auth/magic-link", json={"email": "ada@example.com"})
        clock.advance(minutes=10)
        response = client.post("/api/auth/verify", json={"token": token_from(outbox)})
        assert response.status_code == 400

    def test_unknown_token_is_rejected(self, client):
        assert client.post("/api/auth/verify", json={"token": "nope"}).status_code == 400

    def test_tokens_are_stored_hashed(self, client, outbox, db, make_participant):
        make_participant("ada@example.com")
        client.post("/api/auth/magic-link", json={"email": "ada@example.com"})
        from app.models import MagicLinkToken

        stored = db.scalars(select(MagicLinkToken)).all()
        assert token_from(outbox) not in [t.token_hash for t in stored]


class TestSession:
    def test_me_requires_login(self, client):
        assert client.get("/api/me").status_code == 401

    def test_me_after_login(self, client, outbox, make_participant):
        make_participant("ada@example.com")
        login(client, outbox)
        response = client.get("/api/me")
        assert response.status_code == 200
        assert response.json()["email"] == "ada@example.com"

    def test_session_lasts_14_days(self, client, outbox, clock, make_participant):
        make_participant("ada@example.com")
        login(client, outbox)
        clock.advance(days=13, hours=23)
        assert client.get("/api/me").status_code == 200
        clock.advance(hours=2)
        assert client.get("/api/me").status_code == 401

    def test_logout_ends_session(self, client, outbox, make_participant):
        make_participant("ada@example.com")
        login(client, outbox)
        assert client.post("/api/auth/logout").status_code == 204
        assert client.get("/api/me").status_code == 401

    def test_cookie_not_secure_on_plain_http_base_url(
        self, settings, engine, outbox, make_participant
    ):
        settings.app_base_url = "http://localhost:5173"
        app = create_app(settings)
        app.state.email_sender = outbox
        make_participant("ada@example.com")
        http_client = TestClient(app)
        http_client.post("/api/auth/magic-link", json={"email": "ada@example.com"})
        response = http_client.post("/api/auth/verify", json={"token": token_from(outbox)})
        assert "secure" not in response.headers["set-cookie"].lower()


class TestAdminGuard:
    def _client_with_admin_route(self, app) -> TestClient:
        @app.get("/api/admin/ping")
        def ping(_=Depends(require_admin)):
            return {"ok": True}

        return TestClient(app, base_url="https://testserver")

    def test_anonymous_gets_401(self, app):
        assert self._client_with_admin_route(app).get("/api/admin/ping").status_code == 401

    def test_participant_gets_403(self, app, outbox, make_participant):
        make_participant("ada@example.com")
        client = self._client_with_admin_route(app)
        login(client, outbox)
        assert client.get("/api/admin/ping").status_code == 403

    def test_admin_gets_200(self, app, outbox, make_participant):
        make_participant("boss@example.com", role=ROLE_ADMIN)
        client = self._client_with_admin_route(app)
        login(client, outbox, "boss@example.com")
        assert client.get("/api/admin/ping").status_code == 200


class TestAdminSeed:
    def test_admin_is_created_from_env(self, settings, engine, db):
        settings.admin_email = "Boss@Example.com"
        with TestClient(create_app(settings)):
            pass
        admin = db.scalar(select(Participant).where(Participant.email == "boss@example.com"))
        assert admin is not None and admin.role == ROLE_ADMIN

    def test_seed_is_idempotent(self, settings, engine, db):
        settings.admin_email = "boss@example.com"
        for _ in range(2):
            with TestClient(create_app(settings)):
                pass
        assert len(db.scalars(select(Participant)).all()) == 1

    def test_existing_participant_is_promoted(self, settings, engine, db, make_participant):
        make_participant("boss@example.com")
        settings.admin_email = "boss@example.com"
        with TestClient(create_app(settings)):
            pass
        db.expire_all()
        admins = db.scalars(select(Participant).where(Participant.role == ROLE_ADMIN)).all()
        assert [a.email for a in admins] == ["boss@example.com"]

    def test_app_starts_without_admin_email(self, settings, engine, db):
        settings.admin_email = None
        with TestClient(create_app(settings)):
            pass
        assert db.scalars(select(Participant)).all() == []
