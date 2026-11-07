"""The other emails and the paragraph of the sign-up form that the admin can edit."""

from sqlalchemy import select

from app.email.base import EmailTexts
from app.email.templates import (
    booking_confirmation_email,
    cancellation_email,
    payment_confirmation_email,
    reminder_email,
    waitlist_promoted_email,
)
from app.models import Edition, EmailTemplate, Slot
from tests.helpers import payload

KINDS = [
    "waitlist_joined",
    "already_registered",
    "magic_link",
    "payment_confirmation",
    "booking_confirmation",
    "reminder_mid",
    "reminder_final",
    "waitlist_promoted",
    "cancellation",
]
URL = "/api/admin/email/texts"


def body(it_subject="", it_body="", en_subject="", en_body=""):
    return {
        "templates": {
            "it": {"subject": it_subject, "body": it_body},
            "en": {"subject": en_subject, "body": en_body},
        }
    }


def put_text(client, kind="magic_link", **fields):
    return client.put(f"{URL}/{kind}", json=body(**fields))


class TestAccess:
    def test_needs_an_admin(self, client, edition):
        assert client.get(URL).status_code == 401
        assert client.put(f"{URL}/magic_link", json=body()).status_code == 401
        assert client.put("/api/admin/email/form-intro", json={"it": "x"}).status_code == 401

    def test_participants_are_refused(self, client, make_participant, outbox, edition):
        from tests.test_auth import login

        make_participant("ada@example.com")
        login(client, outbox)
        assert client.get(URL).status_code == 403
        assert put_text(client).status_code == 403
        assert client.put("/api/admin/email/form-intro", json={"it": "x"}).status_code == 403

    def test_without_an_edition_it_is_404(self, admin_client):
        assert admin_client.get(URL).status_code == 404
        assert put_text(admin_client).status_code == 404


class TestSettingsApi:
    def test_lists_every_other_email_with_defaults_in_both_languages(self, admin_client, edition):
        data = admin_client.get(URL).json()
        assert list(data["emails"]) == KINDS
        cancellation = data["emails"]["cancellation"]
        assert cancellation["templates"]["it"] == {"subject": "", "body": ""}
        assert cancellation["defaults"]["it"]["subject"] == "Disdetta al {event}"
        assert cancellation["defaults"]["en"]["subject"] == "Cancellation for {event}"
        assert cancellation["defaults"]["en"]["body"].startswith("Hi {first_name},\n\n")
        confirmation = data["emails"]["booking_confirmation"]
        assert confirmation["defaults"]["it"]["subject"] == (
            "La tua iscrizione al {event} è confermata"
        )
        assert confirmation["defaults"]["en"]["subject"] == (
            "Your registration for {event} is confirmed"
        )
        assert data["form_intro"]["it"] == ""
        assert data["form_intro"]["defaults"]["en"].startswith("Choose when")

    def test_saves_both_languages(self, admin_client, edition):
        response = put_text(
            admin_client,
            it_subject="Entra in {event}",
            it_body="Ciao {first_name}!",
            en_subject="Come in",
            en_body="Hello {first_name}",
        )
        assert response.status_code == 200
        saved = response.json()["emails"]["magic_link"]["templates"]
        assert saved["it"] == {"subject": "Entra in {event}", "body": "Ciao {first_name}!"}
        assert saved["en"] == {"subject": "Come in", "body": "Hello {first_name}"}
        assert admin_client.get(URL).json()["emails"]["magic_link"]["templates"] == saved

    def test_empty_fields_go_back_to_the_standard_wording(self, admin_client, edition):
        put_text(admin_client, it_subject="X", it_body="Y")
        response = put_text(admin_client)
        assert response.json()["emails"]["magic_link"]["templates"]["it"] == {
            "subject": "",
            "body": "",
        }

    def test_other_emails_are_left_alone(self, admin_client, edition):
        put_text(admin_client, "cancellation", it_subject="Addio")
        put_text(admin_client, "magic_link", it_subject="Entra")
        emails = admin_client.get(URL).json()["emails"]
        assert emails["cancellation"]["templates"]["it"]["subject"] == "Addio"

    def test_unknown_email_is_404(self, admin_client, edition):
        assert put_text(admin_client, "registration").status_code == 404
        assert put_text(admin_client, "nope").status_code == 404

    def test_unknown_placeholders_are_refused(self, admin_client, edition):
        response = put_text(admin_client, it_body="Ciao {nome}")
        assert response.status_code == 422
        assert "{nome}" in response.text

    def test_too_long_texts_are_refused(self, admin_client, edition):
        assert put_text(admin_client, it_subject="a" * 201).status_code == 422
        assert put_text(admin_client, en_body="a" * 5001).status_code == 422

    def test_overlapping_first_saves_update_instead_of_failing(
        self, admin_client, edition, engine, monkeypatch
    ):
        """The other save wins the insert between our lookup and our insert: no 500."""
        from sqlalchemy.orm import Session

        from app.services import email_templates as service

        real_save = service.save_email
        calls = []

        def racing_save(db, edition_, admin, kind, templates, now=None):
            calls.append(kind)
            if len(calls) == 1:
                with Session(engine) as other:
                    other.add(
                        EmailTemplate(
                            edition_id=edition_.id, kind=kind, locale="it", subject="Primo", body=""
                        )
                    )
                    other.commit()
                # Our own insert now clashes with the committed row.
                db.add(
                    EmailTemplate(
                        edition_id=edition_.id, kind=kind, locale="it", subject="Secondo", body=""
                    )
                )
                db.flush()
            return real_save(db, edition_, admin, kind, templates, now)

        monkeypatch.setattr(service, "save_email", racing_save)
        response = put_text(admin_client, it_subject="Scelto")
        assert response.status_code == 200
        assert response.json()["emails"]["magic_link"]["templates"]["it"]["subject"] == "Scelto"
        assert len(calls) == 2


