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
