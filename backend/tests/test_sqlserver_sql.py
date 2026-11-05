"""The SQL generated for SQL Server, checked without a server (the CI runs the real thing)."""

from sqlalchemy import select, true
from sqlalchemy.dialects import mssql

from app.models import Edition
from app.services.edition import get_active_edition  # noqa: F401
from app.services.seats import lock_booking, slots_for_update


def compiled(statement) -> str:
    return str(statement.compile(dialect=mssql.dialect(), compile_kwargs={"literal_binds": True}))


def test_slot_lock_uses_an_explicit_hint_on_sql_server():
    sql = compiled(slots_for_update([1, 2], edition_id=1))
    assert "WITH (UPDLOCK, HOLDLOCK)" in sql


def test_boolean_filter_is_valid_on_sql_server():
    sql = compiled(select(Edition).where(Edition.is_active == true()))
    assert "IS 1" not in sql
    assert "is_active = 1" in sql


def test_booking_lock_uses_an_explicit_hint_on_sql_server():
    from unittest.mock import MagicMock

    session = MagicMock()
    lock_booking(session, 7)
    statement = session.execute.call_args.args[0]
    sql = compiled(statement)
    assert "WITH (UPDLOCK, HOLDLOCK)" in sql
    assert "booking.id = 7" in sql
