from sqlalchemy import select

from app.models import AuditLog, Edition
from tests.helpers import payload

CUSTOM = {"subject": "Benvenuto a {evento}", "intro": "Ehi {nome}!", "closing": "A presto!"}


def put_text(client, kind="registration", **body):
    return client.put(f"/api/admin/email-texts/{kind}", json=body)


def register(client, slot_ids):
    return client.post("/api/public/registrations", json=payload(slot_ids))


class TestAccess:
    def test_anonymous_gets_401_and_participant_403(self, client, make_participant):
        assert client.get("/api/admin/email-texts").status_code == 401
        make_participant("ada@example.com")
        client.post("/api/auth/magic-link", json={"email": "ada@example.com"})
        assert client.put("/api/admin/registration-intro", json={"text": "x"}).status_code == 401

    def test_participant_is_refused(self, client, make_participant, outbox):
        make_participant("ada@example.com")
        client.post("/api/auth/magic-link", json={"email": "ada@example.com"})
        token = outbox.sent[-1].body.split("token=")[1].split()[0]
        client.post("/api/auth/verify", json={"token": token})
        assert client.get("/api/admin/email-texts").status_code == 403
        assert put_text(client, **CUSTOM).status_code == 403
        assert client.put("/api/admin/registration-intro", json={"text": "x"}).status_code == 403


class TestListAndSave:
    def test_lists_every_kind_with_defaults_and_nothing_stored(self, admin_client, edition):
        body = admin_client.get("/api/admin/email-texts").json()
        assert body["placeholders"] == ["{nome}", "{evento}"]
        assert [e["kind"] for e in body["emails"]] == [
            "registration",
            "waitlist_joined",
            "already_registered",
            "magic_link",
            "payment_confirmation",
            "reminder_mid",
            "reminder_final",
            "waitlist_promoted",
            "cancellation",
        ]
        first = body["emails"][0]
        assert first["stored"] == {"subject": None, "intro": None, "closing": None}
        assert "{evento}" in first["defaults"]["subject"]
        assert first["automatic"]

    def test_save_returns_the_stored_values_and_logs_it(self, admin_client, edition, db):
        response = put_text(admin_client, **CUSTOM)
        assert response.status_code == 200
        assert response.json()["stored"] == CUSTOM
        listed = admin_client.get("/api/admin/email-texts").json()["emails"][0]
        assert listed["stored"] == CUSTOM
        assert db.scalar(select(AuditLog).where(AuditLog.action == "email_text_changed"))

    def test_blank_fields_go_back_to_the_default(self, admin_client, edition):
        put_text(admin_client, **CUSTOM)
        response = put_text(admin_client, subject="  ", intro="", closing=None)
        assert response.json()["stored"] == {"subject": None, "intro": None, "closing": None}

    def test_overlapping_first_saves_update_instead_of_failing(
        self, admin_client, edition, engine, monkeypatch
    ):
        """The other save wins the insert between our lookup and our insert: we must not 500."""
        from sqlalchemy.orm import Session

        from app.models import EmailText
        from app.services import email_texts as service

        real_save = service.save_texts
        calls = []

        def racing_save(db, edition_, kind, subject, intro, closing, actor, now=None):
            calls.append(kind)
            if len(calls) == 1:
                with Session(engine) as other:
                    other.add(EmailText(edition_id=edition_.id, kind=kind, subject="Primo"))
                    other.commit()
                # Our own insert now clashes with the committed row.
                db.add(EmailText(edition_id=edition_.id, kind=kind, subject="Secondo"))
                db.flush()
            return real_save(db, edition_, kind, subject, intro, closing, actor, now)

        monkeypatch.setattr(service, "save_texts", racing_save)
        response = put_text(admin_client, **CUSTOM)
        assert response.status_code == 200
        assert response.json()["stored"] == CUSTOM
        assert len(calls) == 2

    def test_unknown_kind_is_404(self, admin_client, edition):
        assert put_text(admin_client, "nope", **CUSTOM).status_code == 404

    def test_too_long_texts_are_refused(self, admin_client, edition):
        assert put_text(admin_client, subject="a" * 201).status_code == 422
        assert put_text(admin_client, intro="a" * 4001).status_code == 422
        assert put_text(admin_client, closing="a" * 4001).status_code == 422

    def test_without_an_edition_it_is_404(self, admin_client):
        assert put_text(admin_client, **CUSTOM).status_code == 404


