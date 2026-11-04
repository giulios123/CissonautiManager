import re
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    Booking,
    Participant,
    Slot,
)


@pytest.fixture
def slot_ids(db, edition):
    """Slot ids keyed by (date, period) for the 13-17 July edition."""
    return {(s.date, s.period): s.id for s in db.scalars(select(Slot))}


def payload(slot_ids_list, **overrides):
    body = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "phone": "+39 333 1234567",
        "invited_by": "Grace",
        "can_bring": "Un talk sulle macchine analitiche",
        "slot_ids": slot_ids_list,
        "accept_privacy": True,
        "accept_disclaimer": True,
        "privacy_version": 1,
        "disclaimer_version": 1,
    }
    body.update(overrides)
    return body


def d(day: int) -> date:
    return date(2026, 7, day)


class TestPublicEdition:
    def test_closed_when_no_edition(self, client):
        data = client.get("/api/public/edition").json()
        assert data["registration_open"] is False
        assert data["days"] == []

    def test_closed_without_legal_texts(self, client, admin_client):
        admin_client.put(
            "/api/admin/edition",
            json={"name": "Camp", "start_date": "2026-07-13", "end_date": "2026-07-13"},
        )
        assert client.get("/api/public/edition").json()["registration_open"] is False

    def test_open_lists_days_with_availability(self, client, edition):
        data = client.get("/api/public/edition").json()
        assert data["registration_open"] is True
        assert [day["date"] for day in data["days"]] == [f"2026-07-{n}" for n in range(13, 18)]
        assert all(len(day["slots"]) == 2 for day in data["days"])
        assert {s["available"] for day in data["days"] for s in day["slots"]} == {25}
        assert data["base_fee_cents"] == 1000 and data["per_day_fee_cents"] == 100
        assert data["privacy"]["version"] == 1

    def test_only_enabled_channels_are_listed(self, client, edition, admin_client):
        admin_client.put(
            "/api/admin/payment-channels",
            json=[{"code": "iban", "instructions": "IT00", "enabled": True}],
        )
        channels = client.get("/api/public/edition").json()["payment_channels"]
        assert [c["code"] for c in channels] == ["iban"]

    def test_availability_counts_pending_and_confirmed_only(
        self, client, db, edition, make_participant, make_booking, slot_ids, clock
    ):
        slot = db.get(Slot, slot_ids[(d(13), "morning")])
        make_booking(make_participant("a@example.com"), [slot], STATUS_PENDING)
        make_booking(make_participant("b@example.com"), [slot], STATUS_CONFIRMED)
        make_booking(make_participant("c@example.com"), [slot], STATUS_EXPIRED)
        make_booking(make_participant("d@example.com"), [slot], STATUS_CANCEL_REQUESTED)
        make_booking(
            make_participant("e@example.com"),
            [slot],
            STATUS_PENDING,
            hold_expires_at=clock() - timedelta(minutes=1),
        )
        data = client.get("/api/public/edition").json()
        first = data["days"][0]["slots"]
        morning = next(s for s in first if s["id"] == slot.id)
        assert morning["available"] == 23


