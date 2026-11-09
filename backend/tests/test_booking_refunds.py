from uuid import uuid4

from sqlalchemy import func, select

from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_PENDING,
    STATUS_REFUNDED,
    AuditLog,
    BookingRefund,
    Payment,
)
from tests.test_auth import login
from tests.test_change_slots import pay
from tests.test_exemptions import REG, make


def refund(client, booking, amount, channel="revolut", **extra):
    return client.post(
        f"{REG}/{booking.id}/refunds",
        json={"amount_cents": amount, "channel": channel, **extra},
    )


def credit_booking(db, edition, make_participant, make_booking, paid=5000):
    """A confirmed booking owing 46 € that paid `paid`: credit of paid - 46 €."""
    booking, _ = make(db, edition, make_participant, make_booking, status=STATUS_CONFIRMED)
    pay(db, booking, paid)
    return booking


class TestRecord:
    def test_a_refund_up_to_the_credit_is_recorded_and_changes_no_status(
        self, admin_client, db, edition, make_participant, make_booking, outbox
    ):
        booking = credit_booking(db, edition, make_participant, make_booking)  # credit 4,00 €
        outbox.sent.clear()
        response = refund(admin_client, booking, 400, note="contanti", refunded_on="2026-07-13")
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["booking"]["status"] == STATUS_CONFIRMED
        assert (body["booking"]["paid_cents"], body["booking"]["balance_cents"]) == (4600, 0)
        assert body["booking"]["refunds"][0]["note"] == "contanti"
        # Nothing was cancelled, nothing was sent.
        assert db.scalar(select(func.count()).select_from(Payment)) == 1
        assert outbox.sent == []
        log = db.scalar(select(AuditLog).where(AuditLog.action == "booking_refund"))
        assert "4,00" in log.detail

    def test_a_refund_beyond_the_credit_is_refused(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking = credit_booking(db, edition, make_participant, make_booking)
        refused = refund(admin_client, booking, 401)
        assert refused.status_code == 422
        assert "credito" in refused.json()["detail"]
        assert db.scalar(select(func.count()).select_from(BookingRefund)) == 0

    def test_no_credit_no_refund(self, admin_client, db, edition, make_participant, make_booking):
        booking = credit_booking(db, edition, make_participant, make_booking, paid=4600)
        assert refund(admin_client, booking, 1).status_code == 422

    def test_the_same_request_is_recorded_once(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking = credit_booking(db, edition, make_participant, make_booking)
        key = str(uuid4())
        first = refund(admin_client, booking, 200, request_key=key)
        second = refund(admin_client, booking, 200, request_key=key)
        assert first.status_code == second.status_code == 201
        assert db.scalar(select(func.count()).select_from(BookingRefund)) == 1
        conflict = refund(admin_client, booking, 300, request_key=key)
        assert conflict.status_code == 409
        assert conflict.json()["detail"]["code"] == "payment_request_conflict"

    def test_two_refunds_together_cannot_exceed_the_credit(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking = credit_booking(db, edition, make_participant, make_booking)
        assert refund(admin_client, booking, 300).status_code == 201
        assert refund(admin_client, booking, 200).status_code == 422
        assert refund(admin_client, booking, 100).status_code == 201

    def test_an_exemption_creates_credit_that_can_be_refunded(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, hike = make(db, edition, make_participant, make_booking, status=STATUS_CONFIRMED)
        pay(db, booking, 4600)  # paid in full
        preview = admin_client.post(
            f"{REG}/{booking.id}/exemptions/preview",
            json={
                "category": "internal_non_paying",
                "fee_exempt": True,
                "meals": [],
                "activity_ids": [hike.id],
            },
        ).json()
        admin_client.post(
            f"{REG}/{booking.id}/exemptions/apply",
            json={
                "category": "internal_non_paying",
                "fee_exempt": True,
                "meals": [],
                "activity_ids": [hike.id],
                "preview_token": preview["preview_token"],
            },
        )
        db.refresh(booking)
        assert booking.amount_due_cents == 2000  # lunch and dinner
        assert refund(admin_client, booking, 2600).status_code == 201  # 46 - 20
        assert refund(admin_client, booking, 1).status_code == 422

    def test_a_closed_booking_has_no_active_refund(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking = credit_booking(db, edition, make_participant, make_booking)
        booking.status = STATUS_CANCEL_REQUESTED
        db.commit()
        assert refund(admin_client, booking, 100).status_code == 409

    def test_a_bad_channel_or_amount_is_refused(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking = credit_booking(db, edition, make_participant, make_booking)
        assert refund(admin_client, booking, 100, channel="cash").status_code == 422
        assert refund(admin_client, booking, 0).status_code == 422

    def test_unknown_booking(self, admin_client, edition):
        assert (
            admin_client.post(
                f"{REG}/999/refunds", json={"amount_cents": 1, "channel": "revolut"}
            ).status_code
            == 404
        )


class TestVoid:
    def test_a_voided_refund_stays_on_record_and_stops_counting(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking = credit_booking(db, edition, make_participant, make_booking)
        refund(admin_client, booking, 400)
        refund_id = db.scalar(select(BookingRefund.id))
        response = admin_client.post(
            f"{REG}/{booking.id}/refunds/{refund_id}/void", json={"reason": "Errore"}
        )
        assert response.status_code == 200
        body = response.json()["booking"]
        assert (body["paid_cents"], body["balance_cents"]) == (5000, -400)
        assert body["refunds"][0]["voided"] is True
        assert body["refunds"][0]["void_reason"] == "Errore"
        assert db.scalar(select(func.count()).select_from(BookingRefund)) == 1

    def test_a_reason_is_required_and_twice_is_a_conflict(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking = credit_booking(db, edition, make_participant, make_booking)
        refund(admin_client, booking, 400)
        refund_id = db.scalar(select(BookingRefund.id))
        url = f"{REG}/{booking.id}/refunds/{refund_id}/void"
        assert admin_client.post(url, json={}).status_code == 422
        assert admin_client.post(url, json={"reason": "x"}).status_code == 200
        assert admin_client.post(url, json={"reason": "x"}).status_code == 409
        assert (
            admin_client.post(
                f"{REG}/{booking.id}/refunds/999/void", json={"reason": "x"}
            ).status_code
            == 404
        )


class TestNetPaid:
    def test_a_payment_under_a_refund_cannot_be_voided(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking = credit_booking(db, edition, make_participant, make_booking)
        refund(admin_client, booking, 400)
        payment_id = db.scalar(select(Payment.id))
        blocked = admin_client.post(
            f"{REG}/{booking.id}/payments/{payment_id}/void", json={"reason": "x"}
        )
        assert blocked.status_code == 409
        assert "rimborso" in blocked.json()["detail"]
        db.refresh(booking)
        assert booking.payments[0].voided_at is None

    def test_after_voiding_the_refund_the_payment_can_be_voided_and_the_place_falls_back(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking = credit_booking(db, edition, make_participant, make_booking)
        refund(admin_client, booking, 400)
        refund_id = db.scalar(select(BookingRefund.id))
        payment_id = db.scalar(select(Payment.id))
        admin_client.post(f"{REG}/{booking.id}/refunds/{refund_id}/void", json={"reason": "x"})
        voided = admin_client.post(
            f"{REG}/{booking.id}/payments/{payment_id}/void", json={"reason": "x"}
        )
        assert voided.status_code == 200
        assert voided.json()["booking"]["status"] == STATUS_PENDING

    def test_voiding_another_payment_is_fine_while_enough_remains(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, _ = make(db, edition, make_participant, make_booking, status=STATUS_CONFIRMED)
        pay(db, booking, 4600)
        pay(db, booking, 1000)  # credit 10 €
        refund(admin_client, booking, 400)
        second = db.scalars(select(Payment.id).order_by(Payment.id.desc())).first()
        ok = admin_client.post(f"{REG}/{booking.id}/payments/{second}/void", json={"reason": "x"})
        assert ok.status_code == 200  # 46 paid remains, refunds 4 <= 46

    def test_the_balance_in_every_view_uses_the_net(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, _ = make(db, edition, make_participant, make_booking, status=STATUS_CONFIRMED)
        pay(db, booking, 4600)
        pay(db, booking, 400)
        assert admin_client.get("/api/admin/views/payments-review").json() is not None
        refund(admin_client, booking, 400)
        detail = admin_client.get(f"{REG}/{booking.id}").json()["booking"]
        assert (detail["paid_cents"], detail["balance_cents"]) == (4600, 0)
        # A booking with no balance is not in "to collect".
        assert admin_client.get("/api/admin/views/to-collect").json() == []

    def test_a_refund_on_cancellation_is_capped_by_the_net_paid(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking = credit_booking(db, edition, make_participant, make_booking)  # paid 50, due 46
        refund(admin_client, booking, 400)  # net paid now 46
        booking.status = STATUS_CANCEL_REQUESTED
        db.commit()
        too_much = admin_client.post(f"{REG}/{booking.id}/refund", json={"amount_cents": 4601})
        assert too_much.status_code == 422
        ok = admin_client.post(f"{REG}/{booking.id}/refund", json={"amount_cents": 4600})
        assert ok.status_code == 200
        db.refresh(booking)
        assert booking.status == STATUS_REFUNDED

    def test_the_participant_sees_the_refund_in_their_list_and_the_same_balance(
        self, admin_client, db, edition, make_participant, make_booking, client, outbox
    ):
        booking = credit_booking(db, edition, make_participant, make_booking)
        refund(admin_client, booking, 400, note="privata")
        login(client, outbox)
        mine = client.get("/api/me").json()["bookings"][0]
        assert (mine["paid_cents"], mine["balance_cents"]) == (4600, 0)
        assert [(r["amount_cents"], r["note"]) for r in mine["refunds"]] == [(400, None)]

    def test_no_refund_means_nothing_changes_for_old_bookings(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, _ = make(db, edition, make_participant, make_booking, status=STATUS_CONFIRMED)
        pay(db, booking, 1000)
        detail = admin_client.get(f"{REG}/{booking.id}").json()["booking"]
        assert (detail["paid_cents"], detail["refunds"]) == (1000, [])
