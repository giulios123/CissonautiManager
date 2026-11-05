from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import CLOSE_LEFT, STATUS_EXPIRED, Slot, WaitlistEntry
from app.services import edition as edition_service
from tests.helpers import d
from tests.test_auth import login


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


@pytest.fixture
def ada(make_participant):
    return make_participant("ada@example.com")


@pytest.fixture
def member(client, outbox, ada, db, make_booking):
    """Ada, logged in, with a booking on Monday afternoon."""
    make_booking(ada, [slot(db, 13, "afternoon")])
    login(client, outbox)
    return client


def join(client, slot_id):
    return client.post("/api/me/waitlist", json={"slot_id": slot_id})


def test_join_a_full_slot_and_see_the_position(member, db, fill_slot):
    full = slot(db, 14)
    fill_slot(full)
    response = join(member, full.id)
    assert response.status_code == 201, response.json()
    assert response.json()["position"] == 1
    waitlist = member.get("/api/me").json()["waitlist"]
    assert [(w["slot_id"], w["position"]) for w in waitlist] == [(full.id, 1)]
    assert waitlist[0]["label"] == "mar 14/07 mattina (09:00-13:00)"


def test_the_entry_keeps_the_legal_texts_of_the_booking(member, db, fill_slot, ada, edition):
    full = slot(db, 14)
    fill_slot(full)
    join(member, full.id)
    entry = db.scalar(select(WaitlistEntry))
    privacy = edition_service.latest_legal_document(db, edition, "privacy")
    assert entry.participant_id == ada.id
    assert entry.privacy_document_id == privacy.id


def test_second_person_is_second(member, db, fill_slot, make_participant, add_entry, clock):
    full = slot(db, 14)
    fill_slot(full)
    add_entry(full, make_participant("first@example.com"), clock() - timedelta(minutes=5))
    assert join(member, full.id).json()["position"] == 2


@pytest.mark.parametrize(
    ("setup", "message"),
    [
        ("free", "ancora posti liberi"),
        ("list_full", "completa"),
        ("booked", "Hai già questo slot"),
        ("twice", "Sei già in lista"),
    ],
)
def test_join_refusals(member, db, fill_slot, setup, message, edition):
    target = slot(db, 14)
    if setup == "booked":
        target = slot(db, 13, "afternoon")
        fill_slot(target, capacity=1)
        target.capacity = 1
        db.commit()
    elif setup != "free":
        fill_slot(target)
    if setup == "list_full":
        edition.waitlist_percent = 0
        db.commit()
    if setup == "twice":
        assert join(member, target.id).status_code == 201
    response = join(member, target.id)
    assert response.status_code == 409
    assert message in response.json()["detail"]
    entries = db.scalars(select(WaitlistEntry).where(WaitlistEntry.slot_id == target.id)).all()
    assert len(entries) == (1 if setup == "twice" else 0)


def test_the_evening_has_no_waitlist(member, db):
    response = join(member, slot(db, 14, "evening").id)
    assert response.status_code == 409


def test_past_day_refused(member, db, fill_slot, clock):
    full = slot(db, 13)
    fill_slot(full)
    clock.advance(days=13)  # 14 July
    response = join(member, full.id)
    assert response.status_code == 409
    assert "passato" in response.json()["detail"]


def test_leave_moves_the_others_up(member, db, fill_slot, make_participant, add_entry, clock):
    full = slot(db, 14)
    fill_slot(full)
    join(member, full.id)
    add_entry(full, make_participant("bea@example.com"), clock() + timedelta(minutes=1))
    mine = member.get("/api/me").json()["waitlist"][0]
    assert member.delete(f"/api/me/waitlist/{mine['id']}").status_code == 204
    assert member.get("/api/me").json()["waitlist"] == []
    entries = db.scalars(select(WaitlistEntry).order_by(WaitlistEntry.id)).all()
    db.refresh(entries[0])
    assert entries[0].close_reason == CLOSE_LEFT
    assert entries[1].closed_at is None


def test_cannot_leave_someone_elses_entry(
    member, db, fill_slot, make_participant, add_entry, clock
):
    full = slot(db, 14)
    fill_slot(full)
    entry = add_entry(full, make_participant("bea@example.com"), clock())
    assert member.delete(f"/api/me/waitlist/{entry.id}").status_code == 404


def test_without_any_registration_joining_is_refused(
    client, outbox, make_participant, db, fill_slot
):
    make_participant("ada@example.com")
    login(client, outbox)
    full = slot(db, 14)
    fill_slot(full)
    response = join(client, full.id)
    assert response.status_code == 409
    assert "modulo" in response.json()["detail"]


def test_expired_booking_still_provides_the_legal_texts(
    client, outbox, ada, db, make_booking, fill_slot, clock
):
    make_booking(
        ada,
        [slot(db, 13, "afternoon")],
        status=STATUS_EXPIRED,
        hold_expires_at=clock() - timedelta(hours=1),
    )
    login(client, outbox)
    full = slot(db, 14)
    fill_slot(full)
    assert join(client, full.id).status_code == 201


def test_public_edition_shows_places_left_on_the_waitlist(member, db, fill_slot):
    full = slot(db, 14)
    fill_slot(full, capacity=10)  # 20% of 10 = 2 places on the list
    join(member, full.id)
    days = member.get("/api/public/edition").json()["days"]
    by_id = {s["id"]: s for day in days for s in day["slots"]}
    assert by_id[full.id]["waitlist_free"] == 1
    assert by_id[slot(db, 15).id]["waitlist_free"] is None
