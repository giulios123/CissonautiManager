from datetime import timedelta

from sqlalchemy import func, select

from app.domain.confirmation import POLICY_LEGACY_TOTAL, POLICY_REGISTRATION_FEE
from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_PENDING,
    AuditLog,
    BookingMeal,
    Payment,
)
from app.services.payments import send_due_confirmations
from tests.helpers import d

PREVIEW = "/api/admin/edition/confirmation-policy/preview"
ACTIVATE = "/api/admin/edition/confirmation-policy/activate"


def test_preview_and_activation_are_admin_only(client, make_participant, outbox):
    assert client.get(PREVIEW).status_code == 401
    assert client.post(ACTIVATE, json={"preview_token": "0" * 64}).status_code == 401

    make_participant("ada@example.com")
    from tests.test_auth import login

    login(client, outbox)
    assert client.get(PREVIEW).status_code == 403
    assert client.post(ACTIVATE, json={"preview_token": "0" * 64}).status_code == 403


def slot_on(db, day):
    from app.models import Slot

    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == "morning"))


def payment(client, booking_id, cents, defer_confirmation_email=False):
    return client.post(
        f"/api/admin/registrations/{booking_id}/payments",
        json={
            "amount_cents": cents,
            "channel": "iban",
            "defer_confirmation_email": defer_confirmation_email,
        },
    )


def test_preview_shows_repricing_without_writing_or_expiring_bookings(
    admin_client,
    db,
    edition,
    make_participant,
    make_booking,
    clock,
):
    pending = make_booking(
        make_participant("ada@example.com"), [slot_on(db, 13)], amount_due_cents=2500
    )
    pending.meals = [BookingMeal(date=d(13), kind="lunch")]
    db.commit()
    payment(admin_client, pending.id, 1100)
    expired = make_booking(
        make_participant("expired@example.com"),
        [slot_on(db, 14)],
        status=STATUS_PENDING,
        hold_expires_at=clock() - timedelta(minutes=1),
    )
    closed = make_booking(
        make_participant("closed@example.com"),
        [slot_on(db, 15)],
        status=STATUS_CANCEL_REQUESTED,
    )

    response = admin_client.get(PREVIEW)

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    data = response.json()
    assert data["ready"] is True and data["current_policy"] == POLICY_LEGACY_TOTAL
    assert len(data["preview_token"]) == 64
    assert data["eligible_count"] == 1
    assert (data["excluded_expired_count"], data["excluded_closed_count"]) == (1, 1)
    assert data["new_confirmation_count"] == 1
    [row] = data["rows"]
    assert (row["registration_fee_cents"], row["amount_due_cents"], row["paid_cents"]) == (
        1100,
        1900,
        1100,
    )
    assert (row["balance_before_cents"], row["balance_after_cents"]) == (1400, 800)
    assert row["status_after"] == STATUS_CONFIRMED

    db.refresh(edition)
    db.refresh(pending)
    db.refresh(expired)
    db.refresh(closed)
    assert edition.confirmation_policy == POLICY_LEGACY_TOTAL
    assert (pending.status, pending.amount_due_cents, pending.registration_fee_cents) == (
        STATUS_PENDING,
        2500,
        None,
    )
    assert (expired.status, closed.status) == (STATUS_PENDING, STATUS_CANCEL_REQUESTED)


def test_apply_is_atomic_preserves_payments_and_is_idempotent(
    admin_client,
    db,
    edition,
    make_participant,
    make_booking,
    clock,
    outbox,
):
    covered = make_booking(
        make_participant("ada@example.com"), [slot_on(db, 13)], amount_due_cents=2500
    )
    covered.meals = [BookingMeal(date=d(13), kind="lunch")]
    hold_expires_at = covered.hold_expires_at
    db.commit()
    payment(admin_client, covered.id, 1100)
    confirmed = make_booking(
        make_participant("bob@example.com"),
        [slot_on(db, 14)],
        status=STATUS_CONFIRMED,
        amount_due_cents=3000,
    )
    cancelled = make_booking(
        make_participant("cid@example.com"),
        [slot_on(db, 15)],
        status=STATUS_CANCEL_REQUESTED,
        amount_due_cents=3000,
    )
    preview = admin_client.get(PREVIEW).json()

    response = admin_client.post(ACTIVATE, json={"preview_token": preview["preview_token"]})

    assert response.status_code == 200, response.text
    result = response.json()
    assert (result["already_applied"], result["updated_bookings"], result["new_confirmations"]) == (
        False,
        2,
        1,
    )
    db.refresh(edition)
    db.refresh(covered)
    db.refresh(confirmed)
    db.refresh(cancelled)
    assert edition.confirmation_policy == POLICY_REGISTRATION_FEE
    assert edition.confirmation_policy_activated_at == clock()
    assert (covered.status, covered.registration_fee_cents, covered.amount_due_cents) == (
        STATUS_CONFIRMED,
        1100,
        1900,
    )
    assert covered.hold_expires_at == hold_expires_at
    assert (
        covered.confirmation_cycle,
        covered.confirmation_claimed_cycle,
        covered.confirmation_notice_due_at,
    ) == (1, 1, None)
    assert sum(p.amount_cents for p in covered.payments if p.voided_at is None) == 1100
    assert (confirmed.status, confirmed.registration_fee_cents, confirmed.amount_due_cents) == (
        STATUS_CONFIRMED,
        1100,
        1100,
    )
    assert (cancelled.status, cancelled.registration_fee_cents, cancelled.amount_due_cents) == (
        STATUS_CANCEL_REQUESTED,
        None,
        3000,
    )
    assert len(outbox.sent) == 1
    assert outbox.sent[0].subject.startswith("La tua iscrizione")
    assert "Pagamento registrato" not in outbox.sent[0].body
    audit_count = db.scalar(select(func.count()).select_from(AuditLog))

    retry = admin_client.post(ACTIVATE, json={"preview_token": preview["preview_token"]})

    assert retry.status_code == 200
    assert retry.json()["already_applied"] is True
    assert db.scalar(select(func.count()).select_from(AuditLog)) == audit_count
    db.refresh(covered)
    assert covered.confirmation_cycle == 1


