from datetime import date

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select, text

from app.db import make_engine
from app.domain.booking import available_seats, can_reactivate, has_free_seat
from app.models import Slot
from tests.conftest import reset_database
from tests.helpers import d, payload
from tests.test_admin_edition import PAYLOAD


class TestEveningRules:
    def test_no_capacity_means_unlimited(self):
        assert available_seats(None, 500) is None
        assert has_free_seat(None)

    def test_limited_slots_behave_as_before(self):
        assert available_seats(25, 20) == 5
        assert not has_free_seat(0)

    def test_reactivation_with_unlimited_slots(self):
        assert can_reactivate([None, 3])
        assert not can_reactivate([None, 0])


class TestEveningSlot:
    def test_public_edition_shows_evening_without_limit(self, client, edition):
        evening = client.get("/api/public/edition").json()["days"][0]["slots"][2]
        assert evening["period"] == "evening"
        assert (evening["capacity"], evening["available"]) == (None, None)
        assert (evening["start_time"], evening["end_time"]) == ("19:00:00", "00:00:00")

    def test_more_people_than_the_day_capacity_can_book_the_evening(
        self,
        client,
        db,
        slot_ids,
        make_participant,
        make_booking,
    ):
        evening = db.get(Slot, slot_ids[(d(13), "evening")])
        for n in range(30):
            make_booking(make_participant(f"p{n}@example.com"), [evening])
        body = payload([evening.id], email="late@example.com")
        assert client.post("/api/public/registrations", json=body).status_code == 201

    def test_evening_stays_unlimited_when_default_capacity_changes(self, admin_client):
        admin_client.put("/api/admin/edition", json=PAYLOAD)
        slots = admin_client.put(
            "/api/admin/edition", json={**PAYLOAD, "default_capacity": 10}
        ).json()["slots"]
        assert {s["capacity"] for s in slots if s["period"] == "evening"} == {None}
        assert {s["capacity"] for s in slots if s["period"] != "evening"} == {10}

    def test_evening_only_day_counts_for_the_daily_fee(self, client, slot_ids):
        body = payload([slot_ids[(d(13), "evening")]])
        assert (
            client.post("/api/public/registrations", json=body).json()["booking"][
                "amount_due_cents"
            ]
            == 1100
        )

    def test_evening_and_daytime_of_the_same_day_cost_one_day(self, client, slot_ids):
        ids = [slot_ids[(d(13), "morning")], slot_ids[(d(13), "evening")]]
        booking = client.post("/api/public/registrations", json=payload(ids)).json()["booking"]
        assert booking["amount_due_cents"] == 1100

    def test_evening_and_another_day(self, client, slot_ids):
        ids = [slot_ids[(d(13), "evening")], slot_ids[(d(14), "afternoon")]]
        booking = client.post("/api/public/registrations", json=payload(ids)).json()["booking"]
        assert booking["amount_due_cents"] == 1200

    def test_summary_and_email_name_the_evening(self, client, outbox, slot_ids):
        body = payload([slot_ids[(d(13), "evening")]])
        booking = client.post("/api/public/registrations", json=body).json()["booking"]
        assert booking["slots"][0]["label"] == "lun 13/07 sera (19:00-00:00)"
        assert "sera (19:00-00:00)" in outbox.sent[0].body


class TestEveningHours:
    def test_hours_are_configurable(self, admin_client):
        body = {**PAYLOAD, "evening_start": "20:00", "evening_end": "23:30"}
        slots = admin_client.put("/api/admin/edition", json=body).json()["slots"]
        evenings = [s for s in slots if s["period"] == "evening"]
        assert {(s["start_time"], s["end_time"]) for s in evenings} == {("20:00:00", "23:30:00")}

    def test_midnight_is_a_valid_end(self, admin_client):
        body = {**PAYLOAD, "evening_start": "19:00", "evening_end": "00:00"}
        assert admin_client.put("/api/admin/edition", json=body).status_code == 200

    @pytest.mark.parametrize(
        "start,end", [("22:00", "21:00"), ("20:00", "20:00"), ("00:00", "00:00")]
    )
    def test_invalid_ranges_are_rejected(self, admin_client, start, end):
        body = {**PAYLOAD, "evening_start": start, "evening_end": end}
        assert admin_client.put("/api/admin/edition", json=body).status_code == 422

    def test_existing_edition_gets_evening_slots_on_next_save(self, admin_client, db):
        admin_client.put("/api/admin/edition", json=PAYLOAD)
        db.execute(text("DELETE FROM slot WHERE period = 'evening'"))
        db.commit()
        slots = admin_client.put("/api/admin/edition", json=PAYLOAD).json()["slots"]
        assert len([s for s in slots if s["period"] == "evening"]) == 3


# No explicit ids: SQL Server identity columns reject them.
SLOT_INSERT = "INSERT INTO slot (edition_id, date, period, start_time, end_time, capacity)"
EDITION_ID = "(SELECT MIN(id) FROM edition)"
MORNING = f" VALUES ({EDITION_ID}, :day, 'morning', '09:00:00', '13:00:00', 25)"
EVENING = f" VALUES ({EDITION_ID}, :day, 'evening', '19:00:00', '00:00:00', NULL)"


class TestMigration0002:
    def test_existing_data_gets_evening_defaults_and_roundtrips(self, database_url):
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", database_url)
        engine = make_engine(database_url)
        reset_database(engine)
        command.upgrade(config, "0001")
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO edition (name, morning_start, morning_end, afternoon_start,"
                    " afternoon_end, default_capacity, hold_days, base_fee_cents,"
                    " per_day_fee_cents, is_active) VALUES ('Old', '09:00:00', '13:00:00',"
                    " '14:00:00', '18:00:00', 25, 3, 1000, 100, 1)"
                )
            )
            conn.execute(
                text(SLOT_INSERT + MORNING),
                {"day": date(2026, 7, 13)},
            )
        command.upgrade(config, "0002")
        with engine.connect() as conn:
            row = conn.execute(text("SELECT evening_start, evening_end FROM edition")).one()
        assert str(row[0]).startswith("19:00") and str(row[1]).startswith("00:00")
        with engine.begin() as conn:
            conn.execute(
                text(SLOT_INSERT + EVENING),
                {"day": date(2026, 7, 13)},
            )
        command.downgrade(config, "0001")
        with engine.connect() as conn:
            periods = conn.execute(select(text("period")).select_from(text("slot"))).scalars().all()
        assert periods == ["morning"]
        command.upgrade(config, "head")
        engine.dispose()
