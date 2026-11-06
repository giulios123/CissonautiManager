from datetime import date

import pytest

from app.domain.email_template import (
    DEFAULT_BODY,
    DEFAULT_CARD_TEXT,
    DEFAULT_SUBJECT,
    PLACEHOLDERS,
    is_valid_color,
    render,
    unknown_placeholders,
)
from app.timefmt import format_long_date


class TestPlaceholders:
    def test_known_names_are_accepted(self):
        text = " ".join(f"{{{name}}}" for name in PLACEHOLDERS)
        assert unknown_placeholders(text) == []

    def test_unknown_names_are_reported_once_in_order(self):
        assert unknown_placeholders("{nome} {first_name} {nome} {data inizio}") == [
            "nome",
            "data inizio",
        ]

    def test_text_without_braces_is_fine(self):
        assert unknown_placeholders("Ciao a tutti!") == []

    def test_a_lone_brace_is_just_text(self):
        assert unknown_placeholders("Un { aperta") == []
        assert render("Un { aperta {first_name}", {"first_name": "Ada"}) == "Un { aperta Ada"

    def test_render_replaces_every_occurrence_and_leaves_unknown(self):
        values = {"first_name": "Ada", "event": "Camp"}
        assert render("{first_name}, {first_name} a {event} {x}", values) == "Ada, Ada a Camp {x}"

    def test_values_are_not_interpreted_again(self):
        assert render("{first_name}", {"first_name": "{event}", "event": "X"}) == "{event}"


@pytest.mark.parametrize("locale", ["it", "en"])
def test_default_texts_use_only_known_placeholders(locale):
    for text in (DEFAULT_CARD_TEXT[locale], DEFAULT_SUBJECT[locale], DEFAULT_BODY[locale]):
        assert unknown_placeholders(text) == []


def test_the_default_card_text_matches_the_wording_asked_for():
    values = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "event": "Camp 2027",
        "start_date": "10 July 2027",
        "end_date": "16 July 2027",
    }
    assert render(DEFAULT_CARD_TEXT["en"], values) == (
        "I'm Ada Lovelace and I'll be at Camp 2027 from 10 July 2027 to 16 July 2027"
    )
    assert render(DEFAULT_CARD_TEXT["it"], values).startswith("Sono Ada Lovelace e sarò a Camp")


@pytest.mark.parametrize(
    ("value", "ok"),
    [
        ("#ffffff", True),
        ("#A0b1C2", True),
        ("ffffff", False),
        ("#fff", False),
        ("#gggggg", False),
        ("", False),
    ],
)
def test_colors(value, ok):
    assert is_valid_color(value) is ok


def test_long_dates():
    assert format_long_date(date(2027, 7, 10), "it") == "10 luglio 2027"
    assert format_long_date(date(2027, 7, 10), "en") == "10 July 2027"
    assert format_long_date(date(2027, 1, 1), "en") == "1 January 2027"
