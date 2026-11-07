from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import STATUS_EXPIRED, BookingMeal, Slot
from app.services import edition as edition_service
from tests.helpers import d
from tests.test_auth import login


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


@pytest.fixture
def consent_text(db, edition):
    return edition_service.publish_legal_document(
        db, edition, "health", "Consenso dati sanitari", "Consent for health data"
    )


@pytest.fixture
def booking(db, make_participant, make_booking):
    return make_booking(make_participant("ada@example.com"), [slot(db, 13)])


@pytest.fixture
def member(client, outbox, booking):
    login(client, outbox)
    outbox.sent.clear()
    return client


def save(client, **body):
    return client.put("/api/me/booking/dietary", json=body)


def test_diet_is_saved_without_consent(member, db, booking):
    response = save(member, diet="vegetarian")
    assert response.status_code == 200
    assert response.json()["diet"] == "vegetarian"
    db.refresh(booking)
    assert (booking.diet, booking.allergies, booking.health_consent_at) == (
        "vegetarian",
        None,
        None,
    )


def test_allergies_without_consent_are_refused(member, db, booking, consent_text):
    response = save(member, diet="vegan", allergies="Arachidi")
    assert response.status_code == 422
    assert "consenso" in response.json()["detail"]
    db.refresh(booking)
    assert booking.allergies is None
    assert booking.diet is None


def test_allergies_with_consent_keep_the_version_and_time(member, db, booking, consent_text, clock):
    response = save(member, diet="omnivore", allergies="Arachidi", consent=True, consent_version=1)
    assert response.status_code == 200
    assert response.json()["allergies"] == "Arachidi"
    assert response.json()["health_consent_version"] == 1
    db.refresh(booking)
    assert booking.health_consent_document_id == consent_text.id
    assert booking.health_consent_at == clock()


def test_withdrawing_consent_deletes_the_allergies(member, db, booking, consent_text):
    save(member, allergies="Arachidi", consent=True, consent_version=1)
    response = save(member, allergies="", consent=False)
    assert response.status_code == 200
    db.refresh(booking)
    assert (booking.allergies, booking.health_consent_document_id) == (None, None)


def test_without_a_published_text_allergies_cannot_be_collected(member, edition):
    assert member.get("/api/me").json()["health_consent"] is None
    response = save(member, allergies="Arachidi", consent=True, consent_version=1)
    assert response.status_code == 409


def test_me_shows_the_consent_text(member, consent_text):
    assert member.get("/api/me").json()["health_consent"] == {
        "id": consent_text.id,
        "version": 1,
        "body": "Consenso dati sanitari",
        "body_it": "Consenso dati sanitari",
        "body_en": "Consent for health data",
        "is_legacy": False,
    }


def test_expired_booking_cannot_change(member, db, booking, clock):
    booking.status = STATUS_EXPIRED
    booking.hold_expires_at = clock() - timedelta(hours=1)
    db.commit()
    assert save(member, diet="vegan").status_code == 409


def test_unknown_diet_rejected(member):
    assert save(member, diet="carnivoro").status_code == 422


def test_allergies_never_appear_in_emails(member, db, booking, consent_text, outbox):
    save(member, allergies="Arachidi", consent=True, consent_version=1)
    booking.meals = [BookingMeal(date=d(13), kind="lunch")]
    db.commit()
    member.put("/api/me/booking/slots", json={"slot_ids": [slot(db, 14).id]})
    member.post("/api/me/booking/cancel")
    assert outbox.sent
    assert all("Arachidi" not in m.body for m in outbox.sent)


def test_removed_booking_takes_the_health_data_away(member, db, booking, consent_text):
    save(member, allergies="Arachidi", consent=True, consent_version=1)
    assert member.post("/api/me/booking/cancel").json()["outcome"] == "removed"
    from app.models import Booking

    assert db.scalar(select(Booking).where(Booking.allergies.is_not(None))) is None


def test_consent_to_an_outdated_text_is_refused(member, db, booking, consent_text, edition):
    edition_service.publish_legal_document(
        db, edition, "health", "Consenso v2", "Health consent v2"
    )
    response = save(member, allergies="Arachidi", consent=True, consent_version=1)
    assert response.status_code == 409
    assert "aggiornato" in response.json()["detail"]
    db.refresh(booking)
    assert booking.allergies is None


def test_consent_without_a_version_is_refused(member, consent_text):
    assert save(member, allergies="Arachidi", consent=True).status_code == 409


def test_a_diet_only_save_does_not_upgrade_the_accepted_version(
    member, db, booking, consent_text, edition
):
    save(member, allergies="Arachidi", consent=True, consent_version=1)
    edition_service.publish_legal_document(
        db, edition, "health", "Consenso v2", "Health consent v2"
    )
    response = save(member, diet="vegan", allergies="Arachidi", consent=True, consent_version=1)
    assert response.status_code == 409
    db.refresh(booking)
    assert booking.health_consent_document_id == consent_text.id
