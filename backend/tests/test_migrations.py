from datetime import datetime

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text

import app.models  # noqa: F401
from app.db import Base, make_engine
from tests.conftest import reset_database


@pytest.fixture
def alembic_config(database_url) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    return config


@pytest.fixture
def empty_database(database_url):
    engine = make_engine(database_url)
    reset_database(engine)
    engine.dispose()


def test_upgrade_from_scratch_creates_all_tables(alembic_config, database_url, empty_database):
    command.upgrade(alembic_config, "head")
    engine = make_engine(database_url)
    tables = set(inspect(engine).get_table_names())
    assert set(Base.metadata.tables) <= tables
    command.downgrade(alembic_config, "base")
    remaining = set(inspect(engine).get_table_names()) - {"alembic_version"}
    assert remaining == set()
    engine.dispose()


def test_downgrade_0020_keeps_participant_cancellation_actor(
    alembic_config, database_url, empty_database
):
    command.upgrade(alembic_config, "0019")
    engine = make_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO participant"
                " (first_name, last_name, email, personal_code, role, locale, created_at)"
                " VALUES ('Ada', 'Lovelace', 'ada@example.com', 'CSC-ADA1', 'participant',"
                " 'it', '2026-07-01 10:00:00')"
            )
        )
    command.upgrade(alembic_config, "0020")
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO audit_log"
                " (at, actor_id, participant_id, action, outcome, detail)"
                " VALUES ('2026-07-01 10:00:00', NULL, 1, 'cancelled_by_participant',"
                " 'removed', 'participant cancellation')"
            )
        )
    command.downgrade(alembic_config, "0019")
    with engine.connect() as connection:
        actor_id = connection.execute(text("SELECT actor_id FROM audit_log")).scalar_one()
        columns = {column["name"] for column in inspect(connection).get_columns("audit_log")}
    engine.dispose()

    assert actor_id == 1
    assert "participant_id" not in columns


def test_models_and_migrations_are_in_sync(alembic_config, database_url, empty_database):
    command.upgrade(alembic_config, "head")
    engine = make_engine(database_url)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        diff = compare_metadata(context, Base.metadata)
    engine.dispose()
    assert diff == [], f"models differ from migrations, create a migration: {diff}"


def test_migration_0015_preserves_legacy_activity_time_and_price(
    alembic_config, database_url, empty_database
):
    command.upgrade(alembic_config, "0014")
    engine = make_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO edition (name, start_date, end_date, morning_start, morning_end,"
                " afternoon_start, afternoon_end, evening_start, evening_end, default_capacity,"
                " hold_days, base_fee_cents, per_day_fee_cents, is_active, waitlist_percent,"
                " lunch_price_cents, dinner_price_cents) VALUES ('Camp', '2026-07-13',"
                " '2026-07-17', '09:00:00', '13:00:00', '14:00:00', '18:00:00', '19:00:00',"
                " '00:00:00', 25, 3, 1000, 100, 1, 20, 800, 1200)"
            )
        )
        edition_id = connection.execute(text("SELECT id FROM edition")).scalar_one()
        connection.execute(
            text(
                "INSERT INTO activity (edition_id, title, date, period, time_label, price_cents,"
                " created_at) VALUES (:e, 'Legacy', '2026-07-13', 'morning', 'around ten',"
                " 1500, '2026-07-01 10:00:00')"
            ),
            {"e": edition_id},
        )
    command.upgrade(alembic_config, "head")
    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT time_label, price_cents, payment_mode, starts_at, ends_at, title_it,"
                " title_en, description_it, description_en FROM activity"
            )
        ).one()
        assert tuple(row) == (
            "around ten",
            1500,
            "organizer",
            None,
            None,
            None,
            None,
            None,
            None,
        )
    command.downgrade(alembic_config, "0014")
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT time_label FROM activity")).scalar_one() == "around ten"
        )
        assert "meal_setting" not in inspect(connection).get_table_names()
    engine.dispose()


