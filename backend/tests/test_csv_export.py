import csv
import io
from datetime import UTC, date, datetime

import pytest

from app.csv_export import Amount, csv_filename, csv_response, format_cell, render_csv


def parse(response) -> list[list[str]]:
    text = response.body.decode("utf-8-sig")
    return list(csv.reader(io.StringIO(text), delimiter=";"))


def test_response_is_a_download_with_the_right_type_and_name():
    response = csv_response("persone-2026-07-01.csv", ["Nome"], [["Ada"]])
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert (
        response.headers["content-disposition"] == 'attachment; filename="persone-2026-07-01.csv"'
    )


def test_file_starts_with_the_utf8_byte_order_mark_for_excel():
    assert csv_response("x.csv", ["a"], []).body.startswith(b"\xef\xbb\xbf")


def test_columns_are_separated_by_semicolons_and_rows_by_crlf():
    text = render_csv(["Nome", "Cognome"], [["Ada", "Lovelace"]])
    assert text == "﻿Nome;Cognome\r\nAda;Lovelace\r\n"


def test_a_value_containing_the_separator_or_newlines_is_quoted():
    rows = parse(csv_response("x.csv", ["Nota"], [["uno; due"], ["a\nb"], ['dice "ciao"']]))
    assert [r[0] for r in rows[1:]] == ["uno; due", "a\nb", 'dice "ciao"']


@pytest.mark.parametrize(
    ("cents", "text"),
    [
        (0, "0,00"),
        (5, "0,05"),
        (1100, "11,00"),
        (123456, "1234,56"),
        (-100, "-1,00"),
        (-5, "-0,05"),
    ],
)
def test_amounts_use_the_decimal_comma_and_keep_their_sign(cents, text):
    assert format_cell(Amount(cents)) == text


def test_times_are_written_in_rome_not_utc():
    # 22:30 UTC in July is 00:30 of the next day in Rome
    assert format_cell(datetime(2026, 7, 13, 22, 30, tzinfo=UTC)) == "14/07/2026 00:30"
    assert format_cell(datetime(2026, 1, 13, 22, 30, tzinfo=UTC)) == "13/01/2026 23:30"


def test_dates_booleans_numbers_and_empty_cells():
    assert format_cell(date(2026, 7, 3)) == "03/07/2026"
    assert (format_cell(True), format_cell(False)) == ("sì", "no")
    assert format_cell(7) == "7"
    assert format_cell(None) == ""


def test_accents_and_emoji_survive_the_round_trip():
    rows = parse(csv_response("x.csv", ["Nome"], [["Niccolò Zoë 🎉"], ["Łukasz"]]))
    assert [r[0] for r in rows[1:]] == ["Niccolò Zoë 🎉", "Łukasz"]


@pytest.mark.parametrize(
    "text", ["=SUM(A1:A9)", "+cmd|' /C calc'!A0", "-2+3+cmd", "@SUM(1)", "\t=1"]
)
def test_text_that_could_run_as_a_formula_is_neutralised(text):
    assert format_cell(text) == "'" + text


@pytest.mark.parametrize(
    "text", ["+39 333 1234567", "+39 (06) 123.4567", "0039 333 1234567", "Ada"]
)
def test_phone_numbers_and_normal_text_are_left_alone(text):
    assert format_cell(text) == text


def test_a_negative_amount_is_not_mistaken_for_a_formula():
    assert render_csv(["Saldo"], [[Amount(-100)]]).endswith("-1,00\r\n")


def test_filename_carries_the_date_in_rome():
    assert (
        csv_filename("persone", datetime(2026, 7, 13, 22, 30, tzinfo=UTC))
        == "persone-2026-07-14.csv"
    )
