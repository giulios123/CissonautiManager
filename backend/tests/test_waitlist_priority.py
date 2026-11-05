from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import CLOSE_PROMOTED, STATUS_CANCEL_REQUESTED, Booking, Slot
from app.services.waitlist import (
    LegalAcceptance,
    WaitlistRefused,
    active_entries,
    join,
    position_of,
    promote_freed,
)
from tests.helpers import d


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


@pytest.fixture
def full_monday(db, fill_slot):
    target = slot(db, 13)
    return target, fill_slot(target)


def free_one(db, bookings):
    bookings[0].status = STATUS_CANCEL_REQUESTED
    db.commit()


def queue_of(db, target):
    entries = active_entries(db, [target.id]).get(target.id, [])
    return [e.participant_id for e in entries]


@pytest.fixture
def two_waiting(db, full_monday, make_participant, add_entry, clock):
    """Ada waits since the morning, Bob since the afternoon."""
    target, fillers = full_monday
    ada = make_participant("ada@example.com", first_name="Ada")
    bob = make_participant("bob@example.com", first_name="Bob", invited_by="Ada")
    ada_entry = add_entry(target, ada, clock())
    bob_entry = add_entry(target, bob, clock() + timedelta(hours=5))
    return target, fillers, ada, bob, ada_entry, bob_entry


def test_without_a_verified_plus_one_the_first_to_arrive_goes_first(db, two_waiting):
    target, _fillers, ada, bob, _a, _b = two_waiting
    assert queue_of(db, target) == [ada.id, bob.id]


def test_a_verified_plus_one_gets_the_freed_seat_before_who_arrived_earlier(
    db, two_waiting, outbox, settings, clock
):
    target, fillers, ada, bob, ada_entry, bob_entry = two_waiting
    bob.plus_one_verified_at = clock()
    db.commit()
    free_one(db, fillers)
    outbox.sent.clear()

    [promotion] = promote_freed(db, outbox, settings, [target.id], clock())

    db.refresh(bob_entry)
    db.refresh(ada_entry)
    assert promotion.entry.id == bob_entry.id
    assert bob_entry.close_reason == CLOSE_PROMOTED
    assert ada_entry.closed_at is None
    [email] = outbox.sent
    assert email.to == "bob@example.com"
    booking = db.scalar(select(Booking).where(Booking.participant_id == bob.id))
    assert booking is not None and [s.id for s in booking.slots] == [target.id]


def test_a_verification_done_after_joining_counts_from_the_next_promotion(db, two_waiting, clock):
    target, _fillers, ada, bob, _a, bob_entry = two_waiting
    assert position_of(db, bob_entry) == 2
    bob.plus_one_verified_at = clock() + timedelta(days=1)
    db.commit()
    assert position_of(db, bob_entry) == 1
    assert queue_of(db, target) == [bob.id, ada.id]


def test_removing_the_verification_restores_the_arrival_order(db, two_waiting, clock):
    target, _fillers, ada, bob, _a, _b = two_waiting
    bob.plus_one_verified_at = clock()
    db.commit()
    assert queue_of(db, target) == [bob.id, ada.id]
    bob.plus_one_verified_at = None
    db.commit()
    assert queue_of(db, target) == [ada.id, bob.id]


def test_two_verified_plus_ones_keep_their_arrival_order(
    db, two_waiting, make_participant, add_entry, clock
):
    target, _fillers, ada, bob, _a, _b = two_waiting
    cleo = make_participant("cleo@example.com", first_name="Cleo", invited_by="Bob")
    add_entry(target, cleo, clock() + timedelta(hours=9))
    cleo.plus_one_verified_at = clock()
    bob.plus_one_verified_at = clock()
    db.commit()
    assert queue_of(db, target) == [bob.id, cleo.id, ada.id]


def test_the_priority_never_lets_a_plus_one_into_a_full_list(
    db, two_waiting, make_participant, clock
):
    target, _fillers, _ada, _bob, _a, _b = two_waiting  # 10 seats, 20%: the list holds 2
    dina = make_participant("dina@example.com", first_name="Dina", invited_by="Ada")
    dina.plus_one_verified_at = clock()
    db.commit()
    ada_entry = active_entries(db, [target.id])[target.id][0]
    legal = LegalAcceptance(
        ada_entry.privacy_document_id,
        ada_entry.privacy_accepted_at,
        ada_entry.disclaimer_document_id,
        ada_entry.disclaimer_accepted_at,
    )
    with pytest.raises(WaitlistRefused) as refused:
        join(db, dina, target.id, clock(), legal)
    assert refused.value.reason == "list_full"
