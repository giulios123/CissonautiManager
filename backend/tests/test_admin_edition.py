from datetime import date

from sqlalchemy import func, select

from app.models import Edition, LegalDocument, PaymentChannel, Slot

PAYLOAD = {
    "name": "Camp 2026",
    "start_date": "2026-07-13",
    "end_date": "2026-07-15",
    "default_capacity": 25,
    "hold_days": 3,
    "base_fee_cents": 1000,
    "per_day_fee_cents": 100,
}


class TestAccess:
    def test_anonymous_is_rejected(self, client):
        assert client.get("/api/admin/edition").status_code == 401

    def test_participant_is_rejected(self, client, make_participant, outbox):
        from tests.test_auth import login

        make_participant("ada@example.com")
        login(client, outbox)
        assert client.get("/api/admin/edition").status_code == 403
        assert client.put("/api/admin/edition", json=PAYLOAD).status_code == 403

    def test_no_edition_yet_is_404(self, admin_client):
        assert admin_client.get("/api/admin/edition").status_code == 404


class TestCreateAndUpdate:
    def test_create_generates_three_slots_per_day_with_defaults(self, admin_client):
        response = admin_client.put("/api/admin/edition", json=PAYLOAD)
        assert response.status_code == 200
        slots = response.json()["slots"]
        assert len(slots) == 9
        limited = [s for s in slots if s["period"] != "evening"]
        assert {s["capacity"] for s in limited} == {25}
        first_day = [s for s in slots if s["date"] == "2026-07-13"]
        assert [(s["period"], s["start_time"], s["end_time"]) for s in first_day] == [
            ("morning", "09:00:00", "13:00:00"),
            ("afternoon", "14:00:00", "18:00:00"),
            ("evening", "19:00:00", "00:00:00"),
        ]

    def test_create_adds_four_disabled_payment_channels(self, admin_client):
        channels = admin_client.put("/api/admin/edition", json=PAYLOAD).json()["payment_channels"]
        assert [c["code"] for c in channels] == ["revolut", "satispay", "paypal", "iban"]
        assert not any(c["enabled"] for c in channels)

    def test_saving_twice_keeps_one_edition_and_no_duplicates(self, admin_client, db):
        admin_client.put("/api/admin/edition", json=PAYLOAD)
        admin_client.put("/api/admin/edition", json=PAYLOAD)
        assert db.scalar(select(func.count()).select_from(Edition)) == 1
        assert db.scalar(select(func.count()).select_from(Slot)) == 9
        assert db.scalar(select(func.count()).select_from(PaymentChannel)) == 4

    def test_changing_hours_and_capacity_applies_to_all_slots(self, admin_client):
        admin_client.put("/api/admin/edition", json=PAYLOAD)
        changed = {
            **PAYLOAD,
            "default_capacity": 30,
            "morning_start": "08:00",
            "morning_end": "12:00",
        }
        slots = admin_client.put("/api/admin/edition", json=changed).json()["slots"]
        assert {s["capacity"] for s in slots if s["period"] != "evening"} == {30}
        mornings = [s for s in slots if s["period"] == "morning"]
        assert {(s["start_time"], s["end_time"]) for s in mornings} == {("08:00:00", "12:00:00")}

    def test_fees_and_hold_days_are_saved(self, admin_client):
        body = {**PAYLOAD, "hold_days": 5, "base_fee_cents": 1500, "per_day_fee_cents": 200}
        saved = admin_client.put("/api/admin/edition", json=body).json()
        assert (saved["hold_days"], saved["base_fee_cents"], saved["per_day_fee_cents"]) == (
            5,
            1500,
            200,
        )
        assert admin_client.get("/api/admin/edition").json()["hold_days"] == 5

    def test_extending_dates_adds_slots(self, admin_client):
        admin_client.put("/api/admin/edition", json=PAYLOAD)
        extended = {**PAYLOAD, "end_date": "2026-07-17"}
        assert len(admin_client.put("/api/admin/edition", json=extended).json()["slots"]) == 15

    def test_shrinking_dates_removes_unbooked_slots(self, admin_client):
        admin_client.put("/api/admin/edition", json=PAYLOAD)
        shrunk = {**PAYLOAD, "end_date": "2026-07-13"}
        assert len(admin_client.put("/api/admin/edition", json=shrunk).json()["slots"]) == 3

    def test_edition_without_dates_has_no_slots(self, admin_client):
        body = {"name": "Camp 2026"}
        assert admin_client.put("/api/admin/edition", json=body).json()["slots"] == []


