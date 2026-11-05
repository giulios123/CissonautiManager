import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect

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
