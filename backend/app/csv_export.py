"""CSV downloads that open correctly in Excel with an Italian locale.

Semicolon separator, UTF-8 with a byte order mark (so accents survive), decimal commas and
dates and times in Europe/Rome. Text cells that a spreadsheet could read as a formula are
neutralised.
"""

import csv
import io
import re
from collections.abc import Iterable, Sequence
from datetime import date, datetime
from typing import NamedTuple

from fastapi.responses import Response

from app.timefmt import format_amount, to_rome

BOM = "﻿"
_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")
# Phone numbers and plain figures start with + or - but cannot run anything: keep them as typed.
_PLAIN_NUMBER = re.compile(r"^\+?[\d\s().-]+$")


class Amount(NamedTuple):
    """An amount in cents, written as 12,50 (negative values keep their sign)."""

    cents: int


Cell = str | int | bool | date | datetime | Amount | None


def _safe_text(text: str) -> str:
    if text.startswith(_FORMULA_START) and not _PLAIN_NUMBER.match(text):
        return "'" + text
    return text


def format_cell(value: Cell) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):  # before int: bool is an int
        return "sì" if value else "no"
    if isinstance(value, Amount):
        return format_amount(value.cents)
    if isinstance(value, datetime):
        return to_rome(value).strftime("%d/%m/%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, int):
        return str(value)
    return _safe_text(value)


def render_csv(header: Sequence[str], rows: Iterable[Sequence[Cell]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow([format_cell(cell) for cell in row])
    return BOM + buffer.getvalue()


def csv_filename(prefix: str, now: datetime) -> str:
    return f"{prefix}-{to_rome(now).strftime('%Y-%m-%d')}.csv"


def csv_response(filename: str, header: Sequence[str], rows: Iterable[Sequence[Cell]]) -> Response:
    return Response(
        content=render_csv(header, rows).encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
