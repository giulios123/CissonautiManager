from datetime import date, timedelta

import pytest
from sqlalchemy import func, select

from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    AuditLog,
    Booking,
    Payment,
    Slot,
)
from tests.test_auth import login


def slot_on(db, day, period="morning"):
    return db.scalar(select(Slot).where(Slot.date == date(2026, 7, day), Slot.period == period))


def pay(client, booking_id, cents, channel="iban", **extra):
    body = {"amount_cents": cents, "channel": channel, **extra}
    return client.post(f"/api/admin/registrations/{booking_id}/payments", json=body)


@pytest.fixture
def ada_booking(db, edition, make_participant, make_booking):
    ada = make_participant(
        "ada@example.com", first_name="Ada", last_name="Lovelace", personal_code="CSC-ADA1"
    )
    return make_booking(ada, [slot_on(db, 13), slot_on(db, 14)], amount_due_cents=1200)


class TestAccess:
    def test_anonymous_and_participants_are_rejected(self, client, outbox, make_participant):
        assert client.get("/api/admin/registrations").status_code == 401
        make_participant("ada@example.com")
        login(client, outbox)
        assert client.get("/api/admin/registrations").status_code == 403
        assert client.post("/api/admin/registrations/1/payments", json={}).status_code == 403

    def test_cancellation_history_static_route_is_not_captured_as_booking_id(self, admin_client):
        response = admin_client.get("/api/admin/registrations/cancellations")
        assert response.status_code == 200
        assert response.json() == {"items": [], "has_more": False}


class TestList:
    def test_empty_without_edition(self, admin_client):
        assert admin_client.get("/api/admin/registrations").json() == []

    def test_row_shows_amounts_days_and_status(self, admin_client, ada_booking):
        rows = admin_client.get("/api/admin/registrations").json()
        assert len(rows) == 1
        row = rows[0]
        assert (row["first_name"], row["last_name"], row["email"]) == (
            "Ada",
            "Lovelace",
            "ada@example.com",
        )
        assert row["days"] == 2
        assert row["status"] == STATUS_PENDING
        assert (row["amount_due_cents"], row["paid_cents"], row["balance_cents"]) == (1200, 0, 1200)

    def test_overdue_bookings_are_listed_as_expired(self, admin_client, ada_booking, clock):
        clock.advance(days=3)
        assert admin_client.get("/api/admin/registrations").json()[0]["status"] == STATUS_EXPIRED

    def test_filter_by_status(self, admin_client, db, make_participant, make_booking, ada_booking):
        grace = make_participant("grace@example.com", first_name="Grace", last_name="Hopper")
        make_booking(grace, [slot_on(db, 15)], status=STATUS_CONFIRMED)
        confirmed = admin_client.get("/api/admin/registrations?status=confermata").json()
        assert [r["email"] for r in confirmed] == ["grace@example.com"]
        pending = admin_client.get("/api/admin/registrations?status=in_attesa_pagamento").json()
        assert [r["email"] for r in pending] == ["ada@example.com"]

    def test_filter_by_expired_uses_deadline(self, admin_client, ada_booking, clock):
        clock.advance(days=4)
        expired = admin_client.get("/api/admin/registrations?status=scaduta").json()
        assert len(expired) == 1

    def test_invalid_status_filter_is_rejected(self, admin_client):
        assert admin_client.get("/api/admin/registrations?status=boh").status_code == 422

    @pytest.mark.parametrize("needle", ["ada", "LOVEL", "example.com", "csc-ada1"])
    def test_search_matches_name_email_and_code(self, admin_client, ada_booking, needle):
        assert len(admin_client.get("/api/admin/registrations", params={"q": needle}).json()) == 1

    def test_search_without_match(self, admin_client, ada_booking):
        assert admin_client.get("/api/admin/registrations", params={"q": "zzz"}).json() == []

    def test_search_treats_wildcards_literally(self, admin_client, ada_booking):
        assert admin_client.get("/api/admin/registrations", params={"q": "%"}).json() == []