def test_migration_0016_preserves_legacy_legal_text_and_starts_with_no_consent_events(
    alembic_config, database_url, empty_database
):
    command.upgrade(alembic_config, "0015")
    engine = make_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO edition (name, morning_start, morning_end, afternoon_start,"
                " afternoon_end, evening_start, evening_end, default_capacity, hold_days,"
                " base_fee_cents, per_day_fee_cents, is_active, waitlist_percent,"
                " lunch_price_cents, dinner_price_cents) VALUES ('Camp', '09:00', '13:00',"
                " '14:00', '18:00', '19:00', '00:00', 25, 3, 1000, 100, 1, 20, 800, 1200)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO legal_document (edition_id, kind, version, body, published_at)"
                " VALUES (1, 'privacy', 1, 'Testo originale', '2026-07-01 09:00:00')"
            )
        )
    command.upgrade(alembic_config, "0016")
    with engine.connect() as connection:
        document = connection.execute(
            text("SELECT body, body_it, body_en FROM legal_document WHERE kind = 'privacy'")
        ).one()
        events = connection.execute(text("SELECT COUNT(*) FROM consent_event")).scalar_one()
    command.downgrade(alembic_config, "0015")
    with engine.connect() as connection:
        columns = {column["name"] for column in inspect(connection).get_columns("legal_document")}
        tables = set(inspect(connection).get_table_names())
    engine.dispose()
    assert tuple(document) == ("Testo originale", None, None)
    assert events == 0
    assert "body_it" not in columns and "body_en" not in columns
    assert "consent_event" not in tables


def test_migration_0017_keeps_legacy_policy_and_payment_notice_without_repricing(
    alembic_config, database_url, empty_database
):
    command.upgrade(alembic_config, "0016")
    engine = make_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO edition (name, start_date, end_date, morning_start, morning_end,"
                " afternoon_start, afternoon_end, evening_start, evening_end, default_capacity,"
                " hold_days, base_fee_cents, per_day_fee_cents, is_active, waitlist_percent,"
                " lunch_price_cents, dinner_price_cents) VALUES ('Camp', '2026-07-13',"
                " '2026-07-17', '09:00:00', '13:00:00', '14:00:00', '18:00:00', '19:00:00',"
                " '00:00:00', 25, 3, 1000, 100, 1, 20, 800, 1200)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO participant (first_name, last_name, email, personal_code, role,"
                " locale, created_at) VALUES ('Ada', 'Lovelace', 'ada@example.com', 'CSC-AAAA',"
                " 'participant', 'it', '2026-07-01 10:00:00')"
            )
        )
        for kind in ("privacy", "disclaimer"):
            connection.execute(
                text(
                    "INSERT INTO legal_document (edition_id, kind, version, body, published_at)"
                    " VALUES (1, :kind, 1, 'Legacy text', '2026-07-01 09:00:00')"
                ),
                {"kind": kind},
            )
        connection.execute(
            text(
                "INSERT INTO booking (edition_id, participant_id, status, hold_expires_at,"
                " hold_started_at, amount_due_cents, privacy_document_id, privacy_accepted_at,"
                " disclaimer_document_id, disclaimer_accepted_at, created_at) VALUES"
                " (1, 1, 'in_attesa_pagamento', '2026-07-04 10:00:00',"
                " '2026-07-01 10:00:00', 1350, 1, '2026-07-01 10:00:00', 2,"
                " '2026-07-01 10:00:00', '2026-07-01 10:00:00')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO payment (booking_id, amount_cents, channel, paid_on, recorded_by_id,"
                " created_at, confirmation_email_due_at) VALUES"
                " (1, 400, 'iban', '2026-07-02', 1, '2026-07-02 10:00:00',"
                " '2026-07-02 10:00:30')"
            )
        )

    command.upgrade(alembic_config, "0017")
    with engine.connect() as connection:
        edition = connection.execute(
            text(
                "SELECT confirmation_policy, confirmation_policy_activated_at,"
                " confirmation_policy_preview_token FROM edition"
            )
        ).one()
        booking = connection.execute(
            text(
                "SELECT amount_due_cents, registration_fee_cents, confirmation_cycle,"
                " confirmation_claimed_cycle, confirmation_notice_due_at,"
                " confirmation_notice_payment_id FROM booking"
            )
        ).one()
        payment = connection.execute(
            text("SELECT amount_cents, confirmation_email_due_at FROM payment")
        ).one()
    command.downgrade(alembic_config, "0016")
    with engine.connect() as connection:
        edition_columns = {c["name"] for c in inspect(connection).get_columns("edition")}
        booking_columns = {c["name"] for c in inspect(connection).get_columns("booking")}
        preserved = connection.execute(text("SELECT amount_due_cents FROM booking")).scalar_one()
        legacy_due = connection.execute(
            text("SELECT confirmation_email_due_at FROM payment")
        ).scalar_one()
    engine.dispose()

    assert tuple(edition) == ("legacy_total", None, None)
    assert tuple(booking) == (1350, None, 0, 0, None, None)
    assert payment.amount_cents == 400 and payment.confirmation_email_due_at is not None
    assert preserved == 1350 and legacy_due is not None
    assert "confirmation_policy" not in edition_columns
    assert "registration_fee_cents" not in booking_columns


