from datetime import timedelta

import pytest
from sqlalchemy import select

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
from tests.helpers import d
from tests.test_auth import login
from tests.test_change_slots import available_seats, pay


@pytest.fixture
def booking(db, edition, make_participant, make_booking, slot_ids, admin_client):
    ada = make_participant(
        "ada@example.com",
        first_name="Ada",
        last_name="Lovelace",
        phone="+39 333 111",
        invited_by="Grace",
    )
    ada.can_bring = "Un talk"
    db.commit()
    return make_booking(ada, [db.get(Slot, slot_ids[(d(13), "morning")])])


def patch(client, booking, **body):
    return client.patch(f"/api/admin/registrations/{booking.id}", json=body)


class TestDetails:
    def test_changes_are_saved_and_shown(self, admin_client, booking, db):
        response = patch(
            admin_client, booking, first_name="Adele", last_name="Byron", phone="+39 333 222",
            invited_by="Charles", can_bring="Una demo",
        )  # fmt: skip
        assert response.status_code == 200, response.text
        person = response.json()["participant"]
        assert (person["first_name"], person["last_name"], person["phone"]) == (
            "Adele",
            "Byron",
            "+39 333 222",
        )
        assert (person["invited_by"], person["can_bring"]) == ("Charles", "Una demo")
        db.expire_all()
        assert db.get(Participant, booking.participant_id).first_name == "Adele"

    def test_fields_left_out_stay_as_they_are(self, admin_client, booking):
        person = patch(admin_client, booking, phone="+39 000").json()["participant"]
        assert (person["first_name"], person["invited_by"], person["can_bring"]) == (
            "Ada",
            "Grace",
            "Un talk",
        )

    @pytest.mark.parametrize("empty", [None, "", "   "])
    def test_phone_and_invited_by_can_be_cleared(self, admin_client, booking, empty):
        person = patch(admin_client, booking, phone=empty, invited_by=empty).json()["participant"]
        assert person["phone"] is None and person["invited_by"] is None

    @pytest.mark.parametrize("field", ["first_name", "last_name", "can_bring"])
    @pytest.mark.parametrize("empty", [None, "", "  "])
    def test_required_fields_cannot_be_emptied(self, admin_client, booking, field, empty):
        assert patch(admin_client, booking, **{field: empty}).status_code == 422

    def test_the_email_is_normalised_and_must_be_valid(self, admin_client, booking, db):
        assert patch(admin_client, booking, email="not-an-email").status_code == 422
        assert patch(admin_client, booking, email="  ADA.New@Example.com ").status_code == 200
        db.expire_all()
        assert db.get(Participant, booking.participant_id).email == "ada.new@example.com"

    def test_an_email_used_by_someone_else_is_refused(
        self, admin_client, booking, make_participant, db
    ):
        make_participant("bob@example.com")
        response = patch(admin_client, booking, email="Bob@example.com", first_name="Changed")
        assert response.status_code == 409
        db.expire_all()
        person = db.get(Participant, booking.participant_id)
        assert (person.email, person.first_name) == ("ada@example.com", "Ada")  # nothing applied

    def test_keeping_your_own_email_is_fine(self, admin_client, booking):
        assert patch(admin_client, booking, email="ADA@example.com").status_code == 200

    def test_the_history_says_what_changed_and_who_did_it(self, admin_client, booking):
        data = patch(admin_client, booking, first_name="Adele", phone="").json()
        entry = data["history"][0]
        assert entry["action"] == "details_changed"
        assert "nome: 'Ada' → 'Adele'" in entry["detail"]
        assert "telefono: '+39 333 111' → vuoto" in entry["detail"]
        assert "cognome" not in entry["detail"]

    def test_a_change_that_changes_nothing_leaves_no_trace(self, admin_client, booking, db):
        data = patch(admin_client, booking, first_name="Ada", phone="+39 333 111").json()
        assert data["history"] == []
        assert db.scalar(select(AuditLog)) is None

    def test_an_empty_request_is_accepted_and_changes_nothing(self, admin_client, booking):
        assert patch(admin_client, booking).status_code == 200

    def test_unknown_registration_is_404(self, admin_client):
        assert admin_client.patch("/api/admin/registrations/999", json={}).status_code == 404

    def test_admins_only(self, client, outbox, make_participant, booking):
        assert patch(client, booking, first_name="X").status_code == 401
        make_participant("someone@example.com")
        login(client, outbox, email="someone@example.com")
        assert patch(client, booking, first_name="X").status_code == 403