class TestDetail:
    def test_detail_has_participant_data_and_legal_acceptance(self, admin_client, ada_booking, db):
        data = admin_client.get(f"/api/admin/registrations/{ada_booking.id}").json()
        assert data["participant"]["email"] == "ada@example.com"
        assert data["participant"]["personal_code"] == "CSC-ADA1"
        assert data["privacy"]["version"] == 1
        assert data["disclaimer"]["accepted_at"].startswith("2026-07-01T10:00:00")
        assert len(data["booking"]["slots"]) == 2

    def test_unknown_booking_is_404(self, admin_client):
        assert admin_client.get("/api/admin/registrations/999").status_code == 404


class TestRecordPayment:
    def test_partial_payment_keeps_booking_pending(self, admin_client, ada_booking, outbox):
        data = pay(admin_client, ada_booking.id, 500).json()
        assert data["booking"]["status"] == STATUS_PENDING
        assert (data["booking"]["paid_cents"], data["booking"]["balance_cents"]) == (500, 700)
        assert outbox.sent == []

    def test_payment_covering_the_amount_confirms_and_emails_once(
        self, admin_client, ada_booking, outbox
    ):
        pay(admin_client, ada_booking.id, 500)
        data = pay(admin_client, ada_booking.id, 700).json()
        assert data["booking"]["status"] == STATUS_CONFIRMED
        assert data["booking"]["balance_cents"] == 0
        assert len(outbox.sent) == 1
        assert outbox.sent[0].to == "ada@example.com"
        assert "confermata" in outbox.sent[0].body
        pay(admin_client, ada_booking.id, 100)
        assert len(outbox.sent) == 1

    def test_single_payment_for_the_full_amount_confirms(self, admin_client, ada_booking):
        data = pay(admin_client, ada_booking.id, 1200).json()
        assert data["booking"]["status"] == STATUS_CONFIRMED

    def test_overpayment_confirms_and_shows_negative_balance(self, admin_client, ada_booking):
        data = pay(admin_client, ada_booking.id, 1500).json()
        assert data["booking"]["status"] == STATUS_CONFIRMED
        assert data["booking"]["balance_cents"] == -300

    def test_payment_details_are_stored(self, admin_client, ada_booking, db):
        pay(admin_client, ada_booking.id, 500, "satispay", paid_on="2026-07-02", note="via Anna")
        payment = db.scalar(select(Payment))
        assert (payment.channel, payment.paid_on, payment.note) == (
            "satispay",
            date(2026, 7, 2),
            "via Anna",
        )
        assert payment.recorded_by_id is not None

    def test_quick_payment_request_is_idempotent_and_reuses_undo_deadline(
        self, admin_client, ada_booking, db
    ):
        body = {
            "amount_cents": 500,
            "channel": "iban",
            "paid_on": "2026-07-02",
            "note": "bonifico",
            "defer_confirmation_email": True,
            "request_key": "2c48f9b8-15d7-4660-b80a-983e1e81e4a2",
            "expected_snapshot": {
                "status": STATUS_PENDING,
                "confirmation_policy": "legacy_total",
                "amount_due_cents": 1200,
                "paid_cents": 0,
                "registration_fee_cents": None,
                "confirmation_due_cents": 1200,
            },
        }
        first = admin_client.post(f"/api/admin/registrations/{ada_booking.id}/payments", json=body)
        second = admin_client.post(f"/api/admin/registrations/{ada_booking.id}/payments", json=body)
        assert first.status_code == second.status_code == 201
        assert first.json()["payment_id"] == second.json()["payment_id"]
        assert first.json()["payment_replayed"] is False
        assert second.json()["payment_replayed"] is True
        assert first.json()["payment_undo_until"] == second.json()["payment_undo_until"]
        assert db.scalar(select(func.count()).select_from(Payment)) == 1

    def test_quick_payment_rejects_stale_balance(self, admin_client, ada_booking, db):
        snapshot = {
            "status": STATUS_PENDING,
            "confirmation_policy": "legacy_total",
            "amount_due_cents": 1200,
            "paid_cents": 0,
            "registration_fee_cents": None,
            "confirmation_due_cents": 1200,
        }
        pay(admin_client, ada_booking.id, 100)
        response = admin_client.post(
            f"/api/admin/registrations/{ada_booking.id}/payments",
            json={
                "amount_cents": 500,
                "channel": "iban",
                "request_key": "2c48f9b8-15d7-4660-b80a-983e1e81e4a2",
                "expected_snapshot": snapshot,
            },
        )
        assert response.status_code == 409
        assert db.scalar(select(func.count()).select_from(Payment)) == 1

    def test_reusing_payment_key_with_different_payload_is_a_distinct_conflict(
        self, admin_client, ada_booking
    ):
        key = "2c48f9b8-15d7-4660-b80a-983e1e81e4a2"
        first = pay(admin_client, ada_booking.id, 100, request_key=key)
        assert first.status_code == 201
        conflict = pay(admin_client, ada_booking.id, 200, request_key=key)
        assert conflict.status_code == 409
        assert conflict.json()["detail"]["code"] == "payment_request_conflict"

    def test_replay_of_voided_payment_does_not_offer_an_undo_window(
        self, admin_client, ada_booking
    ):
        body = {
            "amount_cents": 100,
            "channel": "iban",
            "request_key": "2c48f9b8-15d7-4660-b80a-983e1e81e4a2",
        }
        first = admin_client.post(f"/api/admin/registrations/{ada_booking.id}/payments", json=body)
        payment_id = first.json()["payment_id"]
        undone = admin_client.post(
            f"/api/admin/registrations/{ada_booking.id}/payments/{payment_id}/void",
            json={"reason": "entered by mistake"},
        )
        assert undone.status_code == 200

        replay = admin_client.post(f"/api/admin/registrations/{ada_booking.id}/payments", json=body)
        assert replay.status_code == 201
        assert replay.json()["payment_replayed"] is True
        assert replay.json()["payment_undo_until"] is None