def test_migration_0019_imports_legacy_privacy_proofs_without_inventing_locale(
    alembic_config, database_url, empty_database
):
    command.upgrade(alembic_config, "0017")
    engine = make_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO edition (name, start_date, end_date, morning_start, morning_end,"
                " afternoon_start, afternoon_end, evening_start, evening_end, default_capacity,"
                " hold_days, base_fee_cents, per_day_fee_cents, is_active, waitlist_percent,"
                " lunch_price_cents, dinner_price_cents, confirmation_policy)"
                " VALUES ('Camp', '2026-07-13', '2026-07-17', '09:00:00', '13:00:00',"
                " '14:00:00', '18:00:00', '19:00:00', '00:00:00', 25, 3, 1000, 100,"
                " 1, 20, 800, 1200, 'legacy_total')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO participant (first_name, last_name, email, personal_code, role,"
                " locale, created_at) VALUES ('Ada', 'Lovelace', 'ada@example.com', 'CSC-AAAA',"
                " 'participant', 'it', '2026-07-01 10:00:00')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO legal_document (edition_id, kind, version, body, published_at)"
                " VALUES (1, 'privacy', 1, 'Legacy privacy text', '2026-07-01 09:00:00')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO legal_document (edition_id, kind, version, body, published_at)"
                " VALUES (1, 'disclaimer', 1, 'Legacy disclaimer', '2026-07-01 09:00:00')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO slot (edition_id, date, period, start_time, end_time, capacity)"
                " VALUES (1, '2026-07-13', 'morning', '09:00:00', '13:00:00', 25)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO booking (edition_id, participant_id, status, hold_expires_at,"
                " hold_started_at, amount_due_cents, confirmation_cycle,"
                " confirmation_claimed_cycle, privacy_document_id, privacy_accepted_at,"
                " disclaimer_document_id, disclaimer_accepted_at, created_at) VALUES"
                " (1, 1, 'in_attesa_pagamento', '2026-07-04 10:00:00',"
                " '2026-07-01 10:00:00', 1100, 0, 0, 1, '2026-07-01 10:00:00', 2,"
                " '2026-07-01 10:00:00', '2026-07-01 10:00:00')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO waitlist_entry (slot_id, participant_id, created_at,"
                " privacy_document_id, privacy_accepted_at, disclaimer_document_id,"
                " disclaimer_accepted_at, promoted_as_plus_one) VALUES"
                " (1, 1, '2026-07-02 10:00:00', 1, '2026-07-01 10:00:00', 2,"
                " '2026-07-01 10:00:00', 0)"
            )
        )

    command.upgrade(alembic_config, "0019")
    with engine.connect() as connection:
        events = connection.execute(
            text(
                "SELECT edition_id, participant_id, kind, action, document_id, locale,"
                " recorded_at, source FROM consent_event WHERE kind = 'privacy'"
            )
        ).all()
        attempt_columns = {
            column["name"] for column in inspect(connection).get_columns("privacy_notice_attempt")
        }
    engine.dispose()

    assert len(events) == 1
    assert tuple(events[0][:6]) == (1, 1, "privacy", "accepted", 1, None)
    recorded_at = events[0][6]
    if isinstance(recorded_at, datetime):
        recorded_at = recorded_at.isoformat(sep=" ", timespec="microseconds")
    assert recorded_at == "2026-07-01 10:00:00.000000"
    assert events[0][7] == "legacy_import"
    assert {"attempted_at", "participant_id", "document_id"} <= attempt_columns

    command.downgrade(alembic_config, "0017")
    engine = make_engine(database_url)
    with engine.connect() as connection:
        assert "privacy_notice_attempt" not in inspect(connection).get_table_names()
        assert (
            connection.execute(
                text("SELECT COUNT(*) FROM consent_event WHERE kind = 'privacy'")
            ).scalar_one()
            == 0
        )
        locale = next(
            column
            for column in inspect(connection).get_columns("consent_event")
            if column["name"] == "locale"
        )
        assert locale["nullable"] is False
    engine.dispose()