class TestHoldExtension:
    def test_a_later_deadline_is_applied_and_the_booking_stays_pending(
        self, admin_client, booking, db, clock
    ):
        new = (clock() + timedelta(days=6)).isoformat()
        response = patch(admin_client, booking, hold_expires_at=new)
        assert response.status_code == 200, response.text
        assert response.json()["booking"]["status"] == STATUS_PENDING
        db.expire_all()
        assert db.get(Booking, booking.id).hold_expires_at == clock() + timedelta(days=6)

    def test_a_time_without_a_zone_is_read_as_rome_time(self, admin_client, booking, db):
        response = patch(admin_client, booking, hold_expires_at="2026-07-08T11:00")
        assert response.status_code == 200, response.text
        db.expire_all()
        assert (
            db.get(Booking, booking.id).hold_expires_at.isoformat().startswith("2026-07-08T09:00")
        )

    def test_the_seats_stay_taken(self, admin_client, booking, client, slot_ids, clock):
        patch(admin_client, booking, hold_expires_at=(clock() + timedelta(days=6)).isoformat())
        assert available_seats(client)[slot_ids[(d(13), "morning")]] == 24

    def test_an_earlier_or_equal_deadline_is_refused(self, admin_client, booking, db):
        assert (
            patch(
                admin_client, booking, hold_expires_at=booking.hold_expires_at.isoformat()
            ).status_code
            == 422
        )
        earlier = (booking.hold_expires_at - timedelta(hours=1)).isoformat()
        assert patch(admin_client, booking, hold_expires_at=earlier).status_code == 422

    @pytest.mark.parametrize("status", [STATUS_CONFIRMED, STATUS_EXPIRED, STATUS_CANCEL_REQUESTED])
    def test_only_a_pending_booking_can_be_extended(self, admin_client, booking, db, clock, status):
        booking.status = status
        db.commit()
        later = (clock() + timedelta(days=9)).isoformat()
        assert patch(admin_client, booking, hold_expires_at=later).status_code == 409

    def test_a_refused_extension_applies_nothing_else(self, admin_client, booking, db):
        patch(admin_client, booking, first_name="Changed", hold_expires_at="2020-01-01T10:00")
        db.expire_all()
        assert db.get(Participant, booking.participant_id).first_name == "Ada"

    def test_details_and_deadline_can_change_together(self, admin_client, booking, clock):
        later = (clock() + timedelta(days=6)).isoformat()
        data = patch(admin_client, booking, first_name="Adele", hold_expires_at=later).json()
        assert data["participant"]["first_name"] == "Adele"
        assert {e["action"] for e in data["history"]} == {"details_changed", "hold_extended"}

    def test_the_history_shows_old_and_new_deadline_in_rome_time(self, admin_client, booking):
        data = patch(admin_client, booking, hold_expires_at="2026-07-08T11:00").json()
        detail = data["history"][0]["detail"]
        assert "04/07/2026 alle 12:00" in detail and "08/07/2026 alle 11:00" in detail

    def test_reminders_that_are_due_again_are_cleared_and_the_others_kept(
        self, admin_client, booking, db, clock
    ):
        clock.advance(hours=70)  # 3 day hold: both reminders had gone out
        booking.hold_expires_at = booking.hold_started_at + timedelta(days=3)
        booking.reminder_mid_sent_at = booking.hold_started_at + timedelta(hours=36)
        booking.reminder_final_sent_at = booking.hold_started_at + timedelta(hours=48)
        db.commit()
        # 6 days: middle threshold at 72h (still ahead of 70h), final at 120h (ahead too)
        patch(
            admin_client,
            booking,
            hold_expires_at=(booking.hold_started_at + timedelta(days=6)).isoformat(),
        )
        db.expire_all()
        refreshed = db.get(Booking, booking.id)
        assert refreshed.reminder_mid_sent_at is None and refreshed.reminder_final_sent_at is None

    def test_a_reminder_whose_new_threshold_has_passed_stays_marked(
        self, admin_client, booking, db, clock
    ):
        clock.advance(hours=100)
        booking.hold_expires_at = clock() + timedelta(hours=1)
        mid = booking.hold_started_at + timedelta(hours=36)
        booking.reminder_mid_sent_at = mid
        db.commit()
        # 6 days: middle threshold at 72h has passed (now is 100h), so it must not go out twice
        patch(
            admin_client,
            booking,
            hold_expires_at=(booking.hold_started_at + timedelta(days=6)).isoformat(),
        )
        db.expire_all()
        assert db.get(Booking, booking.id).reminder_mid_sent_at == mid


