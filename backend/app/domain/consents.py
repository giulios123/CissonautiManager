"""Pure rules for optional, versioned consent choices."""

from collections.abc import Iterable
from dataclasses import dataclass

from app.models import OPTIONAL_CONSENT_KINDS, ConsentEvent, LegalDocument

NOT_EXPRESSED = "not_expressed"
GRANTED = "granted"
DECLINED = "declined"
WITHDRAWN = "withdrawn"
CONSENT_ACTIONS = (GRANTED, DECLINED, WITHDRAWN)


@dataclass(frozen=True)
class ConsentState:
    kind: str
    action: str
    event: ConsentEvent | None
    current_document: LegalDocument | None

    @property
    def event_id(self) -> int | None:
        return self.event.id if self.event is not None else None

    @property
    def is_authorized_for_current_document(self) -> bool:
        return bool(
            self.event is not None
            and self.event.action == GRANTED
            and self.current_document is not None
            and self.event.document_id == self.current_document.id
        )

    @property
    def needs_renewal(self) -> bool:
        return bool(
            self.event is not None
            and self.event.action == GRANTED
            and self.current_document is not None
            and self.event.document_id != self.current_document.id
        )


def latest_by_kind(events: Iterable[ConsentEvent]) -> dict[str, ConsentEvent]:
    """Return the last event for each supported purpose, ordered by its generated id."""
    latest: dict[str, ConsentEvent] = {}
    for event in events:
        if event.kind in OPTIONAL_CONSENT_KINDS and event.action in CONSENT_ACTIONS:
            previous = latest.get(event.kind)
            if previous is None or event.id > previous.id:
                latest[event.kind] = event
    return latest


def build_states(
    events: Iterable[ConsentEvent], documents: dict[str, LegalDocument | None]
) -> list[ConsentState]:
    latest = latest_by_kind(events)
    return [
        ConsentState(
            kind=kind,
            action=latest[kind].action if kind in latest else NOT_EXPRESSED,
            event=latest.get(kind),
            current_document=documents.get(kind),
        )
        for kind in OPTIONAL_CONSENT_KINDS
    ]


def choice_is_unchanged(
    event: ConsentEvent | None, *, granted: bool, current_document_id: int
) -> bool:
    """An identical submission does not create a second proof event."""
    if event is None:
        return False
    if granted:
        return event.action == GRANTED and event.document_id == current_document_id
    if event.action == WITHDRAWN:
        return True
    return event.action == DECLINED and event.document_id == current_document_id


def action_for_choice(
    event: ConsentEvent | None, *, granted: bool, current_document_id: int
) -> tuple[str, int]:
    """Map a checkbox state to evidence while preserving the document being withdrawn."""
    if granted:
        return GRANTED, current_document_id
    if event is not None and event.action == GRANTED:
        return WITHDRAWN, event.document_id
    return DECLINED, current_document_id
