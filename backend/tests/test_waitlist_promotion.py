from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import (
    CLOSE_BOOKED,
    CLOSE_PROMOTED,
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    Booking,
    Payment,
    Slot,
)
from app.services import views as views_service
from app.services.waitlist import promote_freed
from tests.helpers import d


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


@pytest.fixture
def promote(db, outbox, settings, clock):
    def _promote(*slots):
        return promote_freed(db, outbox, settings, [s.id for s in slots], clock())

    return _promote


@pytest.fixture
def full_monday(db, fill_slot):
    """Monday morning with 10 seats, all taken; returns the slot and the fillers' bookings."""
    target = slot(db, 13)
    return target, fill_slot(target)


def free_one(db, bookings):
    bookings[0].status = STATUS_CANCEL_REQUESTED
    db.commit()


def test_pending_booking_gets_the_slot_a_longer_hold_and_the_new_amount(
    db, full_monday, make_participant, make_booking, add_entry, promote, clock, outbox
):
    target, fillers = full_monday
    ada = make_participant("ada@example.com")
    booking = make_booking(
        ada, [slot(db, 14)], hold_expires_at=clock() + timedelta(hours=2), amount_due_cents=1100
    )
    entry = add_entry(target, ada, clock())
    free_one(db, fillers)
    outbox.sent.clear()

    [promotion] = promote(target)

    db.refresh(booking)
    assert promotion.kind == "add_to_pending"
    assert [s.id for s in booking.slots] == [target.id, slot(db, 14).id]
    assert booking.amount_due_cents == 1200
    assert booking.status == STATUS_PENDING
    assert booking.hold_expires_at == clock() + timedelta(days=3)
    db.refresh(entry)
    assert entry.close_reason == CLOSE_PROMOTED
    assert entry.promoted_booking_id == booking.id
    [email] = outbox.sent
    assert email.subject == "Si è liberato un posto a Cissonauti Summer Camp 2026"
    assert "lun 13/07 mattina" in email.body
    assert "bloccato fino al" in email.body
    assert "Ancora da versare: 12,00 €" in email.body


def test_reminders_are_recomputed_as_after_an_extension(
    db, full_monday, make_participant, make_booking, add_entry, promote, clock
):
    target, fillers = full_monday
    ada = make_participant("ada@example.com")
    booking = make_booking(ada, [slot(db, 14)])
    clock.advance(days=2, hours=12)  # past the middle of the hold: the mid reminder went out
    booking.reminder_mid_sent_at = clock()
    db.commit()
    add_entry(target, ada, clock())
    free_one(db, fillers)
    promote(target)
    db.refresh(booking)
    # The hold is longer and its new middle is ahead: the reminder is due again, for the new
    # amount and deadline (same rule as an admin extension, D-024).
    assert booking.hold_expires_at == clock() + timedelta(days=3)
    assert booking.reminder_mid_sent_at is None


def test_the_hold_is_never_shortened(
    db, full_monday, make_participant, make_booking, add_entry, promote, clock
):
    target, fillers = full_monday
    ada = make_participant("ada@example.com")
    long_hold = clock() + timedelta(days=10)
    booking = make_booking(ada, [slot(db, 14)], hold_expires_at=long_hold)
    add_entry(target, ada, clock())
    free_one(db, fillers)
    promote(target)
    db.refresh(booking)
    assert booking.hold_expires_at == long_hold


def test_confirmed_booking_stays_confirmed_with_the_difference_to_pay(
    db, full_monday, make_participant, make_booking, add_entry, promote, clock, outbox
):
    target, fillers = full_monday
    ada = make_participant("ada@example.com")
    booking = make_booking(ada, [slot(db, 14)], status=STATUS_CONFIRMED, amount_due_cents=1100)
    db.add(
        Payment(
            booking_id=booking.id,
            amount_cents=1100,
            channel="iban",
            paid_on=d(1),
            recorded_by_id=ada.id,
        )
    )
    db.commit()
    add_entry(target, ada, clock())
    free_one(db, fillers)
    outbox.sent.clear()

    [promotion] = promote(target)

    db.refresh(booking)
    assert promotion.kind == "add_to_confirmed"
    assert booking.status == STATUS_CONFIRMED
    assert booking.amount_due_cents == 1200
    reasons = {r.booking_id: r.reason for r in views_service.review_rows(db, clock())}
    assert reasons[booking.id] == "saldo_positivo"
    [email] = outbox.sent
    assert "resta confermata" in email.body
    assert "Ancora da versare: 1,00 €" in email.body


