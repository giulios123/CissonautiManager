from datetime import timedelta

import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.jobs import send_reminders
from app.jobs.send_reminders import send_due_reminders
from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    Booking,
    Slot,
)
from tests.helpers import d
from tests.test_change_slots import pay

MORNING = "morning"


@pytest.fixture
def booking(db, make_participant, make_booking, slot_ids):
    """Pending booking of 11 euro, 3 day hold starting at the fake clock."""
    return make_booking(
        make_participant("ada@example.com"), [db.get(Slot, slot_ids[(d(13), MORNING)])]
    )


def run(db, outbox, settings, clock):
    return send_due_reminders(db, outbox, settings, clock())


def subjects(outbox):
    return [message.subject for message in outbox.sent]


def test_nothing_is_sent_before_half_of_the_hold(db, booking, outbox, settings, clock):
    clock.advance(hours=35)
    summary = run(db, outbox, settings, clock)
    assert outbox.sent == []
    assert (summary.examined, summary.mid, summary.final) == (1, 0, 0)


def test_middle_reminder_goes_out_once(db, booking, outbox, settings, clock):
    clock.advance(hours=36)
    summary = run(db, outbox, settings, clock)
    assert (summary.mid, summary.final) == (1, 0)
    assert subjects(outbox) == ["Promemoria: il tuo posto al Cissonauti Summer Camp"]
    clock.advance(hours=1)
    run(db, outbox, settings, clock)
    assert len(outbox.sent) == 1  # a rerun sends nothing more
    db.refresh(booking)
    assert booking.reminder_mid_sent_at is not None
    assert booking.reminder_final_sent_at is None


def test_final_reminder_follows_and_then_nothing(db, booking, outbox, settings, clock):
    clock.advance(hours=36)
    run(db, outbox, settings, clock)
    clock.advance(hours=12)  # 48 hours in, 24 before the deadline
    summary = run(db, outbox, settings, clock)
    assert summary.final == 1
    assert subjects(outbox)[-1].startswith("Ultimo promemoria")
    clock.advance(hours=11)
    run(db, outbox, settings, clock)
    assert len(outbox.sent) == 2


def test_a_late_run_sends_only_the_final_reminder(db, booking, outbox, settings, clock):
    clock.advance(hours=60)
    run(db, outbox, settings, clock)
    assert len(outbox.sent) == 1
    assert subjects(outbox)[0].startswith("Ultimo promemoria")


def test_reminder_names_the_balance_the_code_and_the_deadline(db, booking, outbox, settings, clock):
    pay(db, booking, 300)
    clock.advance(hours=36)
    run(db, outbox, settings, clock)
    body = outbox.sent[0].body
    assert outbox.sent[0].to == "ada@example.com"
    assert "8,00 €" in body  # 11,00 due minus 3,00 paid
    assert booking.participant.personal_code in body
    assert "04/07/2026" in body
    assert "https://camp.example.org/login" in body


@pytest.mark.parametrize("status", [STATUS_CONFIRMED, STATUS_EXPIRED, STATUS_CANCEL_REQUESTED])
def test_no_reminder_for_bookings_that_are_not_pending(
    db, booking, outbox, settings, clock, status
):
    booking.status = status
    db.commit()
    clock.advance(hours=40)
    run(db, outbox, settings, clock)
    assert outbox.sent == []


def test_no_reminder_when_payments_already_cover_the_amount(db, booking, outbox, settings, clock):
    pay(db, booking, 1100)
    clock.advance(hours=40)
    run(db, outbox, settings, clock)
    assert outbox.sent == []


def test_no_reminder_after_the_deadline(db, booking, outbox, settings, clock):
    clock.advance(days=4)
    summary = run(db, outbox, settings, clock)
    assert outbox.sent == []
    assert summary.examined == 0
    db.refresh(booking)
    assert booking.status == STATUS_EXPIRED  # the job also materialises the expiry


