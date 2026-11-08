import os
from datetime import UTC, date, datetime, time, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.config import Settings
from app.db import Base, make_engine
from app.email import EmailMessage, EmailSender
from app.main import create_app
from app.models import (
    DOC_PRIVACY,
    ROLE_ADMIN,
    ROLE_PARTICIPANT,
    STATUS_PENDING,
    Booking,
    ConsentEvent,
    Participant,
    Slot,
)
from app.services import edition as edition_service
from app.services.passwords import hash_password


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


def reset_database(engine: Engine) -> None:
    """Empty the database. The SQL Server test database is shared between tests, so the Alembic
    version table must go too, or a later migration test would think it is already migrated."""
    Base.metadata.drop_all(engine)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))


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
    reset_database(engine)
    Base.metadata.create_all(engine)
    yield engine
    reset_database(engine)
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
    # Deferred work is collected instead of started on a timer: tests run it when they choose.
    application.state.scheduled = []
    application.state.run_later = lambda delay, task: application.state.scheduled.append(
        (delay, task)
    )
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


DEFAULT_EDITION_VALUES = dict(
    name="Cissonauti Summer Camp 2026",
    start_date=date(2026, 7, 13),
    end_date=date(2026, 7, 17),
    morning_start=time(9, 0),
    morning_end=time(13, 0),
    afternoon_start=time(14, 0),
    afternoon_end=time(18, 0),
    default_capacity=25,
    hold_days=3,
    base_fee_cents=1000,
    per_day_fee_cents=100,
)


@pytest.fixture
def edition(db):
    """Active edition 13-17 July 2026 with default settings and published legal texts."""
    created = edition_service.save_edition(db, dict(DEFAULT_EDITION_VALUES))
    edition_service.publish_legal_document(
        db, created, "privacy", "Informativa privacy v1", "Privacy notice v1"
    )
    edition_service.publish_legal_document(
        db, created, "disclaimer", "Scarico di responsabilità v1", "Liability waiver v1"
    )
    return created


@pytest.fixture
def make_booking(db, edition, clock):
    """Create a booking directly in the database, bypassing the API."""

    def _make(
        participant, slots, status=STATUS_PENDING, hold_expires_at=None, amount_due_cents=None
    ):
        privacy = edition_service.latest_legal_document(db, edition, "privacy")
        disclaimer = edition_service.latest_legal_document(db, edition, "disclaimer")
        booking = Booking(
            edition_id=edition.id,
            participant_id=participant.id,
            status=status,
            hold_expires_at=hold_expires_at or clock() + timedelta(days=3),
            hold_started_at=clock(),
            amount_due_cents=amount_due_cents if amount_due_cents is not None else 1100,
            privacy_document_id=privacy.id,
            privacy_accepted_at=clock(),
            disclaimer_document_id=disclaimer.id,
            disclaimer_accepted_at=clock(),
            created_at=clock(),
        )
        booking.slots = list(slots)
        db.add(booking)
        db.commit()
        db.add(
            ConsentEvent(
                edition_id=edition.id,
                participant_id=participant.id,
                kind=DOC_PRIVACY,
                action="accepted",
                document_id=privacy.id,
                locale="it",
                recorded_at=clock(),
                source="self_service",
            )
        )
        db.commit()
        return booking

    return _make


@pytest.fixture
def admin_client(app, make_participant) -> TestClient:
    make_participant(
        "boss@example.com", role=ROLE_ADMIN, password_hash=hash_password("admin-password-1")
    )
    client = TestClient(app, base_url="https://testserver")
    response = client.post(
        "/api/auth/login", json={"email": "boss@example.com", "password": "admin-password-1"}
    )
    assert response.status_code == 200
    return client


@pytest.fixture
def slot_ids(db, edition):
    """Slot ids keyed by (date, period) for the 13-17 July edition."""
    return {(s.date, s.period): s.id for s in db.scalars(select(Slot))}


@pytest.fixture
def fill_slot(db, make_participant, make_booking):
    """Shrink a slot to `capacity` seats and fill them with bookings of other people.

    With the default 10 seats, the 20% waitlist has 2 places."""
    counter = iter(range(1, 1000))

    def _fill(slot, capacity=10, status=STATUS_PENDING) -> list[Booking]:
        slot.capacity = capacity
        db.commit()
        bookings = []
        for _ in range(capacity):
            n = next(counter)
            other = make_participant(f"filler{n}@example.com", first_name=f"Filler{n}")
            bookings.append(make_booking(other, [slot], status=status))
        return bookings

    return _fill


@pytest.fixture
def add_entry(db, edition):
    """Put someone on a slot's waitlist directly in the database."""
    from app.models import WaitlistEntry

    def _add(slot, participant, at) -> "WaitlistEntry":
        privacy = edition_service.latest_legal_document(db, edition, "privacy")
        disclaimer = edition_service.latest_legal_document(db, edition, "disclaimer")
        entry = WaitlistEntry(
            slot_id=slot.id,
            participant_id=participant.id,
            created_at=at,
            privacy_document_id=privacy.id,
            privacy_accepted_at=at,
            disclaimer_document_id=disclaimer.id,
            disclaimer_accepted_at=at,
        )
        db.add(entry)
        db.commit()
        db.add(
            ConsentEvent(
                edition_id=edition.id,
                participant_id=participant.id,
                kind=DOC_PRIVACY,
                action="accepted",
                document_id=privacy.id,
                locale="it",
                recorded_at=at,
                source="self_service",
            )
        )
        db.commit()
        return entry

    return _add
