from sqlalchemy import select

from app.models import STATUS_EXPIRED, STATUS_PENDING, Booking, Participant, Slot, WaitlistEntry
from app.services import edition as edition_service
from tests.helpers import d, payload


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


def register(client, free_ids, waitlist_ids, **overrides):
    return client.post(
        "/api/public/registrations",
        json=payload(free_ids, waitlist_slot_ids=waitlist_ids, **overrides),
    )


def test_free_slots_are_booked_and_full_ones_go_on_the_waitlist(client, db, fill_slot, outbox):
    full = slot(db, 14)
    fill_slot(full)
    outbox.sent.clear()
    response = register(client, [slot(db, 13).id], [full.id])
    assert response.status_code == 201
    body = response.json()
    assert body["result"] == "created"
    assert [s["label"] for s in body["booking"]["slots"]] == ["lun 13/07 mattina (09:00-13:00)"]
    assert body["booking"]["amount_due_cents"] == 1100
    assert body["waitlist"] == [
        {
            "date": "2026-07-14",
            "period": "morning",
            "label": "mar 14/07 mattina (09:00-13:00)",
            "position": 1,
        }
    ]
    [email] = outbox.sent
    assert "Sei in lista d'attesa per:" in email.body
    assert "mar 14/07 mattina" in email.body


def test_only_full_slots_register_the_person_without_a_booking(
    client, db, fill_slot, outbox, edition
):
    full = slot(db, 14)
    fill_slot(full)
    outbox.sent.clear()
    response = register(client, [], [full.id])
    assert response.status_code == 201
    body = response.json()
    assert body["result"] == "waitlisted"
    assert body["booking"] is None
    assert body["personal_code"].startswith("CSC-")
    ada = db.scalar(select(Participant).where(Participant.email == "ada@example.com"))
    assert db.scalar(select(Booking).where(Booking.participant_id == ada.id)) is None
    entry = db.scalar(select(WaitlistEntry).where(WaitlistEntry.participant_id == ada.id))
    privacy = edition_service.latest_legal_document(db, edition, "privacy")
    assert entry.privacy_document_id == privacy.id
    assert entry.privacy_accepted_at is not None
    [email] = outbox.sent
    assert email.subject == "Sei in lista d'attesa al Cissonauti Summer Camp 2026"
    assert "non devi pagare nulla" in email.body
    assert "/accesso?token=" in email.body or "token=" in email.body


def test_a_full_list_saves_nothing(client, db, fill_slot, edition, outbox):
    full = slot(db, 14)
    fill_slot(full)
    edition.waitlist_percent = 0
    db.commit()
    outbox.sent.clear()
    response = register(client, [slot(db, 13).id], [full.id])
    assert response.status_code == 409
    assert "lista d'attesa si è riempita" in response.json()["detail"]
    assert db.scalar(select(Participant).where(Participant.email == "ada@example.com")) is None
    assert db.scalar(select(Booking)).participant.email.startswith("filler")
    assert outbox.sent == []


def test_a_slot_that_freed_up_meanwhile_saves_nothing(client, db, edition):
    response = register(client, [], [slot(db, 14).id])
    assert response.status_code == 409
    assert "si è liberato un posto" in response.json()["detail"]
    assert db.scalar(select(WaitlistEntry)) is None


def test_someone_already_on_a_waitlist_only_gets_the_link(client, db, fill_slot, outbox):
    full = slot(db, 14)
    fill_slot(full)
    register(client, [], [full.id])
    outbox.sent.clear()
    response = register(client, [slot(db, 15).id], [])
    assert response.json()["result"] == "already_registered"
    assert db.scalar(select(Booking).where(Booking.slots.any(Slot.id == slot(db, 15).id))) is None
    [email] = outbox.sent
    assert email.subject == "Sei già iscritto al Cissonauti Summer Camp 2026"


def test_new_anonymous_registration_does_not_change_existing_participant_phone(
    client, db, make_participant, make_booking
):
    ada = make_participant("ada@example.com", phone=None)
    make_booking(ada, [slot(db, 13)], status=STATUS_EXPIRED)

    response = register(client, [slot(db, 14).id], [], phone="+39 333 1234567")

    assert response.status_code == 201
    assert response.json()["result"] == "created"
    db.refresh(ada)
    assert ada.phone is None


def test_already_registered_does_not_save_phone_before_a_new_registration(
    client, db, make_participant, make_booking
):
    ada = make_participant("ada@example.com", phone=None)
    make_booking(ada, [slot(db, 13)], status=STATUS_PENDING)

    response = register(client, [slot(db, 14).id], [], phone="+39 333 1234567")

    assert response.status_code == 201
    assert response.json()["result"] == "already_registered"
    db.refresh(ada)
    assert ada.phone is None


def test_at_least_one_slot_is_needed(client, edition):
    response = register(client, [], [])
    assert response.status_code == 422


def test_unknown_waitlist_slot_is_rejected(client, edition):
    response = register(client, [], [999999])
    assert response.status_code == 422
