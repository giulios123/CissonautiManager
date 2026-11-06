from datetime import UTC, date, datetime, time

import pytest

from app.models import Slot
from app.timefmt import (
    format_activity,
    format_deadline,
    format_euro,
    format_meal,
    format_slot,
    period_label,
    status_label,
)
from tests.helpers import d, payload
from tests.test_auth import login


class TestFormats:
    def test_italian_stays_as_it_was(self):
        assert format_slot(date(2026, 7, 13), "morning", time(9), time(13), "it") == (
            "lun 13/07 mattina (09:00-13:00)"
        )
        assert format_euro(1234, "it") == "12,34 €"
        assert format_deadline(datetime(2026, 7, 13, 10, 0, tzinfo=UTC), "it") == (
            "13/07/2026 alle 12:00"
        )
        assert format_meal(date(2026, 7, 13), "lunch", "it") == "pranzo di lun 13/07"
        assert format_activity("Gita", date(2026, 7, 13), "afternoon", "it") == (
            "Gita (lun 13/07 pomeriggio)"
        )
        assert status_label("confermata", "it") == "Confermata"
        assert period_label("evening", "it") == "Sera"

    def test_english(self):
        assert format_slot(date(2026, 7, 13), "morning", time(9), time(13), "en") == (
            "Mon 13 Jul morning (09:00-13:00)"
        )
        assert format_euro(1234, "en") == "€12.34"
        assert format_euro(-50, "en") == "-€0.50"
        assert format_deadline(datetime(2026, 7, 13, 10, 0, tzinfo=UTC), "en") == (
            "13 Jul 2026 at 12:00"
        )
        assert format_meal(date(2026, 7, 13), "dinner", "en") == "dinner on Mon 13 Jul"
        assert format_activity("Hike", date(2026, 7, 13), "afternoon", "en") == (
            "Hike (Mon 13 Jul afternoon)"
        )
        assert status_label("in_attesa_pagamento", "en") == "Awaiting payment"
        assert period_label("morning", "en") == "Morning"

    def test_without_a_language_the_request_one_is_used(
        self, client, outbox, db, make_participant, make_booking, slot_ids
    ):
        make_booking(
            make_participant("ada@example.com"), [db.get(Slot, slot_ids[(d(13), "morning")])]
        )
        login(client, outbox)
        english = client.get("/api/me", headers={"Accept-Language": "en"}).json()
        assert english["bookings"][0]["slots"][0]["label"] == "Mon 13 Jul morning (09:00-13:00)"
        italian = client.get("/api/me").json()
        assert italian["bookings"][0]["slots"][0]["label"] == "lun 13/07 mattina (09:00-13:00)"