class TestInEmails:
    def test_default_subject_carries_the_edition_name(self, client, edition, slot_ids, outbox):
        register(client, [min(slot_ids.values())])
        [email] = outbox.sent
        assert email.subject == "Iscrizione a Cissonauti Summer Camp 2026"
        assert email.body.startswith("Ciao Ada,\n\ngrazie per esserti iscritto a Cissonauti")

    def test_renaming_the_edition_renames_the_subject(
        self, client, admin_client, edition, slot_ids, outbox, db
    ):
        edition.name = "Camp d'autunno"
        db.commit()
        register(client, [min(slot_ids.values())])
        assert outbox.sent[-1].subject == "Iscrizione a Camp d'autunno"

    def test_custom_texts_wrap_the_automatic_block(
        self, client, admin_client, edition, slot_ids, outbox
    ):
        put_text(admin_client, **CUSTOM)
        register(client, [min(slot_ids.values())])
        [email] = outbox.sent
        assert email.subject == "Benvenuto a Cissonauti Summer Camp 2026"
        assert email.body.startswith("Ehi Ada!\n\nI tuoi slot:")
        assert email.body.rstrip().endswith("A presto!")
        for automatic in ("Quota da versare:", "Causale: CSC-", "Come pagare:", "accedi/verifica"):
            assert automatic in email.body

    def test_other_kinds_keep_their_own_texts(
        self, client, admin_client, edition, slot_ids, outbox, make_participant
    ):
        put_text(admin_client, **CUSTOM)
        make_participant("bea@example.com")
        client.post("/api/auth/magic-link", json={"email": "bea@example.com"})
        link_email = outbox.sent[-1]
        assert link_email.subject == "Il tuo link di accesso a Cissonauti Summer Camp 2026"
        assert "A presto!" not in link_email.body

    def test_magic_link_text_can_be_customised(
        self, client, admin_client, edition, outbox, make_participant
    ):
        put_text(admin_client, "magic_link", subject="Entra in {evento}", intro="Ciao {nome}, via!")
        make_participant("bea@example.com", first_name="Bea")
        client.post("/api/auth/magic-link", json={"email": "bea@example.com"})
        email = outbox.sent[-1]
        assert email.subject == "Entra in Cissonauti Summer Camp 2026"
        assert email.body.startswith("Ciao Bea, via!\n\nhttp")
        assert "Il link vale 10 minuti." in email.body

    def test_placeholders_in_a_name_are_not_expanded_twice(
        self, client, admin_client, edition, outbox, make_participant
    ):
        put_text(admin_client, "magic_link", intro="{nome}")
        make_participant("bea@example.com", first_name="{evento}")
        client.post("/api/auth/magic-link", json={"email": "bea@example.com"})
        assert outbox.sent[-1].body.startswith("{evento}\n\n")

    def test_without_an_edition_the_default_name_is_used(self, client, outbox, make_participant):
        make_participant("bea@example.com")
        client.post("/api/auth/magic-link", json={"email": "bea@example.com"})
        assert outbox.sent[-1].subject == "Il tuo link di accesso a Cissonauti Summer Camp"


class TestRegistrationIntro:
    DEFAULT = "Scegli i momenti in cui vuoi venire."

    def test_public_edition_shows_the_default_until_one_is_saved(
        self, client, admin_client, edition
    ):
        assert (
            client.get("/api/public/edition").json()["registration_intro"].startswith(self.DEFAULT)
        )
        response = admin_client.put(
            "/api/admin/registration-intro", json={"text": " Ciao!\nA presto "}
        )
        assert response.json()["stored"] == "Ciao!\nA presto"
        assert client.get("/api/public/edition").json()["registration_intro"] == "Ciao!\nA presto"
        assert (
            admin_client.get("/api/admin/edition").json()["registration_intro"] == "Ciao!\nA presto"
        )

    def test_empty_text_restores_the_default(self, client, admin_client, edition):
        admin_client.put("/api/admin/registration-intro", json={"text": "Altro"})
        admin_client.put("/api/admin/registration-intro", json={"text": ""})
        assert (
            client.get("/api/public/edition").json()["registration_intro"].startswith(self.DEFAULT)
        )

    def test_too_long_is_refused_and_saving_the_edition_keeps_the_text(
        self, admin_client, edition, db
    ):
        assert (
            admin_client.put("/api/admin/registration-intro", json={"text": "a" * 4001}).status_code
            == 422
        )
        admin_client.put("/api/admin/registration-intro", json={"text": "Resta"})
        current = admin_client.get("/api/admin/edition").json()
        admin_client.put(
            "/api/admin/edition",
            json={k: v for k, v in current.items() if k in {"name", "default_capacity"}},
        )
        db.expire_all()
        assert db.scalar(select(Edition)).registration_intro == "Resta"