def test_changed_payment_invalidates_preview_without_partial_apply(
    admin_client, db, edition, make_participant, make_booking
):
    booking = make_booking(
        make_participant("ada@example.com"), [slot_on(db, 13)], amount_due_cents=2500
    )
    stale = admin_client.get(PREVIEW).json()["preview_token"]
    assert payment(admin_client, booking.id, 100).status_code == 201

    response = admin_client.post(ACTIVATE, json={"preview_token": stale})

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "I dati sono cambiati. Ricarica l'anteprima prima di applicare."
    )
    db.refresh(edition)
    db.refresh(booking)
    assert edition.confirmation_policy == POLICY_LEGACY_TOTAL
    assert (booking.status, booking.amount_due_cents, booking.registration_fee_cents) == (
        STATUS_PENDING,
        2500,
        None,
    )


def test_deadline_crossing_invalidates_preview_and_never_reactivates_booking(
    admin_client, db, edition, make_participant, make_booking, clock
):
    booking = make_booking(
        make_participant("ada@example.com"), [slot_on(db, 13)], amount_due_cents=1100
    )
    token = admin_client.get(PREVIEW).json()["preview_token"]
    clock.advance(days=4)

    response = admin_client.post(ACTIVATE, json={"preview_token": token})

    assert response.status_code == 409
    db.refresh(edition)
    db.refresh(booking)
    assert edition.confirmation_policy == POLICY_LEGACY_TOTAL
    assert booking.status == STATUS_PENDING
    assert booking.registration_fee_cents is None


def test_booking_without_slots_blocks_activation(
    admin_client, db, edition, make_participant, make_booking
):
    make_booking(make_participant("empty@example.com"), [], amount_due_cents=0)

    preview = admin_client.get(PREVIEW).json()

    assert preview["ready"] is False
    assert preview["preview_token"] is None
    assert preview["blockers"][0]["reason"] == "invalid_slots"
    blocked = admin_client.post(ACTIVATE, json={"preview_token": "0" * 64})
    assert blocked.status_code == 409


def test_activation_transfers_a_pending_legacy_payment_notice_into_the_new_cycle(
    admin_client, db, edition, make_participant, make_booking, outbox, clock
):
    booking = make_booking(
        make_participant("ada@example.com"),
        [slot_on(db, 13)],
        amount_due_cents=1100,
    )
    response = payment(admin_client, booking.id, 1100, defer_confirmation_email=True)
    assert response.status_code == 201
    legacy_payment = db.query(Payment).one()
    old_due_at = legacy_payment.confirmation_email_due_at
    assert old_due_at == clock() + timedelta(seconds=30)

    preview = admin_client.get(PREVIEW).json()
    activated = admin_client.post(ACTIVATE, json={"preview_token": preview["preview_token"]})

    assert activated.status_code == 200, activated.text
    assert activated.json()["transferred_notices"] == 1
    db.refresh(booking)
    db.refresh(legacy_payment)
    assert booking.confirmation_notice_due_at == old_due_at
    assert booking.confirmation_notice_payment_id == legacy_payment.id
    assert legacy_payment.confirmation_email_due_at is None
    assert outbox.sent == []

    clock.advance(seconds=31)
    assert send_due_confirmations(db, outbox, clock()) == 1
    assert len(outbox.sent) == 1
    assert outbox.sent[0].subject.startswith("Pagamento ricevuto")
    db.refresh(legacy_payment)
    assert legacy_payment.confirmation_email_sent_at == clock()
    assert send_due_confirmations(db, outbox, clock()) == 0
    assert len(outbox.sent) == 1


def test_failed_activation_notice_does_not_undo_policy_or_repeat_the_attempt(
    admin_client,
    db,
    edition,
    make_participant,
    make_booking,
    outbox,
    monkeypatch,
    caplog,
):
    edition.base_fee_cents = 500
    edition.per_day_fee_cents = 0
    edition.lunch_price_cents = 600
    booking = make_booking(
        make_participant("ada@example.com"),
        [slot_on(db, 13)],
        amount_due_cents=1100,
    )
    booking.meals = [BookingMeal(date=d(13), kind="lunch")]
    db.commit()
    assert payment(admin_client, booking.id, 500).status_code == 201
    token = admin_client.get(PREVIEW).json()["preview_token"]

    def fail(_message):
        raise RuntimeError("email service unavailable")

    monkeypatch.setattr(outbox, "send", fail)
    with caplog.at_level("ERROR", logger="app.api.admin_edition"):
        response = admin_client.post(ACTIVATE, json={"preview_token": token})

    assert response.status_code == 200, response.text
    assert "Confirmation-policy emails failed" in caplog.text
    db.refresh(edition)
    db.refresh(booking)
    assert edition.confirmation_policy == POLICY_REGISTRATION_FEE
    assert booking.confirmation_claimed_cycle == booking.confirmation_cycle == 1
    assert booking.confirmation_notice_due_at is None
    assert (
        admin_client.post(ACTIVATE, json={"preview_token": token}).json()["already_applied"] is True
    )
    assert len(outbox.sent) == 0