def test_migration_0003_fills_hold_started_at_from_created_at(
    alembic_config, database_url, empty_database
):
    command.upgrade(alembic_config, "0002")
    engine = make_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO edition (name, start_date, end_date, morning_start, morning_end,"
                " afternoon_start, afternoon_end, evening_start, evening_end, default_capacity,"
                " hold_days, base_fee_cents, per_day_fee_cents, is_active) VALUES"
                " ('Camp', '2026-07-13', '2026-07-17', '09:00:00', '13:00:00', '14:00:00',"
                " '18:00:00', '19:00:00', '00:00:00', 25, 3, 1000, 100, 1)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO participant (first_name, last_name, email, personal_code, role,"
                " created_at) VALUES ('Ada', 'Lovelace', 'ada@example.com', 'CSC-AAAA',"
                " 'participant', '2026-07-01 10:00:00')"
            )
        )
        edition_id = connection.execute(text("SELECT id FROM edition")).scalar_one()
        participant_id = connection.execute(text("SELECT id FROM participant")).scalar_one()
        for kind in ("privacy", "disclaimer"):
            connection.execute(
                text(
                    "INSERT INTO legal_document (edition_id, kind, version, body, published_at)"
                    " VALUES (:e, :k, 1, 'testo', '2026-07-01 09:00:00')"
                ),
                {"e": edition_id, "k": kind},
            )
        doc_id = connection.execute(text("SELECT MIN(id) FROM legal_document")).scalar_one()
        connection.execute(
            text(
                "INSERT INTO booking (edition_id, participant_id, status, hold_expires_at,"
                " amount_due_cents, privacy_document_id, privacy_accepted_at,"
                " disclaimer_document_id, disclaimer_accepted_at, created_at) VALUES"
                " (:e, :p, 'in_attesa_pagamento', '2026-07-04 10:00:00', 1100, :d,"
                " '2026-07-01 10:00:00', :d, '2026-07-01 10:00:00', '2026-07-01 10:00:00')"
            ),
            {"e": edition_id, "p": participant_id, "d": doc_id},
        )
    command.upgrade(alembic_config, "0003")
    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT hold_started_at, created_at, reminder_mid_sent_at, cancel_requested_at"
                " FROM booking"
            )
        ).one()
    engine.dispose()
    assert row.hold_started_at == row.created_at
    assert row.reminder_mid_sent_at is None
    assert row.cancel_requested_at is None


def test_migration_0005_sets_the_default_waitlist_percent(
    alembic_config, database_url, empty_database
):
    command.upgrade(alembic_config, "0004")
    engine = make_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO edition (name, start_date, end_date, morning_start, morning_end,"
                " afternoon_start, afternoon_end, evening_start, evening_end, default_capacity,"
                " hold_days, base_fee_cents, per_day_fee_cents, is_active) VALUES"
                " ('Camp', '2026-07-13', '2026-07-17', '09:00:00', '13:00:00', '14:00:00',"
                " '18:00:00', '19:00:00', '00:00:00', 25, 3, 1000, 100, 1)"
            )
        )
    command.upgrade(alembic_config, "0005")
    with engine.connect() as connection:
        percent = connection.execute(text("SELECT waitlist_percent FROM edition")).scalar_one()
    command.downgrade(alembic_config, "0004")
    engine.dispose()
    assert percent == 20


def test_migration_0006_sets_the_placeholder_meal_prices(
    alembic_config, database_url, empty_database
):
    command.upgrade(alembic_config, "0005")
    engine = make_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO edition (name, start_date, end_date, morning_start, morning_end,"
                " afternoon_start, afternoon_end, evening_start, evening_end, default_capacity,"
                " hold_days, base_fee_cents, per_day_fee_cents, is_active, waitlist_percent)"
                " VALUES ('Camp', '2026-07-13', '2026-07-17', '09:00:00', '13:00:00',"
                " '14:00:00', '18:00:00', '19:00:00', '00:00:00', 25, 3, 1000, 100, 1, 20)"
            )
        )
    command.upgrade(alembic_config, "0006")
    with engine.connect() as connection:
        prices = connection.execute(
            text("SELECT lunch_price_cents, dinner_price_cents FROM edition")
        ).one()
    command.downgrade(alembic_config, "0005")
    engine.dispose()
    assert tuple(prices) == (800, 1200)


