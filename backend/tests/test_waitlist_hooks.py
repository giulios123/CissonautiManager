"""Every way a seat frees up hands it to the first person waiting."""

from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import (
    CLOSE_BOOKED,
    CLOSE_CANCELLED,
    CLOSE_PROMOTED,
    Booking,
    Slot,
    WaitlistEntry,
)
from tests.helpers import d
from tests.test_admin_edition import PAYLOAD
from tests.test_auth import login

PROMOTED = "Si è liberato un posto al Cissonauti Summer Camp 2026"


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


@pytest.fixture
def waiting(db, fill_slot, make_participant, add_entry, clock):
    """Monday morning full (10 seats); Bea waits for it."""
    target = slot(db, 13)
    fillers = fill_slot(target)
    bea = make_participant("bea@example.com", first_name="Bea")
    entry = add_entry(target, bea, clock() - timedelta(hours=1))
    return target, fillers, entry


def promoted(db, entry) -> bool:
    db.refresh(entry)
    return entry.close_reason == CLOSE_PROMOTED


def subjects(outbox) -> list[str]:
    return [m.subject for m in outbox.sent]


def test_a_participant_cancelling_frees_the_seat(client, db, outbox, waiting):
    target, fillers, entry = waiting
    login(client, outbox, fillers[0].participant.email)
    outbox.sent.clear()
    assert client.post("/api/me/booking/cancel").status_code == 200
    assert promoted(db, entry)
    assert PROMOTED in subjects(outbox)


def test_a_participant_dropping_the_slot_frees_the_seat(client, db, outbox, waiting, make_booking):
    target, fillers, entry = waiting
    filler = fillers[0]
    filler.slots = [target, slot(db, 14)]
    db.commit()
    login(client, outbox, filler.participant.email)
    response = client.put("/api/me/booking/slots", json={"slot_ids": [slot(db, 14).id]})
    assert response.status_code == 200
    assert promoted(db, entry)


def test_an_admin_dropping_the_slot_frees_the_seat(admin_client, db, waiting):
    target, fillers, entry = waiting
    filler = fillers[0]
    filler.slots = [target, slot(db, 14)]
    db.commit()
    response = admin_client.put(
        f"/api/admin/registrations/{filler.id}/slots", json={"slot_ids": [slot(db, 14).id]}
    )
    assert response.status_code == 200
    assert promoted(db, entry)


def test_an_admin_cancelling_frees_the_seat(admin_client, db, waiting):
    target, fillers, entry = waiting
    assert admin_client.post(f"/api/admin/registrations/{fillers[0].id}/cancel").status_code == 200
    assert promoted(db, entry)


def test_a_larger_capacity_frees_seats(admin_client, db, waiting, edition):
    target, fillers, entry = waiting
    body = dict(PAYLOAD, start_date="2026-07-13", end_date="2026-07-17", default_capacity=25)
    assert admin_client.put("/api/admin/edition", json=body).status_code == 200
    assert promoted(db, entry)


def test_forcing_a_slot_over_capacity_promotes_nobody(
    admin_client, db, waiting, make_participant, make_booking
):
    target, fillers, entry = waiting
    other = make_booking(make_participant("cid@example.com"), [slot(db, 14)])
    response = admin_client.put(
        f"/api/admin/registrations/{other.id}/slots",
        json={"slot_ids": [slot(db, 14).id, target.id], "force": True},
    )
    assert response.status_code == 200
    db.refresh(entry)
    assert entry.closed_at is None


def test_cancelling_closes_the_persons_waitlist_entries_and_says_so(
    client, db, outbox, waiting, make_booking, fill_slot, add_entry, clock
):
    target, fillers, entry = waiting
    tuesday = slot(db, 14)
    fill_slot(tuesday)
    bea = entry.participant
    make_booking(bea, [slot(db, 15)])
    other_entry = add_entry(tuesday, bea, clock())
    login(client, outbox, "bea@example.com")
    outbox.sent.clear()
    client.post("/api/me/booking/cancel")
    for e in (entry, other_entry):
        db.refresh(e)
        assert e.close_reason == CLOSE_CANCELLED
    [email] = outbox.sent
    assert "Sei uscito anche dalle liste d'attesa" in email.body


def test_taking_the_slot_directly_leaves_its_waitlist(client, db, outbox, waiting, make_booking):
    target, fillers, entry = waiting
    bea = entry.participant
    make_booking(bea, [slot(db, 14)])
    # A seat frees up without promotion (e.g. an expiry the job has not handled yet).
    fillers[0].hold_expires_at = fillers[0].created_at
    db.commit()
    login(client, outbox, "bea@example.com")
    response = client.put("/api/me/booking/slots", json={"slot_ids": [slot(db, 14).id, target.id]})
    assert response.status_code == 200
    db.refresh(entry)
    assert entry.close_reason == CLOSE_BOOKED


def test_removing_a_day_with_waitlist_history_is_refused(admin_client, db, waiting, edition):
    target, fillers, entry = waiting
    for booking in fillers:
        booking.slots = []
    db.commit()
    body = dict(PAYLOAD, start_date="2026-07-14", end_date="2026-07-17")
    response = admin_client.put("/api/admin/edition", json=body)
    assert response.status_code == 409
    assert db.scalar(select(WaitlistEntry)).slot_id == target.id
    assert db.scalar(select(Booking)) is not None
