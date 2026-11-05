import re

import pytest
from alembic import command
from sqlalchemy import inspect, select, text

from app.db import make_engine
from app.i18n import MESSAGES, normalize_locale, parse_accept_language, t
from app.models import Participant
from tests.helpers import payload
from tests.test_auth import login
from tests.test_migrations import alembic_config, empty_database  # noqa: F401, F811


class TestAcceptLanguage:
    @pytest.mark.parametrize(
        ("header", "expected"),
        [
            (None, "it"),
            ("", "it"),
            ("en", "en"),
            ("it", "it"),
            ("en-GB,en;q=0.9,it;q=0.8", "en"),
            ("it-IT,it;q=0.9,en;q=0.5", "it"),
            ("fr-FR,fr;q=0.9,en;q=0.5", "en"),
            ("fr,de", "it"),
            ("en;q=0,it;q=0.1", "it"),
            ("it;q=0.2,en;q=0.9", "en"),
        ],
    )
    def test_picks_the_best_supported_language(self, header, expected):
        assert parse_accept_language(header) == expected

    def test_unknown_locale_falls_back_to_italian(self):
        assert normalize_locale("fr") == "it"
        assert normalize_locale(None) == "it"
        assert normalize_locale("en") == "en"


class TestCatalog:
    def test_every_message_exists_in_both_languages_with_the_same_placeholders(self):
        names = lambda text_: sorted(re.findall(r"\{(\w+)\}", text_))  # noqa: E731
        for key, texts in MESSAGES.items():
            assert set(texts) == {"it", "en"}, key
            assert texts["it"].strip() and texts["en"].strip(), key
            assert names(texts["it"]) == names(texts["en"]), key

    def test_fills_placeholders_in_the_requested_language(self):
        assert t("refund.too_high", "en", amount="€5.00") == (
            "The refund can't exceed the amount paid (€5.00)"
        )
        assert "(5,00 €)" in t("refund.too_high", "it", amount="5,00 €")

    def test_defaults_to_italian_outside_a_request(self):
        assert t("booking.none") == "Non hai ancora un'iscrizione"


class TestErrorsFollowTheRequestLanguage:
    def _bad_login(self, client, language):
        headers = {"Accept-Language": language} if language else {}
        return client.post(
            "/api/auth/login",
            json={"email": "x@example.com", "password": "nope-nope-nope"},
            headers=headers,
        )

    def test_italian_by_default(self, client):
        assert self._bad_login(client, None).json()["detail"] == "Email o password non corretti"

    def test_english_with_accept_language(self, client):
        response = self._bad_login(client, "en")
        assert response.status_code == 401
        assert response.json()["detail"] == "Wrong email or password"

    def test_a_service_error_with_a_parameter(self, client, edition, admin_client):
        response = admin_client.put(
            "/api/admin/edition",
            json={"name": "C", "start_date": "2026-07-15", "end_date": "2026-07-13"},
            headers={"Accept-Language": "en"},
        )
        assert response.status_code == 422
        assert "The end date can't be before the start date" in str(response.json()["detail"])

    def test_validation_errors_are_translated_too(self, client, edition):
        body = payload([edition.slots[0].id])
        body["accept_privacy"] = False
        response = client.post(
            "/api/public/registrations", json=body, headers={"Accept-Language": "en"}
        )
        assert response.status_code == 422
        assert "accept the privacy notice" in str(response.json()["detail"])

    def test_language_does_not_leak_between_requests(self, client):
        assert self._bad_login(client, "en").json()["detail"] == "Wrong email or password"
        assert self._bad_login(client, None).json()["detail"] == "Email o password non corretti"


class TestParticipantLocale:
    def test_registration_saves_the_language_of_the_form(self, client, edition, db):
        body = payload([edition.slots[0].id])
        body["locale"] = "en"
        assert client.post("/api/public/registrations", json=body).status_code == 201
        assert db.scalar(select(Participant.locale)) == "en"

    def test_without_a_locale_the_request_language_is_used(self, client, edition, db):
        body = payload([edition.slots[0].id])
        response = client.post(
            "/api/public/registrations", json=body, headers={"Accept-Language": "en-US"}
        )
        assert response.status_code == 201
        assert db.scalar(select(Participant.locale)) == "en"

    def test_italian_when_nothing_says_otherwise(self, client, edition, db):
        assert (
            client.post(
                "/api/public/registrations", json=payload([edition.slots[0].id])
            ).status_code
            == 201
        )
        assert db.scalar(select(Participant.locale)) == "it"

    def test_unknown_locale_is_rejected(self, client, edition):
        body = payload([edition.slots[0].id])
        body["locale"] = "fr"
        assert client.post("/api/public/registrations", json=body).status_code == 422

    def test_me_shows_and_changes_the_language(self, client, outbox, make_participant, db):
        make_participant("ada@example.com")
        login(client, outbox)
        assert client.get("/api/me").json()["locale"] == "it"
        assert client.put("/api/me/locale", json={"locale": "en"}).status_code == 204
        assert client.get("/api/me").json()["locale"] == "en"
        db.expire_all()
        assert db.scalar(select(Participant.locale)) == "en"

    def test_changing_the_language_needs_a_login_and_a_known_language(
        self, client, outbox, make_participant
    ):
        assert client.put("/api/me/locale", json={"locale": "en"}).status_code == 401
        make_participant("ada@example.com")
        login(client, outbox)
        assert client.put("/api/me/locale", json={"locale": "fr"}).status_code == 422


def test_migration_0011_gives_existing_people_italian(
    alembic_config,  # noqa: F811
    database_url,
    empty_database,  # noqa: F811
):
    command.upgrade(alembic_config, "0010")
    engine = make_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO participant (first_name, last_name, email, personal_code, role,"
                " created_at) VALUES ('Ada', 'Lovelace', 'ada@example.com', 'CSC-0001',"
                " 'participant', '2026-07-01 10:00:00')"
            )
        )
    command.upgrade(alembic_config, "0011")
    with engine.connect() as connection:
        assert connection.execute(text("SELECT locale FROM participant")).scalar() == "it"
    command.downgrade(alembic_config, "0010")
    columns = {column["name"] for column in inspect(engine).get_columns("participant")}
    assert "locale" not in columns
    engine.dispose()
