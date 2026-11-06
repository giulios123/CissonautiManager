from app.domain.email_texts import (
    DEFAULT_EVENT_NAME,
    KINDS,
    SUBJECT_MAX,
    TEXT_MAX,
    EmailParts,
    compose,
    fill,
    resolve,
    validate,
)


def test_every_kind_has_default_texts_with_the_event_in_the_subject():
    for kind, info in KINDS.items():
        assert info.label and info.automatic, kind
        assert info.defaults.intro.startswith("Ciao {nome}"), kind
    assert all("{evento}" in info.defaults.subject for info in KINDS.values())


def test_resolve_uses_defaults_for_missing_or_blank_fields():
    parts = resolve("registration", {"subject": "  ", "intro": None, "closing": "A presto"})
    defaults = KINDS["registration"].defaults
    assert parts.subject == defaults.subject
    assert parts.intro == defaults.intro
    assert parts.closing == "A presto"
    assert resolve("registration", None) == defaults


def test_fill_replaces_only_the_two_placeholders():
    text = "Ciao {nome}, benvenuto a {evento} {altro} {0}"
    assert fill(text, "Ada", "Camp") == "Ciao Ada, benvenuto a Camp {altro} {0}"


def test_fill_does_not_expand_placeholders_found_in_the_name():
    assert fill("{nome} {evento}", "{evento}", "X") == "{evento} X"


def test_compose_keeps_the_automatic_block_between_opening_and_closing():
    parts = EmailParts("Oggetto {evento}", "Ciao {nome},", "Ciao ciao")
    subject, body = compose(parts, "Ada", "Camp", "Quota: 10,00 €\nCausale: CSC-1\n")
    assert subject == "Oggetto Camp"
    assert body == "Ciao Ada,\n\nQuota: 10,00 €\nCausale: CSC-1\n\nCiao ciao\n"


def test_compose_skips_an_empty_closing_and_flattens_the_subject():
    parts = EmailParts("Uno\ndue", "Ciao", "")
    subject, body = compose(parts, "Ada", "Camp", "Dati")
    assert subject == "Uno due"
    assert body == "Ciao\n\nDati\n"


def test_validate_limits():
    assert validate("a" * SUBJECT_MAX, "b" * TEXT_MAX, None) is None
    assert validate("a" * (SUBJECT_MAX + 1), None, None)
    assert validate(None, "b" * (TEXT_MAX + 1), None)
    assert validate(None, None, "b" * (TEXT_MAX + 1))


def test_default_event_name():
    assert DEFAULT_EVENT_NAME == "Cissonauti Summer Camp"
