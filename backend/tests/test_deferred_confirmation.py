from datetime import timedelta

import pytest
from sqlalchemy import select

from app.jobs.send_reminders import send_due_reminders
from app.models import STATUS_CONFIRMED, STATUS_EXPIRED, STATUS_PENDING, Payment, Slot
from app.services.payments import send_due_confirmations
from tests.helpers import d


@pytest.fixture
def booking(db, make_participant, make_booking, slot_ids):
    return make_booking(
        make_participant("ada@example.com"), [db.get(Slot, slot_ids[(d(13), "morning")])]
    )


def pay(client, booking, **extra):
    body = {"amount_cents": 1100, "channel": "iban", **extra}
    return client.post(f"/api/admin/registrations/{booking.id}/payments", json=body)


def confirmations(outbox):
    return [m for m in outbox.sent if m.subject.startswith("Pagamento ricevuto")]


def test_without_the_flag_the_email_goes_out_at_once(admin_client, booking, outbox, db):
    assert pay(admin_client, booking).status_code == 201
    assert len(confirmations(outbox)) == 1
    assert db.scalars(select(Payment)).one().confirmation_email_due_at is None


def test_with_the_flag_the_booking_is_confirmed_but_the_email_waits(
    admin_client, booking, outbox, db, app, clock
):
    response = pay(admin_client, booking, defer_confirmation_email=True)
    assert response.status_code == 201
    assert response.json()["booking"]["status"] == STATUS_CONFIRMED
    assert confirmations(outbox) == []
    payment = db.scalars(select(Payment)).one()
    assert payment.confirmation_email_due_at == clock() + timedelta(seconds=30)
    # The app asks to be called back once the delay is over.
    assert [delay for delay, _ in app.state.scheduled] == [30.0]


def test_the_timer_sends_the_email_once_the_delay_is_over(
    admin_client, booking, outbox, app, clock
):
    pay(admin_client, booking, defer_confirmation_email=True)
    _, run = app.state.scheduled[0]
    clock.advance(seconds=29)
    run()
    assert confirmations(outbox) == []
    clock.advance(seconds=2)
    run()
    run()  # a second run must not send it again
    assert len(confirmations(outbox)) == 1


def test_a_voided_payment_never_sends_its_email(admin_client, booking, outbox, app, clock, db):
    pay(admin_client, booking, defer_confirmation_email=True)
    payment = db.scalars(select(Payment)).one()
    clock.advance(seconds=5)
    response = admin_client.post(
        f"/api/admin/registrations/{booking.id}/payments/{payment.id}/void",
        json={"reason": "Annullato subito dalla vista Da incassare"},
    )
    assert response.status_code == 200
    assert response.json()["booking"]["status"] == STATUS_PENDING
    clock.advance(seconds=60)
    app.state.scheduled[0][1]()
    assert confirmations(outbox) == []


def test_a_booking_no_longer_confirmed_gets_no_email(admin_client, booking, outbox, app, clock, db):
    pay(admin_client, booking, defer_confirmation_email=True)
    db.refresh(booking)
    booking.status = STATUS_EXPIRED
    db.commit()
    clock.advance(seconds=31)
    assert send_due_confirmations(db, outbox, clock()) == 0
    assert confirmations(outbox) == []


def test_the_hourly_job_sends_what_the_timer_missed(
    admin_client, booking, outbox, db, settings, clock
):
    pay(admin_client, booking, defer_confirmation_email=True)
    clock.advance(minutes=40)
    summary = send_due_reminders(db, outbox, settings, clock())
    assert summary.confirmations == 1
    assert len(confirmations(outbox)) == 1
    # And a timer that wakes up afterwards finds nothing left to send.
    assert send_due_confirmations(db, outbox, clock()) == 0


def test_a_payment_that_does_not_confirm_sends_nothing_even_with_the_flag(
    admin_client, booking, outbox, app, clock
):
    response = pay(admin_client, booking, amount_cents=500, defer_confirmation_email=True)
    assert response.json()["booking"]["status"] == STATUS_PENDING
    assert app.state.scheduled == []
    clock.advance(minutes=5)
    assert confirmations(outbox) == []