def test_a_reactivated_booking_gets_its_reminders_again(
    admin_client, db, booking, outbox, settings, clock
):
    clock.advance(hours=36)
    run(db, outbox, settings, clock)
    assert len(outbox.sent) == 1
    clock.advance(days=3)  # expired
    assert (
        admin_client.post(
            f"/api/admin/registrations/{booking.id}/payments",
            json={"amount_cents": 500, "channel": "iban"},
        ).status_code
        == 201
    )
    clock.advance(hours=36)
    db.expire_all()  # the real job opens a fresh session on every run
    run(db, outbox, settings, clock)
    assert len(outbox.sent) == 2


def test_a_reminder_claimed_by_another_run_in_the_meantime_is_not_sent(
    db, booking, outbox, settings, clock, engine, monkeypatch
):
    clock.advance(hours=36)
    real_due_reminder = send_reminders.due_reminder

    def racing(*args):
        kind = real_due_reminder(*args)
        with Session(engine) as other:  # a second run marks the reminder first
            other.execute(update(Booking).values(reminder_mid_sent_at=clock()))
            other.commit()
        return kind

    monkeypatch.setattr(send_reminders, "due_reminder", racing)
    summary = run(db, outbox, settings, clock)
    assert outbox.sent == []
    assert summary.mid == 0


def test_main_runs_with_settings_from_the_environment(
    settings, engine, outbox, booking, clock, monkeypatch, caplog
):
    clock.advance(hours=36)
    monkeypatch.setattr(send_reminders, "get_settings", lambda: settings)
    monkeypatch.setattr(send_reminders, "build_email_sender", lambda _: outbox)
    monkeypatch.setattr(send_reminders, "utcnow", clock)
    with caplog.at_level("INFO", logger="app.jobs.send_reminders"):
        send_reminders.main()
    assert len(outbox.sent) == 1
    assert "mid=1" in caplog.text
    assert "waitlist promotions=0" in caplog.text


@pytest.mark.parametrize(
    "change",
    [
        lambda b, clock: setattr(b, "status", STATUS_CONFIRMED),
        lambda b, clock: setattr(b, "status", STATUS_CANCEL_REQUESTED),
        lambda b, clock: setattr(b, "hold_expires_at", b.hold_expires_at + timedelta(days=3)),
        lambda b, clock: setattr(b, "amount_due_cents", b.amount_due_cents + 100),
    ],
    ids=["paid", "cancelled", "hold extended", "amount changed"],
)
def test_a_reminder_is_not_sent_if_the_booking_changed_after_it_was_evaluated(
    db, booking, outbox, settings, clock, engine, monkeypatch, change
):
    clock.advance(hours=36)
    real_due_reminder = send_reminders.due_reminder

    def racing(*args):
        kind = real_due_reminder(*args)
        with Session(engine) as other:  # another request changes the booking in the meantime
            change(other.get(Booking, booking.id), clock)
            other.commit()
        return kind

    monkeypatch.setattr(send_reminders, "due_reminder", racing)
    summary = run(db, outbox, settings, clock)
    assert outbox.sent == []
    assert summary.mid == 0
    db.expire_all()
    assert db.get(Booking, booking.id).reminder_mid_sent_at is None  # nothing was consumed


def test_a_seat_freed_by_an_expired_hold_goes_to_the_first_waiting(
    db, outbox, settings, clock, fill_slot, make_participant, add_entry, slot_ids
):
    target = db.get(Slot, slot_ids[(d(14), MORNING)])
    fillers = fill_slot(target)
    fillers[0].hold_expires_at = clock() + timedelta(hours=1)
    db.commit()
    bea = make_participant("bea@example.com")
    entry = add_entry(target, bea, clock())
    outbox.sent.clear()

    assert run(db, outbox, settings, clock).promoted == 0
    clock.advance(hours=2)
    summary = run(db, outbox, settings, clock)

    assert summary.promoted == 1
    db.refresh(entry)
    assert entry.promoted_booking_id is not None
    assert "Si è liberato un posto al Cissonauti Summer Camp" in subjects(outbox)
    # A second run finds nothing left to hand out.
    assert run(db, outbox, settings, clock).promoted == 0
