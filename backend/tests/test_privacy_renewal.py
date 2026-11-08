from datetime import timedelta

from sqlalchemy import select

from app.email.templates import privacy_renewal_email
from app.jobs import send_reminders
from app.jobs.send_reminders import send_due_privacy_notices
from app.models import (
    DOC_PRIVACY,
    STATUS_CANCEL_REQUESTED,
    Booking,
    ConsentEvent,
    Participant,
    Slot,
)
from app.services import edition as edition_service
from app.services import privacy as privacy_service
from tests.helpers import d, payload
from tests.test_auth import login


def publish_privacy_v2(db, edition):
    return edition_service.publish_legal_document(
        db, edition, DOC_PRIVACY, "Informativa aggiornata", "Updated privacy notice"
    )


def test_privacy_api_requires_authenticated_current_version_and_is_idempotent(
    client, outbox, admin_client, db, edition, make_participant, make_booking, slot_ids, clock
):
    participant = make_participant("ada@example.com")
    make_booking(
        participant,
        [db.get(Slot, slot_ids[(d(13), "morning")])],
    )
    current = publish_privacy_v2(db, edition)
    login(client, outbox)

    response = client.get("/api/me")
    assert response.status_code == 200
    assert response.json()["privacy_acceptance_required"] is True
    state = client.get("/api/me/privacy")
    assert state.status_code == 200
    assert state.headers["cache-control"] == "private, no-store"
    assert state.json()["current_document"]["id"] == current.id
    assert [event["document"]["version"] for event in state.json()["history"]] == [1]

    stale = client.post(
        "/api/me/privacy/accept",
        json={"document_id": 1, "version": 1, "locale": "it", "accepted": True},
    )
    assert stale.status_code == 409
    accepted = client.post(
        "/api/me/privacy/accept",
        json={
            "document_id": current.id,
            "version": current.version,
            "locale": "en",
            "accepted": True,
        },
    )
    assert accepted.status_code == 200
    assert accepted.json()["required"] is False
    client.post(
        "/api/me/privacy/accept",
        json={
            "document_id": current.id,
            "version": current.version,
            "locale": "en",
            "accepted": True,
        },
    )
    events = db.scalars(
        select(ConsentEvent).where(
            ConsentEvent.participant_id == participant.id,
            ConsentEvent.kind == DOC_PRIVACY,
        )
    ).all()
    assert [(event.document_id, event.locale, event.recorded_at) for event in events] == [
        (1, "it", clock()),
        (current.id, "en", clock()),
    ]

    admin = admin_client.get(f"/api/admin/participants/{participant.id}/consents")
    assert admin.status_code == 200
    assert admin.json()["privacy_acceptance_required"] is False
    assert [event["document"]["version"] for event in admin.json()["privacy_history"]] == [1, 2]
    assert [event["locale"] for event in admin.json()["privacy_history"]] == ["it", "en"]


def test_privacy_pending_blocks_edit_apis_but_allows_cancellation(
    client, outbox, db, edition, make_participant, make_booking, slot_ids, clock
):
    participant = make_participant("ada@example.com")
    booking = make_booking(participant, [db.get(Slot, slot_ids[(d(13), "morning")])])
    publish_privacy_v2(db, edition)
    login(client, outbox)

    requests = (
        ("PUT", "/api/me/booking/slots", {"slot_ids": [slot_ids[(d(13), "morning")]]}),
        ("PUT", "/api/me/booking/meals", {"meals": []}),
        ("PUT", "/api/me/booking/activities", {"activity_ids": []}),
        (
            "POST",
            "/api/me/contributions",
            {"kind": "talk", "title": "A topic", "description": None},
        ),
        ("POST", "/api/me/waitlist", {"slot_id": slot_ids[(d(14), "morning")]}),
    )
    for method, path, body in requests:
        response = client.request(method, path, json=body)
        assert response.status_code == 428, (path, response.text)
        assert response.json()["detail"]["code"] == "privacy_acceptance_required"

    response = client.post("/api/me/booking/cancel")
    assert response.status_code == 200
    assert response.json()["outcome"] == "removed"
    assert db.scalar(select(Booking.id).where(Booking.id == booking.id)) is None


def test_new_public_registration_records_initial_privacy_acceptance(client, db, edition, slot_ids):
    response = client.post(
        "/api/public/registrations",
        json=payload([slot_ids[(d(13), "morning")]]),
    )
    assert response.status_code == 201
    participant = db.scalar(select(Participant).where(Participant.email == "ada@example.com"))
    assert participant is not None
    event = db.scalar(
        select(ConsentEvent).where(
            ConsentEvent.participant_id == participant.id,
            ConsentEvent.kind == DOC_PRIVACY,
        )
    )
    assert event is not None
    assert (event.action, event.locale, event.source) == (
        "accepted",
        "it",
        "public_registration",
    )
    assert privacy_service.acceptance_required(db, edition, participant) is False