class TestCancellationHistory:
    def test_participant_cancellation_is_visible_with_a_structured_outcome(
        self, admin_client, ada_booking, db, client, outbox
    ):
        from tests.test_auth import login

        login(client, outbox)
        response = client.post("/api/me/booking/cancel")
        assert response.status_code == 200

        history = admin_client.get("/api/admin/registrations/cancellations")
        assert history.status_code == 200
        assert history.json()["items"][0]["outcome"] == "removed"

    def test_cursor_pages_do_not_repeat_rows(self, admin_client, ada_booking, db, clock):
        db.add_all(
            [
                AuditLog(
                    at=clock(),
                    actor_id=None,
                    booking_id=None,
                    participant_id=ada_booking.participant_id,
                    edition_id=ada_booking.edition_id,
                    action="cancelled_by_participant",
                    outcome="removed",
                    detail=f"Cancellation {index}",
                )
                for index in range(4)
            ]
        )
        db.commit()

        first = admin_client.get(
            "/api/admin/registrations/cancellations", params={"limit": 2}
        ).json()
        cursor = first["items"][-1]
        second = admin_client.get(
            "/api/admin/registrations/cancellations",
            params={"limit": 2, "before_at": cursor["at"], "before_id": cursor["id"]},
        ).json()
        assert set(row["id"] for row in first["items"]).isdisjoint(
            row["id"] for row in second["items"]
        )
        assert first["has_more"] is True

    def test_date_defaults_to_today_in_rome(self, admin_client, ada_booking, db, clock):
        clock.advance(hours=14)  # 2026-07-01 10:00 UTC + 14h = 00:00 on July 2nd in Rome
        pay(admin_client, ada_booking.id, 500)
        assert db.scalar(select(Payment.paid_on)) == date(2026, 7, 2)

    def test_notes_are_visible_to_admins(self, admin_client, ada_booking):
        data = pay(admin_client, ada_booking.id, 500, note="in contanti").json()
        assert data["booking"]["payments"][0]["note"] == "in contanti"

    @pytest.mark.parametrize(
        "body",
        [
            {"amount_cents": 0, "channel": "iban"},
            {"amount_cents": -5, "channel": "iban"},
            {"amount_cents": 100, "channel": "bitcoin"},
            {"amount_cents": 100},
        ],
    )
    def test_invalid_payment_is_rejected(self, admin_client, ada_booking, db, body):
        response = admin_client.post(
            f"/api/admin/registrations/{ada_booking.id}/payments", json=body
        )
        assert response.status_code == 422
        assert db.scalar(select(func.count()).select_from(Payment)) == 0

    def test_unknown_booking_is_404(self, admin_client):
        assert pay(admin_client, 999, 100).status_code == 404

    def test_payment_does_not_change_cancelled_bookings(
        self, admin_client, db, make_participant, make_booking, edition
    ):
        booking = make_booking(
            make_participant("x@example.com"),
            [slot_on(db, 13)],
            status=STATUS_CANCEL_REQUESTED,
            amount_due_cents=1100,
        )
        data = pay(admin_client, booking.id, 1100).json()
        assert data["booking"]["status"] == STATUS_CANCEL_REQUESTED