class TestRegistration:
    def test_creates_pending_booking_with_amount_code_and_deadline(
        self, client, db, slot_ids, clock
    ):
        ids = [slot_ids[(d(13), "morning")], slot_ids[(d(14), "afternoon")]]
        response = client.post("/api/public/registrations", json=payload(ids))
        assert response.status_code == 201
        data = response.json()
        assert data["result"] == "created"
        booking = data["booking"]
        assert booking["status"] == STATUS_PENDING
        assert booking["amount_due_cents"] == 1200
        assert re.fullmatch(r"CSC-[A-Z2-9]{4}", booking["personal_code"])
        assert datetime.fromisoformat(booking["hold_expires_at"]) == clock() + timedelta(days=3)
        assert len(booking["slots"]) == 2

        participant = db.scalar(select(Participant))
        assert participant.email == "ada@example.com"
        assert participant.personal_code == booking["personal_code"]
        assert participant.can_bring.startswith("Un talk")
        assert participant.role == "participant"

    def test_morning_and_afternoon_of_same_day_cost_one_day(self, client, slot_ids):
        ids = [slot_ids[(d(13), "morning")], slot_ids[(d(13), "afternoon")]]
        booking = client.post("/api/public/registrations", json=payload(ids)).json()["booking"]
        assert booking["amount_due_cents"] == 1100

    def test_three_non_contiguous_days(self, client, slot_ids):
        ids = [slot_ids[(d(n), "morning")] for n in (13, 15, 17)]
        booking = client.post("/api/public/registrations", json=payload(ids)).json()["booking"]
        assert booking["amount_due_cents"] == 1300

    def test_payment_channels_are_in_the_summary(self, client, admin_client, slot_ids):
        admin_client.put(
            "/api/admin/payment-channels",
            json=[{"code": "satispay", "instructions": "333 000 111", "enabled": True}],
        )
        body = payload([slot_ids[(d(13), "morning")]])
        booking = client.post("/api/public/registrations", json=body).json()["booking"]
        assert booking["payment_channels"] == [
            {"code": "satispay", "label": "Satispay", "instructions": "333 000 111"}
        ]

    def test_saves_accepted_legal_versions_with_timestamp(self, client, db, slot_ids, clock):
        client.post("/api/public/registrations", json=payload([slot_ids[(d(13), "morning")]]))
        booking = db.scalar(select(Booking))
        assert booking.privacy_document_id and booking.disclaimer_document_id
        assert booking.privacy_accepted_at == clock()
        assert booking.disclaimer_accepted_at == clock()

    def test_sends_email_with_summary_code_and_magic_link(self, client, outbox, slot_ids):
        client.post("/api/public/registrations", json=payload([slot_ids[(d(13), "morning")]]))
        assert len(outbox.sent) == 1
        message = outbox.sent[0]
        assert message.to == "ada@example.com"
        assert "CSC-" in message.body
        assert "11,00 €" in message.body
        assert "lun 13/07 mattina (09:00-13:00)" in message.body
        assert "https://camp.example.org/accedi/verifica?token=" in message.body

    def test_deadline_in_email_is_shown_in_rome_time(self, client, outbox, slot_ids):
        client.post("/api/public/registrations", json=payload([slot_ids[(d(13), "morning")]]))
        assert "04/07/2026 alle 12:00" in outbox.sent[0].body  # 10:00 UTC is 12:00 in Rome

    def test_email_link_logs_the_participant_in(self, client, outbox, slot_ids):
        client.post("/api/public/registrations", json=payload([slot_ids[(d(13), "morning")]]))
        token = re.search(r"token=([\w-]+)", outbox.sent[0].body).group(1)
        assert client.post("/api/auth/verify", json={"token": token}).json()["redirect"] == "/io"

    def test_optional_fields_can_be_omitted(self, client, slot_ids):
        body = payload([slot_ids[(d(13), "morning")]])
        del body["phone"], body["invited_by"]
        assert client.post("/api/public/registrations", json=body).status_code == 201

    def test_whitespace_is_trimmed_and_email_lowercased(self, client, db, slot_ids):
        body = payload([slot_ids[(d(13), "morning")]], first_name="  Ada ", email="Ada@Example.COM")
        client.post("/api/public/registrations", json=body)
        participant = db.scalar(select(Participant))
        assert (participant.first_name, participant.email) == ("Ada", "ada@example.com")


class TestValidation:
    @pytest.mark.parametrize(
        "override",
        [
            {"first_name": ""},
            {"last_name": "   "},
            {"email": "not-an-email"},
            {"can_bring": ""},
            {"slot_ids": []},
            {"accept_privacy": False},
            {"accept_disclaimer": False},
        ],
    )
    def test_invalid_input_is_rejected(self, client, db, slot_ids, outbox, override):
        body = payload([slot_ids[(d(13), "morning")]], **override)
        assert client.post("/api/public/registrations", json=body).status_code == 422
        assert db.scalar(select(func.count()).select_from(Participant)) == 0
        assert outbox.sent == []

    def test_unknown_slot_is_rejected(self, client, db, slot_ids):
        body = payload([slot_ids[(d(13), "morning")], 99999])
        assert client.post("/api/public/registrations", json=body).status_code == 422
        assert db.scalar(select(func.count()).select_from(Booking)) == 0

    def test_duplicated_slot_ids_count_once(self, client, slot_ids):
        sid = slot_ids[(d(13), "morning")]
        response = client.post("/api/public/registrations", json=payload([sid, sid]))
        assert response.status_code == 201
        assert len(response.json()["booking"]["slots"]) == 1

    def test_outdated_legal_version_is_rejected(self, client, admin_client, db, slot_ids):
        admin_client.post("/api/admin/legal-documents", json={"kind": "privacy", "body": "v2"})
        body = payload([slot_ids[(d(13), "morning")]])
        response = client.post("/api/public/registrations", json=body)
        assert response.status_code == 409
        assert "testi legali" in response.json()["detail"]
        assert db.scalar(select(func.count()).select_from(Booking)) == 0

    def test_closed_registration_is_rejected(self, client):
        response = client.post("/api/public/registrations", json=payload([1]))
        assert response.status_code == 409


