from types import SimpleNamespace

from app.domain.consents import (
    DECLINED,
    GRANTED,
    NOT_EXPRESSED,
    WITHDRAWN,
    action_for_choice,
    build_states,
    choice_is_unchanged,
)


def event(event_id, kind, action, document_id):
    return SimpleNamespace(id=event_id, kind=kind, action=action, document_id=document_id)


def document(document_id, kind):
    return SimpleNamespace(id=document_id, kind=kind)


def test_each_purpose_has_an_independent_unexpressed_or_declined_state():
    states = build_states(
        [event(1, "media", DECLINED, 20)],
        {"attendance": document(10, "attendance"), "media": document(20, "media")},
    )

    assert [(state.kind, state.action) for state in states] == [
        ("attendance", NOT_EXPRESSED),
        ("media", DECLINED),
    ]


def test_grant_only_authorizes_the_current_document_version():
    old_grant = event(4, "attendance", GRANTED, 10)
    state = build_states(
        [old_grant],
        {"attendance": document(11, "attendance"), "media": None},
    )[0]

    assert not state.is_authorized_for_current_document
    assert state.needs_renewal


def test_revocation_references_the_previous_grant_and_repeat_is_noop():
    previous = event(7, "attendance", GRANTED, 10)

    assert action_for_choice(previous, granted=False, current_document_id=11) == (WITHDRAWN, 10)
    assert choice_is_unchanged(previous, granted=True, current_document_id=10)
    withdrawn = event(8, "attendance", WITHDRAWN, 10)
    assert choice_is_unchanged(withdrawn, granted=False, current_document_id=11)


def test_decline_is_tied_to_the_current_text_and_grant_to_current_document():
    assert action_for_choice(None, granted=False, current_document_id=11) == (DECLINED, 11)
    assert action_for_choice(None, granted=True, current_document_id=11) == (GRANTED, 11)
    old_decline = event(3, "media", DECLINED, 10)
    assert not choice_is_unchanged(old_decline, granted=False, current_document_id=11)