class TestBookedDaysProtection:
    def test_cannot_remove_a_day_with_booked_slots(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        slot = db.scalar(select(Slot).where(Slot.date == date(2026, 7, 17)))
        make_booking(make_participant("ada@example.com"), [slot])
        shrunk = {**PAYLOAD, "start_date": "2026-07-13", "end_date": "2026-07-16"}
        response = admin_client.put("/api/admin/edition", json=shrunk)
        assert response.status_code == 409
        assert "17/07/2026" in response.json()["detail"]
        assert db.scalar(select(func.count()).select_from(Slot)) == 15
        db.expire_all()
        assert db.scalar(select(Edition)).end_date == date(2026, 7, 17)

    def test_can_remove_days_without_bookings_even_if_others_are_booked(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        slot = db.scalar(select(Slot).where(Slot.date == date(2026, 7, 13)))
        make_booking(make_participant("ada@example.com"), [slot])
        shrunk = {**PAYLOAD, "end_date": "2026-07-14"}
        assert admin_client.put("/api/admin/edition", json=shrunk).status_code == 200


class TestValidation:
    def test_end_before_start(self, admin_client):
        body = {**PAYLOAD, "start_date": "2026-07-15", "end_date": "2026-07-13"}
        assert admin_client.put("/api/admin/edition", json=body).status_code == 422

    def test_only_one_date(self, admin_client):
        body = {"name": "x", "start_date": "2026-07-15"}
        assert admin_client.put("/api/admin/edition", json=body).status_code == 422

    def test_slot_start_must_precede_end(self, admin_client):
        body = {**PAYLOAD, "morning_start": "13:00", "morning_end": "09:00"}
        assert admin_client.put("/api/admin/edition", json=body).status_code == 422

    def test_capacity_and_fees_bounds(self, admin_client):
        for field, value in [("default_capacity", 0), ("hold_days", 0), ("base_fee_cents", -1)]:
            body = {**PAYLOAD, field: value}
            assert admin_client.put("/api/admin/edition", json=body).status_code == 422, field


class TestPaymentChannels:
    def test_update_instructions_and_enable(self, admin_client):
        admin_client.put("/api/admin/edition", json=PAYLOAD)
        body = [
            {"code": "iban", "instructions": "IT00 X000 0000 0000", "enabled": True},
            {"code": "revolut", "instructions": "@cissonauti", "enabled": True},
        ]
        response = admin_client.put("/api/admin/payment-channels", json=body)
        assert response.status_code == 200
        by_code = {c["code"]: c for c in response.json()}
        assert by_code["iban"]["enabled"] and by_code["iban"]["instructions"].startswith("IT00")
        assert by_code["revolut"]["enabled"]
        assert not by_code["paypal"]["enabled"]

    def test_unknown_channel_is_rejected(self, admin_client):
        admin_client.put("/api/admin/edition", json=PAYLOAD)
        body = [{"code": "bitcoin", "instructions": "", "enabled": True}]
        assert admin_client.put("/api/admin/payment-channels", json=body).status_code == 422


class TestLegalDocuments:
    def test_each_publication_is_a_new_version_and_old_ones_are_kept(self, admin_client, db):
        admin_client.put("/api/admin/edition", json=PAYLOAD)
        first = admin_client.post(
            "/api/admin/legal-documents", json={"kind": "privacy", "body": "A"}
        )
        second = admin_client.post(
            "/api/admin/legal-documents", json={"kind": "privacy", "body": "B"}
        )
        assert (first.json()["version"], second.json()["version"]) == (1, 2)
        bodies = db.scalars(select(LegalDocument.body).order_by(LegalDocument.version)).all()
        assert bodies == ["A", "B"]
        assert admin_client.get("/api/admin/edition").json()["privacy"]["body"] == "B"

    def test_versions_are_counted_per_kind(self, admin_client):
        admin_client.put("/api/admin/edition", json=PAYLOAD)
        admin_client.post("/api/admin/legal-documents", json={"kind": "privacy", "body": "A"})
        response = admin_client.post(
            "/api/admin/legal-documents", json={"kind": "disclaimer", "body": "D"}
        )
        assert response.json()["version"] == 1

    def test_empty_text_is_rejected(self, admin_client):
        admin_client.put("/api/admin/edition", json=PAYLOAD)
        response = admin_client.post(
            "/api/admin/legal-documents", json={"kind": "privacy", "body": ""}
        )
        assert response.status_code == 422


class TestWaitlistPercent:
    def test_default_is_20_and_it_can_change(self, admin_client):
        assert admin_client.put("/api/admin/edition", json=PAYLOAD).json()["waitlist_percent"] == 20
        saved = admin_client.put("/api/admin/edition", json=dict(PAYLOAD, waitlist_percent=40))
        assert saved.json()["waitlist_percent"] == 40

    def test_out_of_range_is_rejected(self, admin_client):
        for value in (-1, 101):
            response = admin_client.put(
                "/api/admin/edition", json=dict(PAYLOAD, waitlist_percent=value)
            )
            assert response.status_code == 422