class TestReactivate:
    def expire(self, db, booking, clock):
        booking.status = STATUS_EXPIRED
        db.commit()
        clock.advance(days=5)

    def reactivate(self, client, booking):
        return client.post(f"/api/admin/registrations/{booking.id}/reactivate")

    def test_an_expired_booking_gets_a_new_hold_and_fresh_reminders(
        self, admin_client, booking, db, clock, client, slot_ids
    ):
        booking.reminder_mid_sent_at = clock()
        db.commit()
        self.expire(db, booking, clock)
        response = self.reactivate(admin_client, booking)
        assert response.status_code == 200, response.text
        assert response.json()["booking"]["status"] == STATUS_PENDING
        db.expire_all()
        refreshed = db.get(Booking, booking.id)
        assert refreshed.hold_expires_at == clock() + timedelta(days=3)
        assert refreshed.hold_started_at == clock()
        assert refreshed.reminder_mid_sent_at is None
        assert available_seats(client)[slot_ids[(d(13), "morning")]] == 24
        assert response.json()["history"][0]["action"] == "reactivated"

    def test_a_pending_booking_past_its_deadline_counts_as_expired(
        self, admin_client, booking, clock
    ):
        clock.advance(days=5)
        assert self.reactivate(admin_client, booking).json()["booking"]["status"] == STATUS_PENDING

    def test_it_is_refused_when_a_slot_is_full_and_nothing_changes(
        self, admin_client, booking, db, clock, make_participant, make_booking, slot_ids
    ):
        slot = db.get(Slot, slot_ids[(d(13), "morning")])
        slot.capacity = 1
        db.commit()
        make_booking(make_participant("bob@example.com"), [slot], status=STATUS_CONFIRMED)
        self.expire(db, booking, clock)
        response = self.reactivate(admin_client, booking)
        assert response.status_code == 409
        assert "13/07" in response.json()["detail"]
        db.expire_all()
        assert db.get(Booking, booking.id).status == STATUS_EXPIRED
        assert db.scalar(select(AuditLog)) is None

    @pytest.mark.parametrize("status", [STATUS_CONFIRMED, STATUS_CANCEL_REQUESTED, STATUS_REFUNDED])
    def test_only_an_expired_booking_can_be_reactivated(self, admin_client, booking, db, status):
        booking.status = status
        db.commit()
        assert self.reactivate(admin_client, booking).status_code == 409

    def test_an_expired_booking_that_is_already_paid_is_confirmed(
        self, admin_client, booking, db, clock, outbox
    ):
        pay(db, booking, 1100)
        self.expire(db, booking, clock)
        data = self.reactivate(admin_client, booking).json()
        assert data["booking"]["status"] == STATUS_CONFIRMED
        assert [m.subject for m in outbox.sent] == ["Pagamento ricevuto: sei dentro!"]

    def test_admins_only(self, client, outbox, make_participant, booking):
        assert self.reactivate(client, booking).status_code == 401
        make_participant("someone@example.com")
        login(client, outbox, email="someone@example.com")
        assert self.reactivate(client, booking).status_code == 403