def test_migration_0008_leaves_existing_participants_unverified(
    alembic_config, database_url, empty_database
):
    command.upgrade(alembic_config, "0007")
    engine = make_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO participant (first_name, last_name, email, personal_code, role,"
                " invited_by, created_at) VALUES ('Ada', 'Lovelace', 'ada@example.com',"
                " 'CSC-AAAA', 'participant', 'Bob', '2026-07-01 10:00:00')"
            )
        )
    command.upgrade(alembic_config, "0008")
    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT invited_by, plus_one_verified_at, plus_one_verified_by_id FROM participant"
            )
        ).one()
    command.downgrade(alembic_config, "0007")
    with engine.connect() as connection:
        columns = {c["name"] for c in inspect(connection).get_columns("participant")}
        invited_by = connection.execute(text("SELECT invited_by FROM participant")).scalar_one()
    engine.dispose()
    assert tuple(row) == ("Bob", None, None)
    assert "plus_one_verified_at" not in columns
    assert invited_by == "Bob"


def test_migration_0009_marks_existing_promotions_as_not_plus_one(
    alembic_config, database_url, empty_database
):
    command.upgrade(alembic_config, "0008")
    engine = make_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO edition (name, start_date, end_date, morning_start, morning_end,"
                " afternoon_start, afternoon_end, evening_start, evening_end, default_capacity,"
                " hold_days, base_fee_cents, per_day_fee_cents, is_active, waitlist_percent,"
                " lunch_price_cents, dinner_price_cents) VALUES ('Camp', '2026-07-13',"
                " '2026-07-17', '09:00:00', '13:00:00', '14:00:00', '18:00:00', '19:00:00',"
                " '00:00:00', 25, 3, 1000, 100, 1, 20, 800, 1200)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO participant (first_name, last_name, email, personal_code, role,"
                " created_at) VALUES ('Ada', 'Lovelace', 'ada@example.com', 'CSC-AAAA',"
                " 'participant', '2026-07-01 10:00:00')"
            )
        )
        edition_id = connection.execute(text("SELECT id FROM edition")).scalar_one()
        participant_id = connection.execute(text("SELECT id FROM participant")).scalar_one()
        connection.execute(
            text(
                "INSERT INTO slot (edition_id, date, period, start_time, end_time, capacity)"
                " VALUES (:e, '2026-07-13', 'morning', '09:00:00', '13:00:00', 10)"
            ),
            {"e": edition_id},
        )
        slot_id = connection.execute(text("SELECT id FROM slot")).scalar_one()
        for kind in ("privacy", "disclaimer"):
            connection.execute(
                text(
                    "INSERT INTO legal_document (edition_id, kind, version, body, published_at)"
                    " VALUES (:e, :k, 1, 'testo', '2026-07-01 09:00:00')"
                ),
                {"e": edition_id, "k": kind},
            )
        doc_id = connection.execute(text("SELECT MIN(id) FROM legal_document")).scalar_one()
        connection.execute(
            text(
                "INSERT INTO waitlist_entry (slot_id, participant_id, created_at, closed_at,"
                " close_reason, privacy_document_id, privacy_accepted_at, disclaimer_document_id,"
                " disclaimer_accepted_at) VALUES (:s, :p, '2026-07-01 10:00:00',"
                " '2026-07-02 10:00:00', 'promoted', :d, '2026-07-01 10:00:00', :d,"
                " '2026-07-01 10:00:00')"
            ),
            {"s": slot_id, "p": participant_id, "d": doc_id},
        )
    command.upgrade(alembic_config, "0009")
    with engine.connect() as connection:
        flag = connection.execute(
            text("SELECT promoted_as_plus_one FROM waitlist_entry")
        ).scalar_one()
    command.downgrade(alembic_config, "0008")
    with engine.connect() as connection:
        columns = {c["name"] for c in inspect(connection).get_columns("waitlist_entry")}
    engine.dispose()
    assert not flag
    assert "promoted_as_plus_one" not in columns


