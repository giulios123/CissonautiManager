import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine

import app.models  # noqa: F401
from app.config import Settings
from app.db import Base, make_engine
from app.main import create_app


@pytest.fixture
def database_url(tmp_path) -> str:
    """SQLite by default; set TEST_DATABASE_URL to run the suite on SQL Server."""
    return os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def settings(tmp_path, database_url) -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        database_url=database_url,
        static_dir=str(tmp_path / "static"),
        secret_key="test-secret",
    )


@pytest.fixture
def engine(database_url) -> Engine:
    engine = make_engine(database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(settings: Settings, engine: Engine) -> TestClient:
    return TestClient(create_app(settings))