class TestPaymentOnExpiredBooking:
    def test_revives_when_there_is_room_and_holds_again(
        self, admin_client, ada_booking, clock, outbox, db
    ):
        clock.advance(days=5)
        data = pay(admin_client, ada_booking.id, 500).json()
        assert data["booking"]["status"] == STATUS_PENDING
        assert data["warning"] is None
        db.expire_all()
        assert db.get(Booking, ada_booking.id).hold_expires_at == clock() + timedelta(days=3)

    def test_revival_starts_a_new_hold_and_resets_the_reminders(
        self, admin_client, ada_booking, clock, db
    ):
        ada_booking.reminder_mid_sent_at = clock() + timedelta(hours=36)
        ada_booking.reminder_final_sent_at = clock() + timedelta(hours=48)
        db.commit()
        original_start = ada_booking.hold_started_at
        clock.advance(days=5)
        pay(admin_client, ada_booking.id, 500)
        db.expire_all()
        booking = db.get(Booking, ada_booking.id)
        assert booking.hold_started_at == clock() != original_start
        assert booking.reminder_mid_sent_at is None
        assert booking.reminder_final_sent_at is None

    def test_revives_and_confirms_when_payment_covers(
        self, admin_client, ada_booking, clock, outbox
    ):
        clock.advance(days=5)
        data = pay(admin_client, ada_booking.id, 1200).json()
        assert data["booking"]["status"] == STATUS_CONFIRMED
        assert len(outbox.sent) == 1

    def test_stays_expired_with_warning_when_a_slot_is_full(
        self, admin_client, db, ada_booking, clock, make_participant, make_booking, outbox
    ):
        clock.advance(days=5)
        slot = slot_on(db, 13)
        slot.capacity = 1
        db.commit()
        make_booking(make_participant("late@example.com"), [slot])
        response = pay(admin_client, ada_booking.id, 1200)
        data = response.json()
        assert response.status_code == 201
        assert data["booking"]["status"] == STATUS_EXPIRED
        assert data["booking"]["paid_cents"] == 1200
        assert "slot" in data["warning"]
        assert outbox.sent == []

    def test_warning_persists_when_reading_the_booking_again(
        self, admin_client, db, ada_booking, clock, make_participant, make_booking
    ):
        clock.advance(days=5)
        slot = slot_on(db, 14)
        slot.capacity = 1
        db.commit()
        make_booking(make_participant("late@example.com"), [slot])
        pay(admin_client, ada_booking.id, 500)
        data = admin_client.get(f"/api/admin/registrations/{ada_booking.id}").json()
        assert data["warning"]

    def test_seats_taken_by_the_revived_booking_count_again(
        self, admin_client, db, ada_booking, clock, client
    ):
        clock.advance(days=5)
        pay(admin_client, ada_booking.id, 500)
        slot = db.get(Slot, slot_on(db, 13).id)
        data = client.get("/api/public/edition").json()
        first_day = next(d for d in data["days"] if d["date"] == "2026-07-13")
        morning = next(s for s in first_day["slots"] if s["id"] == slot.id)
        assert morning["available"] == 24
