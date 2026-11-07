from datetime import date

from sqlalchemy import select

from app.domain.confirmation import POLICY_REGISTRATION_FEE
from app.models import STATUS_CONFIRMED, STATUS_PENDING, Booking, Participant, Payment, Slot
from tests.helpers import d, payload


def slot_on(db, day, period="morning"):
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


def pay(client, booking_id, cents):
    return client.post(
        f"/api/admin/registrations/{booking_id}/payments",
        json={"amount_cents": cents, "channel": "iban"},
    )


def test_payment_confirms_on_registration_fee_and_void_reverses_it(
    admin_client, db, edition, make_participant, make_booking, outbox
):
    edition.confirmation_policy = POLICY_REGISTRATION_FEE
    participant = make_participant("ada@example.com")
    booking = make_booking(
        participant,
        [slot_on(db, 13), slot_on(db, 14)],
        amount_due_cents=3500,
    )
    booking.registration_fee_cents = 1200
    db.commit()

    partial = pay(admin_client, booking.id, 1199).json()["booking"]
    assert partial["status"] == STATUS_PENDING
    assert partial["balance_cents"] == 2301

    completing = pay(admin_client, booking.id, 1).json()
    assert completing["booking"]["status"] == STATUS_CONFIRMED
    assert completing["booking"]["balance_cents"] == 2300
    assert len(outbox.sent) == 1

    voided = admin_client.post(
        f"/api/admin/registrations/{booking.id}/payments/{completing['payment_id']}/void",
        json={"reason": "Pagamento registrato per errore"},
    )
    assert voided.status_code == 200, voided.text
    assert voided.json()["booking"]["status"] == STATUS_PENDING
    assert voided.json()["booking"]["paid_cents"] == 1199


def test_zero_registration_fee_creates_confirmed_booking_without_payment(
    client, db, edition, slot_ids
):
    edition.confirmation_policy = POLICY_REGISTRATION_FEE
    edition.base_fee_cents = 0
    edition.per_day_fee_cents = 0
    db.commit()
    day_slot_id = slot_ids[(date(2026, 7, 13), "morning")]

    response = client.post("/api/public/registrations", json=payload([day_slot_id]))

    assert response.status_code == 201, response.text
    participant = db.scalar(select(Participant).where(Participant.email == "ada@example.com"))
    booking_id = db.scalar(select(Booking.id).where(Booking.participant_id == participant.id))
    db.expire_all()
    booking = db.get(Booking, booking_id)
    assert (booking.status, booking.registration_fee_cents, booking.amount_due_cents) == (
        STATUS_CONFIRMED,
        0,
        0,
    )
    assert db.scalar(select(Payment).where(Payment.booking_id == booking_id)) is None