def test_external_guest_tables_upgrade_and_downgrade(alembic_config, database_url, empty_database):
    command.upgrade(alembic_config, "0023_included_meal")
    engine = make_engine(database_url)
    assert "external_guest" not in inspect(engine).get_table_names()
    command.upgrade(alembic_config, "0024_external_guests")
    tables = set(inspect(engine).get_table_names())
    assert {"external_guest", "external_guest_meal", "external_guest_activity"} <= tables
    command.downgrade(alembic_config, "0023_included_meal")
    tables = set(inspect(engine).get_table_names())
    assert not {"external_guest", "external_guest_meal", "external_guest_activity"} & tables
    engine.dispose()


def test_external_movement_table_upgrade_and_downgrade(
    alembic_config, database_url, empty_database
):
    command.upgrade(alembic_config, "0024_external_guests")
    engine = make_engine(database_url)
    assert "external_movement" not in inspect(engine).get_table_names()
    command.upgrade(alembic_config, "0025_external_movements")
    assert "external_movement" in inspect(engine).get_table_names()
    command.downgrade(alembic_config, "0024_external_guests")
    assert "external_movement" not in inspect(engine).get_table_names()
    engine.dispose()


def test_exemptions_and_refunds_upgrade_keeps_existing_bookings_ordinary(
    alembic_config, database_url, empty_database
):
    command.upgrade(alembic_config, "0025_external_movements")
    engine = make_engine(database_url)
    command.upgrade(alembic_config, "0026_exemptions_refunds")
    inspector = inspect(engine)
    assert {"category", "fee_exempt", "exemption_preview_token"} <= {
        c["name"] for c in inspector.get_columns("booking")
    }
    assert "exempt" in {c["name"] for c in inspector.get_columns("booking_meal")}
    assert "exempt" in {c["name"] for c in inspector.get_columns("booking_activity")}
    assert "booking_refund" in inspector.get_table_names()
    command.downgrade(alembic_config, "0025_external_movements")
    inspector = inspect(engine)
    assert "booking_refund" not in inspector.get_table_names()
    assert "category" not in {c["name"] for c in inspector.get_columns("booking")}
    engine.dispose()


def test_hidden_contributions_upgrade_keeps_existing_ones_visible(
    alembic_config, database_url, empty_database
):
    command.upgrade(alembic_config, "0026_exemptions_refunds")
    engine = make_engine(database_url)
    command.upgrade(alembic_config, "0027_contribution_hidden")
    columns = {c["name"] for c in inspect(engine).get_columns("contribution")}
    assert {"hidden_at", "hidden_by_id", "hidden_reason"} <= columns
    command.downgrade(alembic_config, "0026_exemptions_refunds")
    columns = {c["name"] for c in inspect(engine).get_columns("contribution")}
    assert not {"hidden_at", "hidden_by_id", "hidden_reason"} & columns
    engine.dispose()


def test_activity_source_upgrade_keeps_existing_activities_unlinked(
    alembic_config, database_url, empty_database
):
    command.upgrade(alembic_config, "0027_contribution_hidden")
    engine = make_engine(database_url)
    command.upgrade(alembic_config, "0028_activity_source")
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("activity")}
    assert {"source_contribution_id", "source_title", "request_key"} <= columns
    assert "uq_activity_request_key" in {i["name"] for i in inspector.get_indexes("activity")}
    command.downgrade(alembic_config, "0027_contribution_hidden")
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("activity")}
    assert not {"source_contribution_id", "source_title", "request_key"} & columns
    assert "uq_activity_request_key" not in {i["name"] for i in inspector.get_indexes("activity")}
    engine.dispose()


def test_benefit_delivery_upgrade_adds_an_empty_register(
    alembic_config, database_url, empty_database
):
    command.upgrade(alembic_config, "0028_activity_source")
    engine = make_engine(database_url)
    command.upgrade(alembic_config, "0029_benefit_delivery")
    inspector = inspect(engine)
    assert "benefit_delivery" in inspector.get_table_names()
    indexes = {i["name"] for i in inspector.get_indexes("benefit_delivery")}
    assert {"uq_benefit_delivery_active", "uq_benefit_delivery_request_key"} <= indexes
    command.downgrade(alembic_config, "0028_activity_source")
    assert "benefit_delivery" not in inspect(engine).get_table_names()
    engine.dispose()
