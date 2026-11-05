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


def test_models_and_migrations_are_in_sync(alembic_config, database_url, empty_database):
    command.upgrade(alembic_config, "head")
    engine = make_engine(database_url)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        diff = compare_metadata(context, Base.metadata)
    engine.dispose()
    assert diff == [], f"models differ from migrations, create a migration: {diff}"


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