class TestInEmails:
    def test_the_standard_subject_carries_the_name_of_the_edition(
        self, client, edition, make_participant, outbox, db
    ):
        make_participant("bea@example.com")
        client.post("/api/auth/magic-link", json={"email": "bea@example.com"})
        assert outbox.sent[-1].subject == "Il tuo link di accesso al Cissonauti Summer Camp 2026"
        edition.name = "Camp d'autunno"
        db.commit()
        client.post("/api/auth/magic-link", json={"email": "bea@example.com"})
        assert outbox.sent[-1].subject == "Il tuo link di accesso al Camp d'autunno"

    def test_the_magic_link_wording_is_replaced_and_the_link_stays(
        self, client, admin_client, edition, make_participant, outbox
    ):
        put_text(
            admin_client,
            it_subject="Entra in {event}",
            it_body="Ehi {first_name} {last_name}, via!",
        )
        make_participant("bea@example.com", first_name="Bea", last_name="Rossi")
        client.post("/api/auth/magic-link", json={"email": "bea@example.com"})
        email = outbox.sent[-1]
        assert email.subject == "Entra in Cissonauti Summer Camp 2026"
        assert email.body.startswith("Ehi Bea Rossi, via!\n\nhttp")
        assert "/verify?token=" in email.body or "token=" in email.body
        assert "Il link vale 10 minuti" in email.body

    def test_each_language_uses_its_own_text(
        self, client, admin_client, edition, make_participant, outbox
    ):
        put_text(admin_client, it_body="Ciao a te", en_subject="Come in", en_body="Hello you")
        make_participant("bea@example.com", locale="en")
        client.post("/api/auth/magic-link", json={"email": "bea@example.com"})
        english = outbox.sent[-1]
        assert english.subject == "Come in"
        assert english.body.startswith("Hello you\n\nhttp")
        make_participant("gigi@example.com", locale="it")
        client.post("/api/auth/magic-link", json={"email": "gigi@example.com"})
        italian = outbox.sent[-1]
        assert italian.body.startswith("Ciao a te\n\nhttp")
        assert italian.subject == "Il tuo link di accesso al Cissonauti Summer Camp 2026"

    def test_the_standard_opening_is_kept_when_nothing_is_written(
        self, client, edition, make_participant, outbox
    ):
        make_participant("bea@example.com", first_name="Bea")
        client.post("/api/auth/magic-link", json={"email": "bea@example.com"})
        assert outbox.sent[-1].body.startswith("Ciao Bea,\n\napri questo link per entrare.\n\nhttp")

    def test_already_registered_and_waitlist_texts(
        self, client, admin_client, edition, slot_ids, outbox, db
    ):
        put_text(admin_client, "already_registered", it_body="Di nuovo tu, {first_name}!")
        first = min(slot_ids.values())
        for _ in range(2):
            client.post("/api/public/registrations", json=payload([first]))
        email = outbox.sent[-1]
        assert email.body.startswith("Di nuovo tu, Ada!\n\nPer vedere la tua pagina personale")

    def test_a_person_registered_only_on_the_waitlist_gets_the_text(
        self, client, admin_client, edition, db, fill_slot, outbox
    ):
        put_text(
            admin_client, "waitlist_joined", it_subject="In coda per {event}", it_body="Eccoci"
        )
        full = db.scalar(select(Slot).order_by(Slot.id))
        fill_slot(full)
        outbox.sent.clear()
        response = client.post(
            "/api/public/registrations",
            json=payload([], waitlist_slot_ids=[full.id]),
        )
        assert response.status_code == 201
        email = outbox.sent[-1]
        assert email.subject == "In coda per Cissonauti Summer Camp 2026"
        assert email.body.startswith("Eccoci\n\n")
        assert "Finché non si libera un posto" in email.body


