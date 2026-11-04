import os
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.config import Settings
from app.db import Base, make_engine
from app.email import EmailMessage, EmailSender
from app.main import create_app
from app.models import ROLE_PARTICIPANT, Participant


class OutboxEmailSender(EmailSender):
    """Collects sent emails so tests can inspect them."""

    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> None:
        self.sent.append(message)


class FakeClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 7, 1, 10, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.current

    def advance(self, **kwargs) -> None:
        self.current += timedelta(**kwargs)


@pytest.fixture
def database_url(tmp_path) -> str:
    """SQLite by default; set TEST_DATABASE_URL to run the suite on SQL Server."""
    return os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def settings(tmp_path, database_url) -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        app_base_url="https://camp.example.org",
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
def outbox() -> OutboxEmailSender:
    return OutboxEmailSender()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def app(settings, engine, outbox, clock) -> FastAPI:
    application = create_app(settings)
    application.state.email_sender = outbox
    application.state.clock = clock
    return application


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app, base_url="https://testserver")


@pytest.fixture
def db(engine) -> Session:
    with Session(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
def make_participant(db):
    counter = iter(range(1, 1000))

    def _make(email="ada@example.com", role=ROLE_PARTICIPANT, **extra) -> Participant:
        n = next(counter)
        participant = Participant(
            first_name=extra.pop("first_name", "Ada"),
            last_name=extra.pop("last_name", "Lovelace"),
            email=email,
            personal_code=extra.pop("personal_code", f"CSC-{n:04d}"),
            role=role,
            **extra,
        )
        db.add(participant)
        db.commit()
        return participant

    return _make