def test_someone_only_on_the_list_gets_a_new_booking_with_the_texts_of_the_entry(
    db, full_monday, make_participant, add_entry, promote, clock, outbox
):
    target, fillers = full_monday
    bea = make_participant("bea@example.com")
    entry = add_entry(target, bea, clock() - timedelta(days=1))
    free_one(db, fillers)
    outbox.sent.clear()

    [promotion] = promote(target)

    booking = db.scalar(select(Booking).where(Booking.participant_id == bea.id))
    assert promotion.kind == "new_booking"
    assert booking.status == STATUS_PENDING
    assert [s.id for s in booking.slots] == [target.id]
    assert booking.amount_due_cents == 1100
    assert booking.hold_expires_at == clock() + timedelta(days=3)
    assert booking.privacy_document_id == entry.privacy_document_id
    assert booking.privacy_accepted_at == entry.privacy_accepted_at
    [email] = outbox.sent
    assert "accedi/verifica?token=" in email.body


def test_an_expired_booking_does_not_receive_the_slot(
    db, full_monday, make_participant, make_booking, add_entry, promote, clock
):
    target, fillers = full_monday
    ada = make_participant("ada@example.com")
    old = make_booking(
        ada, [slot(db, 14)], status=STATUS_EXPIRED, hold_expires_at=clock() - timedelta(hours=1)
    )
    add_entry(target, ada, clock())
    free_one(db, fillers)
    [promotion] = promote(target)
    assert promotion.kind == "new_booking"
    assert promotion.booking.id != old.id
    db.refresh(old)
    assert [s.id for s in old.slots] == [slot(db, 14).id]


def test_two_free_seats_promote_two_people_in_order(
    db, full_monday, make_participant, add_entry, promote, clock
):
    target, fillers = full_monday
    first = make_participant("first@example.com")
    second = make_participant("second@example.com")
    third = make_participant("third@example.com")
    add_entry(target, second, clock() - timedelta(minutes=5))
    add_entry(target, first, clock() - timedelta(minutes=10))
    add_entry(target, third, clock())
    target.capacity = 12
    db.commit()
    promotions = promote(target)
    assert [p.booking.participant_id for p in promotions] == [first.id, second.id]


def test_entries_on_other_slots_are_kept(
    db, full_monday, make_participant, add_entry, promote, clock, fill_slot
):
    target, fillers = full_monday
    tuesday = slot(db, 14)
    fill_slot(tuesday)
    bea = make_participant("bea@example.com")
    add_entry(target, bea, clock())
    other = add_entry(tuesday, bea, clock())
    free_one(db, fillers)
    promote(target)
    db.refresh(other)
    assert other.closed_at is None


def test_no_promotion_without_a_free_seat(
    db, full_monday, make_participant, add_entry, promote, clock
):
    target, _ = full_monday
    add_entry(target, make_participant("bea@example.com"), clock())
    assert promote(target) == []


def test_no_promotion_on_a_past_day(db, full_monday, make_participant, add_entry, promote, clock):
    target, fillers = full_monday
    entry = add_entry(target, make_participant("bea@example.com"), clock())
    free_one(db, fillers)
    clock.advance(days=13)  # 14 July: Monday is over
    assert promote(target) == []
    db.refresh(entry)
    assert entry.closed_at is None


def test_someone_who_already_has_the_slot_is_skipped(
    db, full_monday, make_participant, make_booking, add_entry, promote, clock
):
    target, fillers = full_monday
    ada = make_participant("ada@example.com")
    bea = make_participant("bea@example.com")
    make_booking(ada, [target])  # forced in by an admin, over capacity
    first = add_entry(target, ada, clock() - timedelta(minutes=1))
    add_entry(target, bea, clock())
    fillers[0].status = STATUS_CANCEL_REQUESTED
    fillers[1].status = STATUS_CANCEL_REQUESTED
    db.commit()
    [promotion] = promote(target)
    assert promotion.booking.participant_id == bea.id
    db.refresh(first)
    assert first.close_reason == CLOSE_BOOKED