class TestTemplateFunctions:
    """The other emails, built from a booking, with and without the organizers' text."""

    def booking(self, make_participant, make_booking, db):
        person = make_participant("ada@example.com", first_name="Ada")
        slots = list(db.scalars(select(Slot).order_by(Slot.id)))[:2]
        return make_booking(person, slots)

    def test_payment_confirmation(self, make_participant, make_booking, db, edition):
        booking = self.booking(make_participant, make_booking, db)
        texts = EmailTexts("Camp", "Pagato: {event}", "Grazie Ada!")
        email = payment_confirmation_email(booking, 1100, texts)
        assert email.subject == "Pagato: {event}"  # placeholders are replaced by the service
        assert email.body.startswith("Grazie Ada!\n\nPagamento registrato: 11,00")
        assert "Ci vediamo presto!" in email.body
        assert "1 giorno di presenza:" in email.body
        assert email.html is not None
        standard = payment_confirmation_email(booking, 1100, EmailTexts("Camp"))
        assert standard.subject == "Pagamento ricevuto: sei dentro al Camp!"
        assert standard.body.startswith("Ciao Ada,\n\nabbiamo registrato il tuo pagamento:")

    def test_booking_confirmation_does_not_claim_a_new_payment(
        self, make_participant, make_booking, db, edition
    ):
        booking = self.booking(make_participant, make_booking, db)
        booking.registration_fee_cents = 1200
        booking.amount_due_cents = 1600
        texts = EmailTexts("Camp", "Conferma Camp", "Quota coperta.")

        email = booking_confirmation_email(booking, 1200, "https://camp.example.org/login", texts)

        assert email.subject == "Conferma Camp"
        assert email.body.startswith("Quota coperta.\n\nQuota di partecipazione coperta: 12,00 €")
        assert "Resta da saldare all'organizzazione: 4,00 €" in email.body
        assert "https://camp.example.org/login" in email.body
        assert "Pagamento registrato" not in email.body

    def test_reminders(self, make_participant, make_booking, db, edition):
        booking = self.booking(make_participant, make_booking, db)
        texts = EmailTexts("Camp", None, "Ricordati!")
        for kind in ("mid", "final"):
            email = reminder_email(booking, kind, [], 500, "http://x/login", texts)
            assert email.body.startswith("Ricordati!\n\nIl posto è bloccato fino al")
            assert "Ancora da versare: 5,00" in email.body
            assert "Se hai già pagato" in email.body
        mid = reminder_email(booking, "mid", [], 500, "http://x/login", EmailTexts("Camp"))
        final = reminder_email(booking, "final", [], 500, "http://x/login", EmailTexts("Camp"))
        assert mid.subject == "Promemoria: il tuo posto al Camp"
        assert final.subject == "Ultimo promemoria: il tuo posto al Camp sta per liberarsi"

    def test_promotion_and_cancellation(self, make_participant, make_booking, db, edition):
        booking = self.booking(make_participant, make_booking, db)
        slot = booking.slots[0]
        promoted = waitlist_promoted_email(
            booking, slot, "new_booking", [], 1100, "http://x/t", EmailTexts("Camp", None, "Evviva")
        )
        assert promoted.body.startswith("Evviva\n\nSlot assegnato: ")
        assert "http://x/t" in promoted.body
        cancelled = cancellation_email(
            "ada@example.com", "Ada", True, False, "it", EmailTexts("Camp", "Ciao {event}", "Addio")
        )
        assert cancelled.body.startswith("Addio\n\nNon risultano pagamenti")


class TestFormIntro:
    def put_intro(self, client, **fields):
        return client.put("/api/admin/email/form-intro", json=fields)

    def test_public_edition_has_the_standard_paragraph_in_both_languages(self, client, edition):
        intro = client.get("/api/public/edition").json()["registration_intro"]
        assert intro["it"].startswith("Scegli i momenti in cui vuoi venire")
        assert intro["en"].startswith("Choose when you want to come")

    def test_the_written_paragraph_replaces_the_standard_one_per_language(
        self, client, admin_client, edition
    ):
        response = self.put_intro(admin_client, it=" Benvenuti!\nScegliete. ")
        assert response.json()["form_intro"]["it"] == "Benvenuti!\nScegliete."
        intro = client.get("/api/public/edition").json()["registration_intro"]
        assert intro["it"] == "Benvenuti!\nScegliete."
        assert intro["en"].startswith("Choose when")  # the other language is untouched

    def test_empty_text_restores_the_standard_one(self, client, admin_client, edition):
        self.put_intro(admin_client, it="Altro", en="Other")
        self.put_intro(admin_client, it="", en="")
        intro = client.get("/api/public/edition").json()["registration_intro"]
        assert intro["it"].startswith("Scegli i momenti")

    def test_too_long_is_refused(self, admin_client, edition):
        assert self.put_intro(admin_client, it="a" * 2001).status_code == 422

    def test_saving_the_edition_keeps_the_paragraph(self, admin_client, edition, db):
        self.put_intro(admin_client, it="Resta", en="Stay")
        current = admin_client.get("/api/admin/edition").json()
        admin_client.put("/api/admin/edition", json={"name": current["name"]})
        db.expire_all()
        saved = db.scalar(select(Edition))
        assert (saved.registration_intro_it, saved.registration_intro_en) == ("Resta", "Stay")
