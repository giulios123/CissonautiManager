from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    STATUS_REFUNDED,
    AuditLog,
    Booking,
    Participant,
    Slot,
)
from app.services import audit as audit_service
from tests.helpers import d
from tests.test_auth import login
from tests.test_change_slots import available_seats, pay

MORNING = "morning"


@pytest.fixture
def booking(db, edition, make_participant, make_booking, slot_ids, admin_client):
    ada = make_participant("ada@example.com", first_name="Ada", last_name="Lovelace")
    return make_booking(ada, [db.get(Slot, slot_ids[(d(13), MORNING)])])


def put(client, booking, ids, **extra):
    return client.put(
        f"/api/admin/registrations/{booking.id}/slots", json={"slot_ids": ids, **extra}
    )


class TestSlots:
    def test_adds_a_slot_and_recomputes_the_amount_keeping_the_deadline(
        self, admin_client, booking, slot_ids, db
    ):
        deadline = booking.hold_expires_at
        response = put(
            admin_client, booking, [slot_ids[(d(13), MORNING)], slot_ids[(d(14), MORNING)]]
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["booking"]["amount_due_cents"] == 1200
        assert len(data["booking"]["slots"]) == 2
        db.expire_all()
        assert db.get(Booking, booking.id).hold_expires_at == deadline

    def test_the_history_says_what_was_added_removed_and_the_new_amount(
        self, admin_client, booking, slot_ids
    ):
        data = put(admin_client, booking, [slot_ids[(d(14), MORNING)]]).json()
        entry = data["history"][0]
        assert entry["action"] == "slots_changed"
        assert "Aggiunti: mar 14/07 mattina" in entry["detail"]
        assert "Tolti: lun 13/07 mattina" in entry["detail"]
        assert "11,00 € → 11,00 €" in entry["detail"]

    def test_a_confirmed_booking_stays_confirmed(self, admin_client, booking, db, slot_ids):
        booking.status = STATUS_CONFIRMED
        db.commit()
        pay(db, booking, 1100)
        data = put(
            admin_client, booking, [slot_ids[(d(13), MORNING)], slot_ids[(d(14), MORNING)]]
        ).json()
        assert data["booking"]["status"] == STATUS_CONFIRMED
        assert data["booking"]["balance_cents"] == 100

    @pytest.mark.parametrize("status", [STATUS_EXPIRED, STATUS_CANCEL_REQUESTED, STATUS_REFUNDED])
    def test_a_closed_booking_cannot_be_edited(self, admin_client, booking, db, slot_ids, status):
        booking.status = status
        db.commit()
        assert put(admin_client, booking, [slot_ids[(d(14), MORNING)]]).status_code == 409

    def test_days_already_over_can_be_changed_without_forcing(
        self, admin_client, booking, db, slot_ids, clock
    ):
        clock.advance(days=13)  # 14 July: the 13th is over
        booking.hold_expires_at = clock() + timedelta(days=3)  # keep it pending for the test
        db.commit()
        response = put(admin_client, booking, [slot_ids[(d(15), MORNING)]])
        assert response.status_code == 200, response.text

    def test_a_full_slot_is_refused_with_a_hint_about_forcing(
        self, admin_client, booking, db, slot_ids, make_participant, make_booking
    ):
        full = db.get(Slot, slot_ids[(d(14), MORNING)])
        full.capacity = 1
        db.commit()
        make_booking(make_participant("bob@example.com"), [full])
        response = put(admin_client, booking, [slot_ids[(d(13), MORNING)], full.id])
        assert response.status_code == 409
        assert "14/07" in response.json()["detail"] and "Forza" in response.json()["detail"]
        db.expire_all()
        assert len(db.get(Booking, booking.id).slots) == 1

    def test_forcing_goes_over_capacity_and_says_so(
        self, admin_client, booking, db, slot_ids, make_participant, make_booking
    ):
        full = db.get(Slot, slot_ids[(d(14), MORNING)])
        full.capacity = 1
        db.commit()
        make_booking(make_participant("bob@example.com"), [full])
        response = put(admin_client, booking, [slot_ids[(d(13), MORNING)], full.id], force=True)
        assert response.status_code == 200, response.text
        data = response.json()
        assert "capienza superata" in data["warning"] and "14/07" in data["warning"]
        assert "Oltre la capienza" in data["history"][0]["detail"]
        slot = next(
            s
            for day in admin_client.get("/api/admin/views/slots").json()["days"]
            for s in day["slots"]
            if s["id"] == full.id
        )
        assert (slot["present"], slot["capacity"], slot["free"]) == (2, 1, 0)

    def test_an_empty_or_unknown_selection_is_refused(self, admin_client, booking):
        assert put(admin_client, booking, []).status_code == 422
        assert put(admin_client, booking, [999999]).status_code == 422

    def test_a_pending_booking_the_new_amount_covers_is_confirmed(
        self, admin_client, booking, db, slot_ids, outbox
    ):
        booking.amount_due_cents = 1200
        db.commit()
        pay(db, booking, 1100)
        data = put(admin_client, booking, [slot_ids[(d(13), MORNING)]]).json()
        assert data["booking"]["status"] == STATUS_CONFIRMED
        assert len(outbox.sent) == 1

    def test_unknown_booking_is_404(self, admin_client):
        assert (
            admin_client.put(
                "/api/admin/registrations/999/slots", json={"slot_ids": [1]}
            ).status_code
            == 404
        )

    def test_admins_only(self, client, outbox, make_participant, booking, slot_ids):
        assert put(client, booking, [slot_ids[(d(13), MORNING)]]).status_code == 401
        make_participant("someone@example.com")
        login(client, outbox, email="someone@example.com")
        assert put(client, booking, [slot_ids[(d(13), MORNING)]]).status_code == 403


class TestCancellation:
    def cancel(self, client, booking):
        return client.post(f"/api/admin/registrations/{booking.id}/cancel")

    def test_with_payments_it_becomes_a_requested_cancellation_and_the_person_is_told(
        self, admin_client, booking, db, outbox, client, slot_ids
    ):
        pay(db, booking, 500)
        data = self.cancel(admin_client, booking).json()
        assert data["outcome"] == "requested"
        assert data["detail"]["booking"]["status"] == STATUS_CANCEL_REQUESTED
        assert data["detail"]["history"][0]["action"] == "cancelled_by_admin"
        assert [m.to for m in outbox.sent] == ["ada@example.com"]
        assert available_seats(client)[slot_ids[(d(13), MORNING)]] == 25

    def test_without_payments_the_booking_is_removed_but_the_trace_stays(
        self, admin_client, booking, db, outbox
    ):
        booking_id = booking.id
        data = self.cancel(admin_client, booking).json()
        assert data == {"outcome": "removed", "detail": None}
        db.expire_all()
        assert db.scalar(select(func.count()).select_from(Booking)) == 0
        assert db.scalar(select(Participant).where(Participant.email == "ada@example.com"))
        entry = db.scalar(select(AuditLog))
        assert entry.booking_id is None  # detached, so a later booking cannot inherit it
        assert "Ada Lovelace" in entry.detail and "ada@example.com" in entry.detail
        assert audit_service.history(db, booking_id) == []
        assert "rimossa" in entry.detail
        assert len(outbox.sent) == 1

    def test_earlier_history_of_a_removed_booking_is_detached_too_and_not_inherited(
        self, admin_client, booking, db, slot_ids, make_participant
    ):
        old_id = booking.id
        kept = {
            "edition_id": booking.edition_id,
            "hold_expires_at": booking.hold_expires_at,
            "hold_started_at": booking.hold_started_at,
            "privacy_document_id": booking.privacy_document_id,
            "privacy_accepted_at": booking.privacy_accepted_at,
            "disclaimer_document_id": booking.disclaimer_document_id,
            "disclaimer_accepted_at": booking.disclaimer_accepted_at,
        }
        admin_client.patch(f"/api/admin/registrations/{old_id}", json={"first_name": "Adele"})
        assert db.scalar(select(AuditLog)).booking_id == old_id
        assert self.cancel(admin_client, booking).json()["outcome"] == "removed"
        db.expire_all()
        entries = db.scalars(select(AuditLog)).all()
        assert len(entries) == 2 and all(e.booking_id is None for e in entries)
        # a new booking (on SQLite it takes the freed id) starts with an empty history
        bob = make_participant("bob@example.com")
        newer = Booking(participant_id=bob.id, status=STATUS_PENDING, amount_due_cents=1100, **kept)
        newer.slots = [db.get(Slot, slot_ids[(d(14), MORNING)])]
        db.add(newer)
        db.commit()
        detail = admin_client.get(f"/api/admin/registrations/{newer.id}").json()
        assert detail["history"] == []

    @pytest.mark.parametrize("status", [STATUS_EXPIRED, STATUS_CANCEL_REQUESTED, STATUS_REFUNDED])
    def test_a_closed_booking_cannot_be_cancelled(self, admin_client, booking, db, outbox, status):
        booking.status = status
        db.commit()
        assert self.cancel(admin_client, booking).status_code == 409
        assert outbox.sent == []

    def test_a_confirmed_booking_can_be_cancelled(self, admin_client, booking, db):
        booking.status = STATUS_CONFIRMED
        db.commit()
        pay(db, booking, 1100)
        assert self.cancel(admin_client, booking).json()["outcome"] == "requested"

    def test_unknown_booking_is_404(self, admin_client):
        assert admin_client.post("/api/admin/registrations/999/cancel").status_code == 404

    def test_admins_only(self, client, outbox, make_participant, booking):
        assert self.cancel(client, booking).status_code == 401
        make_participant("someone@example.com")
        login(client, outbox, email="someone@example.com")
        assert self.cancel(client, booking).status_code == 403
