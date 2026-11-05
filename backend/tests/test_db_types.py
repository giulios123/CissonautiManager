from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Participant


def test_datetimes_roundtrip_as_utc(engine):
    rome = timezone(timedelta(hours=2))
    with Session(engine) as session:
        participant = Participant(
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            personal_code="CSC-AAAA",
            created_at=datetime(2026, 7, 1, 12, 0, tzinfo=rome),
        )
        session.add(participant)
        session.commit()
        session.refresh(participant)
        assert participant.created_at == datetime(2026, 7, 1, 10, 0, tzinfo=UTC)
        assert participant.created_at.tzinfo is not None


def test_naive_datetimes_are_rejected(engine):
    with Session(engine) as session:
        session.add(
            Participant(
                first_name="Ada",
                last_name="Lovelace",
                email="ada@example.com",
                personal_code="CSC-AAAA",
                created_at=datetime(2026, 7, 1, 12, 0),
            )
        )
        with pytest.raises(Exception, match="naive datetime"):
            session.commit()


def test_names_outside_latin1_survive_a_roundtrip(engine):
    """Text columns are Unicode: on SQL Server a plain VARCHAR would turn these into '?'."""
    name = "Łukasz 🌍 Ñandú"
    with Session(engine) as session:
        session.add(
            Participant(
                first_name=name,
                last_name="Żółć",
                email="lukasz@example.com",
                personal_code="CSC-LUKA",
            )
        )
        session.commit()
    with Session(engine) as session:
        stored = session.scalar(select(Participant))
        assert (stored.first_name, stored.last_name) == (name, "Żółć")
