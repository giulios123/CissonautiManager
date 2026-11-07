from datetime import timedelta

from sqlalchemy import select

from app.models import (
    STATUS_EXPIRED,
    ConsentEvent,
    LegalDocument,
    Participant,
    Slot,
)
from tests.helpers import d, payload


def publish_optional_documents(db, edition):
    documents = {}
    for kind, body_it, body_en in (
        ("attendance", "Presenza", "Attendance"),
        ("media", "Foto e video", "Photos and videos"),
    ):
        document = LegalDocument(
            edition_id=edition.id,
            kind=kind,
            version=1,
            body=body_it,
            body_it=body_it,
            body_en=body_en,
        )
        db.add(document)
        documents[kind] = document
    db.commit()
    return documents


def choices(documents, *, attendance=True, media=False):
    return {
        "attendance": {
            "granted": attendance,
            "document_id": documents["attendance"].id,
            "version": documents["attendance"].version,
        },
        "media": {
            "granted": media,
            "document_id": documents["media"].id,
            "version": documents["media"].version,
        },
    }


def test_new_registration_records_each_optional_choice_once_for_the_person(
    client, db, edition, slot_ids, clock
):
    documents = publish_optional_documents(db, edition)
    response = client.post(
        "/api/public/registrations",
        json=payload(
            [slot_ids[(d(13), "morning")], slot_ids[(d(13), "afternoon")]],
            optional_consents=choices(documents),
            consent_locale="en",
        ),
    )

    assert response.status_code == 201
    events = db.scalars(select(ConsentEvent).order_by(ConsentEvent.id)).all()
    assert [(event.kind, event.action) for event in events] == [
        ("attendance", "granted"),
        ("media", "declined"),
    ]
    participant_id = db.scalar(select(Participant.id).where(Participant.email == "ada@example.com"))
    assert {event.participant_id for event in events} == {participant_id}
    assert {event.edition_id for event in events} == {edition.id}
    assert {event.locale for event in events} == {"en"}
    assert {event.source for event in events} == {"public_registration"}
    assert {event.recorded_at for event in events} == {clock()}


def test_waitlist_only_registration_records_the_same_pair_without_a_booking(
    client, db, edition, fill_slot, slot_ids
):
    documents = publish_optional_documents(db, edition)
    full_slots = [
        db.get(Slot, slot_ids[(d(14), "morning")]),
        db.get(Slot, slot_ids[(d(15), "morning")]),
    ]
    for full_slot in full_slots:
        fill_slot(full_slot)

    response = client.post(
        "/api/public/registrations",
        json=payload(
            [],
            waitlist_slot_ids=[full_slot.id for full_slot in full_slots],
            optional_consents=choices(documents),
            consent_locale="it",
        ),
    )

    assert response.status_code == 201
    assert response.json()["result"] == "waitlisted"
    assert len(db.scalars(select(ConsentEvent)).all()) == 2
    person = db.scalar(select(Participant).where(Participant.email == "ada@example.com"))
    assert person is not None
    assert all(event.participant_id == person.id for event in db.scalars(select(ConsentEvent)))


def test_omitted_optional_choices_leave_no_event(client, db, edition, slot_ids):
    publish_optional_documents(db, edition)

    response = client.post(
        "/api/public/registrations",
        json=payload([slot_ids[(d(13), "morning")]]),
    )

    assert response.status_code == 201
    assert db.scalars(select(ConsentEvent)).all() == []


def test_full_slot_rolls_back_person_booking_and_optional_events(
    client, db, edition, slot_ids, fill_slot
):
    documents = publish_optional_documents(db, edition)
    sid = slot_ids[(d(13), "morning")]
    fill_slot(db.get(Slot, sid))

    response = client.post(
        "/api/public/registrations",
        json=payload([sid], optional_consents=choices(documents)),
    )

    assert response.status_code == 409
    assert db.scalar(select(Participant).where(Participant.email == "ada@example.com")) is None
    assert db.scalars(select(ConsentEvent)).all() == []


def test_new_optional_text_published_after_form_load_requires_refresh(
    client, db, edition, admin_client, slot_ids
):
    documents = publish_optional_documents(db, edition)
    first = documents["attendance"]
    admin_client.post(
        "/api/admin/legal-documents",
        json={"kind": "attendance", "body_it": "Nuova presenza", "body_en": "New attendance"},
    )

    response = client.post(
        "/api/public/registrations",
        json=payload(
            [slot_ids[(d(13), "morning")]],
            optional_consents={
                "attendance": {
                    "granted": True,
                    "document_id": first.id,
                    "version": first.version,
                }
            },
        ),
    )

    assert response.status_code == 409
    assert db.scalar(select(Participant).where(Participant.email == "ada@example.com")) is None
    assert db.scalars(select(ConsentEvent)).all() == []


def test_existing_active_account_cannot_change_choices_or_recover_its_code(
    client, db, edition, make_participant, make_booking, slot_ids, clock
):
    documents = publish_optional_documents(db, edition)
    ada = make_participant("ada@example.com")
    make_booking(ada, [db.get(Slot, slot_ids[(d(13), "morning")])])
    db.add(
        ConsentEvent(
            edition_id=edition.id,
            participant_id=ada.id,
            kind="attendance",
            action="granted",
            document_id=documents["attendance"].id,
            locale="it",
            source="self_service",
            recorded_at=clock(),
        )
    )
    db.commit()

    response = client.post(
        "/api/public/registrations",
        json=payload(
            [slot_ids[(d(14), "morning")]],
            optional_consents=choices(documents, attendance=False),
        ),
    )

    assert response.json()["result"] == "already_registered"
    assert response.json()["personal_code"] is None
    assert "CSC-" not in response.text
    assert "ada@example.com" not in response.text
    assert "Ada" not in response.text
    db.refresh(db.scalar(select(ConsentEvent)))
    assert db.scalar(select(ConsentEvent)).action == "granted"


def test_returning_existing_account_gets_personal_code_only_by_email(
    client, db, edition, make_participant, make_booking, slot_ids, clock, outbox
):
    documents = publish_optional_documents(db, edition)
    ada = make_participant("ada@example.com")
    old = make_booking(
        ada,
        [db.get(Slot, slot_ids[(d(13), "morning")])],
        status=STATUS_EXPIRED,
        hold_expires_at=clock() - timedelta(days=1),
    )

    response = client.post(
        "/api/public/registrations",
        json=payload([slot_ids[(d(14), "morning")]], optional_consents=choices(documents)),
    )

    assert response.status_code == 201
    assert response.json()["result"] == "created"
    assert response.json()["personal_code"] is None
    assert response.json()["booking"]["personal_code"] is None
    assert response.json()["message"]
    assert old.participant.personal_code not in response.text
    assert len(outbox.sent) == 1
    assert old.participant.personal_code in outbox.sent[0].body
    assert db.scalars(select(ConsentEvent)).all() == []