class TestEmailsInTheLanguageOfThePerson:
    def _register(self, client, edition, locale, email="ada@example.com"):
        body = payload([edition.slots[0].id], locale=locale, email=email)
        assert client.post("/api/public/registrations", json=body).status_code == 201

    def test_registration_in_english(self, client, edition, outbox):
        self._register(client, edition, "en")
        message = outbox.sent[0]
        assert message.subject == "Registration for Cissonauti Summer Camp 2026"
        assert message.body.startswith("Hi Ada,")
        for expected in (
            "thank you for signing up for Cissonauti Summer Camp 2026!",
            "Your slots:",
            "Amount to pay: €",
            "Payment reference: CSC-",
            "Your place is held until",
            "How to pay:",
            "https://camp.example.org/login/verify?token=",
        ):
            assert expected in message.body, expected

    def test_registration_in_italian_is_unchanged(self, client, edition, outbox):
        self._register(client, edition, "it")
        message = outbox.sent[0]
        assert message.subject == "Iscrizione al Cissonauti Summer Camp 2026"
        assert message.body.startswith("Ciao Ada,")
        assert "Quota da versare: " in message.body and "Causale: CSC-" in message.body

    def test_the_language_follows_the_person_not_the_request(
        self, client, make_participant, outbox
    ):
        make_participant("ada@example.com", locale="en")
        client.post(
            "/api/auth/magic-link",
            json={"email": "ada@example.com"},
            headers={"Accept-Language": "it"},
        )
        message = outbox.sent[0]
        assert message.subject == "Your sign-in link for Cissonauti Summer Camp"
        assert "open this link to sign in" in message.body

    def test_the_public_form_never_changes_the_saved_language(self, client, edition, outbox, db):
        from sqlalchemy import select

        from app.models import Participant

        self._register(client, edition, "it")
        self._register(client, edition, "en")  # anyone who knows the address can do this
        assert db.scalar(select(Participant.locale)) == "it"

    def test_the_emails_of_that_request_follow_the_form_language(self, client, edition, outbox):
        self._register(client, edition, "it")
        self._register(client, edition, "en")
        assert (
            outbox.sent[1].subject == "You are already registered for Cissonauti Summer Camp 2026"
        )
        # The saved language still rules everything else, such as the sign-in link.
        outbox.sent.clear()
        client.post("/api/auth/magic-link", json={"email": "ada@example.com"})
        assert outbox.sent[0].subject == "Il tuo link di accesso al Cissonauti Summer Camp 2026"

    def test_a_returning_person_with_no_booking_gets_the_form_language_once(
        self, client, edition, outbox, db, make_participant
    ):
        from sqlalchemy import select

        from app.models import Participant

        make_participant("ada@example.com", locale="it")
        self._register(client, edition, "en")
        message = outbox.sent[0]
        assert message.subject == "Registration for Cissonauti Summer Camp 2026"
        assert message.body.startswith("Hi Ada,")
        assert db.scalar(select(Participant.locale)) == "it"

    def test_a_new_person_keeps_the_form_language(self, client, edition, db):
        from sqlalchemy import select

        from app.models import Participant

        self._register(client, edition, "en", email="new@example.com")
        assert db.scalar(select(Participant.locale)) == "en"

    def test_payment_confirmation_in_english(
        self, db, admin_client, make_participant, make_booking, slot_ids, outbox
    ):
        booking = make_booking(
            make_participant("ada@example.com", locale="en"),
            [db.get(Slot, slot_ids[(d(13), "morning")])],
        )
        response = admin_client.post(
            f"/api/admin/registrations/{booking.id}/payments",
            json={"amount_cents": 1100, "channel": "iban"},
            headers={"Accept-Language": "it"},
        )
        assert response.status_code == 201
        message = outbox.sent[-1]
        assert message.subject == "Payment received: you're in for Cissonauti Summer Camp 2026!"
        assert "your registration for Cissonauti Summer Camp 2026 is confirmed" in message.body
        assert "Mon 13 Jul morning" in message.body and "€11.00" in message.body

    def test_reminders_in_english(
        self, db, make_participant, make_booking, slot_ids, outbox, settings, clock
    ):
        from app.jobs.send_reminders import send_due_reminders

        make_booking(
            make_participant("ada@example.com", locale="en"),
            [db.get(Slot, slot_ids[(d(13), "morning")])],
        )
        clock.advance(hours=36)
        send_due_reminders(db, outbox, settings, clock())
        message = outbox.sent[-1]
        assert message.subject == "Reminder: your place at Cissonauti Summer Camp 2026"
        assert "a reminder that your place is being held" in message.body
        assert "Your place is held until" in message.body
        assert "Still to pay: €11.00" in message.body
        assert "https://camp.example.org/login" in message.body
        clock.advance(hours=35)
        send_due_reminders(db, outbox, settings, clock())
        assert outbox.sent[-1].subject.startswith("Last reminder:")

    def test_cancellation_in_english(
        self, client, db, make_participant, make_booking, slot_ids, outbox
    ):
        make_booking(
            make_participant("ada@example.com", locale="en"),
            [db.get(Slot, slot_ids[(d(13), "morning")])],
        )
        login(client, outbox)
        assert client.post("/api/me/booking/cancel").status_code == 200
        message = outbox.sent[-1]
        assert message.subject == "Cancellation for Cissonauti Summer Camp 2026"
        assert "we have recorded your cancellation" in message.body
        assert "nothing else to do" in message.body


@pytest.mark.parametrize("kind", ["add_to_confirmed", "new_booking", "add_to_pending"])
def test_promotion_email_exists_in_both_languages(
    db, make_participant, make_booking, slot_ids, kind
):
    from app.email.templates import waitlist_promoted_email

    slot = db.get(Slot, slot_ids[(d(13), "morning")])
    for locale, subject in (("it", "Si è liberato un posto"), ("en", "A place has opened up")):
        booking = make_booking(
            make_participant(f"{locale}{kind}@example.com", locale=locale), [slot]
        )
        message = waitlist_promoted_email(booking, slot, kind, [], 500, "https://x.test/l")
        assert message.subject.startswith(subject)
        assert "https://x.test/l" in message.body
