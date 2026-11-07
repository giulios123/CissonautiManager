from datetime import date

import pytest
from sqlalchemy import select

from app.models import Booking, ConsentEvent, Slot
from app.services import edition as edition_service
from tests.test_auth import login


def add_optional_texts(db, edition):
    return {
        "attendance": edition_service.publish_legal_document(
            db, edition, "attendance", "Presenza riservata", "Members-only attendance"
        ),
        "media": edition_service.publish_legal_document(
            db, edition, "media", "Foto e video", "Photos and video"
        ),
    }


@pytest.fixture
def consent_member(client, outbox, db, edition, make_participant, make_booking):
    participant = make_participant("ada@example.com")
    slot = db.scalar(select(Slot).where(Slot.date == date(2026, 7, 13), Slot.period == "morning"))
    make_booking(participant, [slot])
    docs = add_optional_texts(db, edition)
    login(client, outbox)
    return client, participant, docs


def test_personal_consent_endpoint_requires_login(client):
    assert client.get("/api/me/consents").status_code == 401
    assert client.put("/api/me/consents/attendance", json={}).status_code == 401


def test_participant_can_read_and_grant_own_choices(consent_member):
    client, participant, docs = consent_member
    response = client.get("/api/me/consents")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "private, no-store"
    assert response.json()["associated"] is True
    assert [item["action"] for item in response.json()["consents"]] == [
        "not_expressed",
        "not_expressed",
    ]

    response = client.put(
        "/api/me/consents/attendance",
        json={
            "granted": True,
            "document_id": docs["attendance"].id,
            "version": docs["attendance"].version,
            "locale": "en",
            "expected_event_id": None,
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["consents"][0]["action"] == "granted"
    assert response.json()["consents"][1]["action"] == "not_expressed"


def test_revoke_remains_available_after_new_document_and_booking_removal(
    consent_member, db, edition
):
    client, participant, docs = consent_member
    grant = client.put(
        "/api/me/consents/attendance",
        json={
            "granted": True,
            "document_id": docs["attendance"].id,
            "version": 1,
            "locale": "it",
            "expected_event_id": None,
        },
    ).json()["consents"][0]
    booking = db.scalar(select(Booking).where(Booking.participant_id == participant.id))
    db.delete(booking)
    db.commit()
    assert client.get("/api/me/consents").json()["associated"] is True
    # A new full version makes the old grant non-current, but does not block revocation.
    edition_service.publish_legal_document(
        db, edition, "attendance", "Presenza riservata v2", "Members-only attendance v2"
    )
    response = client.put(
        "/api/me/consents/attendance",
        json={
            "granted": False,
            "locale": "en",
            "expected_event_id": grant["event_id"],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["consents"][0]["action"] == "withdrawn"
    events = db.scalars(
        select(ConsentEvent).where(ConsentEvent.participant_id == participant.id)
    ).all()
    assert [(event.action, event.document_id) for event in events] == [
        ("granted", docs["attendance"].id),
        ("withdrawn", docs["attendance"].id),
    ]


def test_stale_choice_conflicts_and_does_not_append(consent_member, db):
    client, participant, docs = consent_member
    payload = {
        "granted": True,
        "document_id": docs["attendance"].id,
        "version": 1,
        "locale": "it",
        "expected_event_id": None,
    }
    assert client.put("/api/me/consents/attendance", json=payload).status_code == 200
    response = client.put("/api/me/consents/attendance", json={**payload, "granted": False})
    assert response.status_code == 409
    assert db.query(ConsentEvent).filter_by(participant_id=participant.id).count() == 1


def test_admin_can_read_waitlist_only_person_history(
    admin_client, db, edition, make_participant, add_entry, clock
):
    unassociated = make_participant("nobody@example.com")
    assert (
        admin_client.get(f"/api/admin/participants/{unassociated.id}/consents").status_code == 404
    )

    participant = make_participant("ada@example.com")
    slot = db.scalar(select(Slot).where(Slot.date == date(2026, 7, 13), Slot.period == "morning"))
    add_entry(slot, participant, clock())
    response = admin_client.get(f"/api/admin/participants/{participant.id}/consents")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "private, no-store"
    assert response.json()["associated"] is True
    response = admin_client.put(
        f"/api/admin/participants/{participant.id}/consents/attendance", json={}
    )
    assert response.status_code == 404