class TestCapacity:
    def _fill(self, db, slot_id, make_participant, make_booking, count):
        slot = db.get(Slot, slot_id)
        for n in range(count):
            make_booking(make_participant(f"p{n}@example.com"), [slot])

    def test_last_seat_can_be_taken_then_slot_is_full(
        self, client, db, slot_ids, make_participant, make_booking
    ):
        sid = slot_ids[(d(13), "morning")]
        self._fill(db, sid, make_participant, make_booking, 24)
        assert client.post("/api/public/registrations", json=payload([sid])).status_code == 201
        other = payload([sid], email="grace@example.com", first_name="Grace")
        response = client.post("/api/public/registrations", json=other)
        assert response.status_code == 409
        assert response.json()["full_slot_ids"] == [sid]

    def test_full_slot_creates_nothing_and_names_the_slot(
        self, client, db, slot_ids, make_participant, make_booking, outbox
    ):
        full_id = slot_ids[(d(13), "morning")]
        self._fill(db, full_id, make_participant, make_booking, 25)
        before = db.scalar(select(func.count()).select_from(Participant))
        body = payload([full_id, slot_ids[(d(14), "morning")]], email="late@example.com")
        response = client.post("/api/public/registrations", json=body)
        assert response.status_code == 409
        assert "lun 13/07 mattina" in response.json()["detail"]
        assert db.scalar(select(func.count()).select_from(Participant)) == before
        assert outbox.sent == []

    def test_other_slots_of_the_same_request_stay_free_for_others(
        self, client, db, slot_ids, make_participant, make_booking
    ):
        full_id = slot_ids[(d(13), "morning")]
        self._fill(db, full_id, make_participant, make_booking, 25)
        body = payload([slot_ids[(d(14), "morning")]], email="other@example.com")
        assert client.post("/api/public/registrations", json=body).status_code == 201

    def test_expired_hold_frees_the_seat(
        self, client, db, slot_ids, make_participant, make_booking, clock
    ):
        sid = slot_ids[(d(13), "morning")]
        slot = db.get(Slot, sid)
        db.get(Slot, sid).capacity = 1
        db.commit()
        make_booking(make_participant("first@example.com"), [slot])
        body = payload([sid], email="second@example.com")
        assert client.post("/api/public/registrations", json=body).status_code == 409
        clock.advance(days=3)
        assert client.post("/api/public/registrations", json=body).status_code == 201

    def test_expiry_is_written_to_the_database_on_read(
        self, client, db, slot_ids, make_participant, make_booking, clock
    ):
        slot = db.get(Slot, slot_ids[(d(13), "morning")])
        booking = make_booking(make_participant("first@example.com"), [slot])
        clock.advance(days=4)
        client.get("/api/public/edition")
        db.expire_all()
        assert db.get(Booking, booking.id).status == STATUS_EXPIRED

    def test_cancelled_and_confirmed_bookings_follow_the_rules(
        self, client, db, slot_ids, make_participant, make_booking
    ):
        sid = slot_ids[(d(13), "morning")]
        slot = db.get(Slot, sid)
        slot.capacity = 1
        db.commit()
        make_booking(make_participant("a@example.com"), [slot], STATUS_CANCEL_REQUESTED)
        body = payload([sid], email="b@example.com")
        assert client.post("/api/public/registrations", json=body).status_code == 201
        slot = db.get(Slot, sid)
        body = payload([sid], email="c@example.com")
        assert client.post("/api/public/registrations", json=body).status_code == 409


class TestSameEmail:
    def test_active_booking_blocks_a_new_one_and_sends_a_link(self, client, db, slot_ids, outbox):
        sid = slot_ids[(d(13), "morning")]
        client.post("/api/public/registrations", json=payload([sid]))
        response = client.post(
            "/api/public/registrations",
            json=payload([slot_ids[(d(14), "morning")]], email="ADA@example.com"),
        )
        assert response.status_code == 201
        assert response.json()["result"] == "already_registered"
        assert db.scalar(select(func.count()).select_from(Booking)) == 1
        assert db.scalar(select(func.count()).select_from(Participant)) == 1
        assert len(outbox.sent) == 2
        assert "già iscritto" in outbox.sent[1].body
        assert "token=" in outbox.sent[1].body

    def test_expired_booking_allows_a_new_one_when_there_is_room(self, client, db, slot_ids, clock):
        sid = slot_ids[(d(13), "morning")]
        client.post("/api/public/registrations", json=payload([sid]))
        clock.advance(days=3, minutes=1)
        response = client.post("/api/public/registrations", json=payload([sid]))
        assert response.json()["result"] == "created"
        assert db.scalar(select(func.count()).select_from(Participant)) == 1
        assert db.scalar(select(func.count()).select_from(Booking)) == 2

    def test_expired_booking_is_rejected_when_the_slot_is_now_full(
        self, client, db, slot_ids, clock, make_participant, make_booking
    ):
        sid = slot_ids[(d(13), "morning")]
        client.post("/api/public/registrations", json=payload([sid]))
        clock.advance(days=3, minutes=1)
        slot = db.get(Slot, sid)
        slot.capacity = 1
        db.commit()
        make_booking(make_participant("someone@example.com"), [slot])
        response = client.post("/api/public/registrations", json=payload([sid]))
        assert response.status_code == 409


class TestEmbedding:
    def test_registration_page_can_be_framed_by_google_sites_only(self, client):
        csp = client.get("/iscrizione").headers["content-security-policy"]
        assert csp == "frame-ancestors https://sites.google.com https://*.googleusercontent.com"

    def test_trailing_slash_is_treated_the_same(self, client):
        assert "sites.google.com" in client.get("/iscrizione/").headers["content-security-policy"]

    @pytest.mark.parametrize("path", ["/", "/accedi", "/admin", "/api/health", "/api/me"])
    def test_everything_else_cannot_be_framed_by_others(self, client, path):
        assert client.get(path).headers["content-security-policy"] == "frame-ancestors 'self'"