def test_known_account_public_resubmission_stays_pending_until_login(
    client, db, edition, make_participant, make_booking, slot_ids, clock
):
    participant = make_participant("ada@example.com")
    slot = db.get(Slot, slot_ids[(d(13), "morning")])
    make_booking(
        participant,
        [slot],
        status="scaduta",
        hold_expires_at=clock() - timedelta(seconds=1),
    )
    current = publish_privacy_v2(db, edition)
    response = client.post(
        "/api/public/registrations",
        json=payload([slot.id], privacy_version=current.version),
    )
    assert response.status_code == 201
    assert response.json()["result"] == "created"
    assert privacy_service.acceptance_required(db, edition, participant) is True
    assert (
        db.scalar(
            select(ConsentEvent.id).where(
                ConsentEvent.participant_id == participant.id,
                ConsentEvent.document_id == current.id,
            )
        )
        is None
    )


def test_hourly_job_sends_once_for_current_pending_bookings_and_open_waitlists(
    db, edition, make_participant, make_booking, add_entry, slot_ids, outbox, settings, clock
):
    booked = make_participant("booked@example.com")
    make_booking(booked, [db.get(Slot, slot_ids[(d(13), "morning")])])

    waiting = make_participant("waiting@example.com")
    add_entry(db.get(Slot, slot_ids[(d(14), "morning")]), waiting, clock())

    accepted = make_participant("accepted@example.com")
    make_booking(accepted, [db.get(Slot, slot_ids[(d(15), "morning")])])
    current = publish_privacy_v2(db, edition)
    privacy_service.accept_current(
        db,
        edition,
        accepted,
        document_id=current.id,
        version=current.version,
        locale="it",
        now=clock(),
    )
    db.commit()

    assert send_due_privacy_notices(db, outbox, settings, clock()) == 2
    assert [message.to for message in outbox.sent] == [booked.email, waiting.email]
    assert all("/login?lang=it" in message.body for message in outbox.sent)
    assert all("versione 2" in message.body for message in outbox.sent)
    assert send_due_privacy_notices(db, outbox, settings, clock()) == 0
    assert len(outbox.sent) == 2


def test_failed_privacy_notice_is_not_retried(
    db, edition, make_participant, make_booking, slot_ids, outbox, settings, clock, monkeypatch
):
    participant = make_participant("failed@example.com")
    make_booking(participant, [db.get(Slot, slot_ids[(d(13), "morning")])])
    publish_privacy_v2(db, edition)
    attempts = []

    def fail_send(message):
        attempts.append(message)
        raise RuntimeError("email provider unavailable")

    monkeypatch.setattr(outbox, "send", fail_send)
    assert send_due_privacy_notices(db, outbox, settings, clock()) == 1
    assert len(attempts) == 1
    assert send_due_privacy_notices(db, outbox, settings, clock()) == 0
    assert len(attempts) == 1


def test_privacy_notice_rechecks_active_association_under_lock(
    db, edition, make_participant, make_booking, slot_ids, outbox, settings, clock, monkeypatch
):
    participant = make_participant("cancelled@example.com")
    booking = make_booking(participant, [db.get(Slot, slot_ids[(d(13), "morning")])])
    publish_privacy_v2(db, edition)
    db.commit()
    real_lock = send_reminders.lock_edition

    def cancel_before_eligibility_check(session, edition_id):
        booking.status = STATUS_CANCEL_REQUESTED
        session.commit()
        real_lock(session, edition_id)

    monkeypatch.setattr(send_reminders, "lock_edition", cancel_before_eligibility_check)
    assert send_due_privacy_notices(db, outbox, settings, clock()) == 0
    assert outbox.sent == []
    assert privacy_service.active_recipient_ids(db, edition, clock()) == []


def test_privacy_notice_template_is_bilingual_and_requires_login():
    from app.models import Participant

    participant = Participant(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        personal_code="CSC-AAAA",
        locale="en",
    )
    message = privacy_renewal_email(
        participant,
        event_name="Camp",
        version=3,
        link="https://camp.example.org/login?lang=en",
    )
    assert message.subject == "Updated privacy notice for Camp"
    assert "version 3" in message.body
    assert "Sign in" in message.body
    assert "https://camp.example.org/login?lang=en" in message.body
