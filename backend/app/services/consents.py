"""Read and write optional consent evidence for the active edition."""

from collections import defaultdict
from collections.abc import Collection
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain import consents as consent_domain
from app.domain.consents import ConsentState
from app.models import (
    DOC_ATTENDANCE,
    OPTIONAL_CONSENT_KINDS,
    Booking,
    ConsentEvent,
    Edition,
    LegalDocument,
    Participant,
    Slot,
    WaitlistEntry,
)
from app.services import edition as edition_service


class InvalidConsentKind(Exception):
    pass


class ConsentDocumentUnavailable(Exception):
    pass


class ConsentConflict(Exception):
    pass


def _current_documents(db: Session, edition: Edition) -> dict[str, LegalDocument | None]:
    return {
        kind: edition_service.latest_legal_document(db, edition, kind)
        for kind in OPTIONAL_CONSENT_KINDS
    }


def _events_for(db: Session, edition: Edition, participant: Participant) -> list[ConsentEvent]:
    return list(
        db.scalars(
            select(ConsentEvent)
            .where(
                ConsentEvent.edition_id == edition.id,
                ConsentEvent.participant_id == participant.id,
            )
            .order_by(ConsentEvent.id)
        )
    )


def get_states(db: Session, edition: Edition, participant: Participant) -> list[ConsentState]:
    """Return one state per optional purpose, including unexpressed legacy choices."""
    return consent_domain.build_states(
        _events_for(db, edition, participant), _current_documents(db, edition)
    )


def attendance_authorized(
    db: Session, edition: Edition, participant_ids: Collection[int]
) -> set[int]:
    """The people whose attendance consent is granted for the current document, in one query.

    Used to show a name to other participants: anything but a valid grant (declined, withdrawn,
    never expressed, or granted on an older document) leaves the person out.
    """
    current = edition_service.latest_legal_document(db, edition, DOC_ATTENDANCE)
    if current is None or not participant_ids:
        return set()
    by_person: dict[int, list[ConsentEvent]] = defaultdict(list)
    for event in db.scalars(
        select(ConsentEvent).where(
            ConsentEvent.edition_id == edition.id,
            ConsentEvent.kind == DOC_ATTENDANCE,
            ConsentEvent.participant_id.in_(participant_ids),
        )
    ):
        by_person[event.participant_id].append(event)
    authorized: set[int] = set()
    for person_id, events in by_person.items():
        latest = consent_domain.latest_by_kind(events).get(DOC_ATTENDANCE)
        state = ConsentState(DOC_ATTENDANCE, latest.action, latest, current) if latest else None
        if state is not None and state.is_authorized_for_current_document:
            authorized.add(person_id)
    return authorized


def has_edition_association(db: Session, edition: Edition, participant: Participant) -> bool:
    """A booking, waitlist entry, or consent proof links the person to the edition."""
    queries = (
        select(Booking.id).where(
            Booking.edition_id == edition.id, Booking.participant_id == participant.id
        ),
        select(WaitlistEntry.id)
        .join(WaitlistEntry.slot)
        .where(
            WaitlistEntry.participant_id == participant.id,
            Slot.edition_id == edition.id,
        ),
        select(ConsentEvent.id).where(
            ConsentEvent.edition_id == edition.id, ConsentEvent.participant_id == participant.id
        ),
    )
    return any(db.scalar(query.limit(1)) is not None for query in queries)


def _document_snapshot(document: LegalDocument | None) -> dict | None:
    if document is None:
        return None
    return {
        "id": document.id,
        "version": document.version,
        "body": document.body,
        "body_it": document.body_it,
        "body_en": document.body_en,
        "is_legacy": document.body_it is None or document.body_en is None,
    }


def collection_snapshot(db: Session, edition: Edition, participant: Participant) -> dict:
    """Serialize personal status plus append-only evidence for both optional purposes."""
    events = _events_for(db, edition, participant)
    current_documents = _current_documents(db, edition)
    states = consent_domain.build_states(events, current_documents)
    by_kind: dict[str, list[ConsentEvent]] = {kind: [] for kind in OPTIONAL_CONSENT_KINDS}
    for event in events:
        if event.kind in by_kind:
            by_kind[event.kind].append(event)
    return {
        "edition_id": edition.id,
        "associated": has_edition_association(db, edition, participant),
        "consents": [
            {
                "kind": state.kind,
                "action": state.action,
                "event_id": state.event_id,
                "authorized_for_current_document": state.is_authorized_for_current_document,
                "needs_renewal": state.needs_renewal,
                "current_document": _document_snapshot(state.current_document),
                "events": [
                    {
                        "id": event.id,
                        "action": event.action,
                        "locale": event.locale,
                        "recorded_at": event.recorded_at,
                        "source": event.source,
                        "document": _document_snapshot(event.document),
                    }
                    for event in by_kind[state.kind]
                ],
            }
            for state in states
        ],
    }


def _latest_event(
    db: Session, edition: Edition, participant: Participant, kind: str
) -> ConsentEvent | None:
    return db.scalar(
        select(ConsentEvent)
        .where(
            ConsentEvent.edition_id == edition.id,
            ConsentEvent.participant_id == participant.id,
            ConsentEvent.kind == kind,
        )
        .order_by(ConsentEvent.id.desc())
        .limit(1)
    )


def record_choice(
    db: Session,
    edition: Edition,
    participant: Participant,
    *,
    kind: str,
    granted: bool,
    document_id: int | None,
    version: int | None,
    locale: str,
    expected_event_id: int | None,
    source: str,
    now: datetime,
) -> ConsentEvent | None:
    """Append one version-checked choice without committing the caller's transaction.

    HTTP write handlers already take the edition lock in `get_db`; the expected event id then
    detects stale forms even when two callers started from the same read.
    """
    if kind not in OPTIONAL_CONSENT_KINDS:
        raise InvalidConsentKind()
    if locale not in ("it", "en") or source not in ("public_registration", "self_service"):
        raise ConsentDocumentUnavailable()

    event = _latest_event(db, edition, participant, kind)
    actual_event_id = event.id if event is not None else None

    # Revoking an existing grant must remain possible after a new, incomplete legal
    # document is published. The event points back to the grant's document.
    if not granted and event is not None and event.action == "granted":
        if actual_event_id != expected_event_id:
            raise ConsentConflict()
        created = ConsentEvent(
            edition_id=edition.id,
            participant_id=participant.id,
            kind=kind,
            action="withdrawn",
            document_id=event.document_id,
            locale=locale,
            recorded_at=now,
            source=source,
        )
        db.add(created)
        db.flush()
        return created

    if event is not None and event.action == "withdrawn" and not granted:
        return None

    current = _current_documents(db, edition)[kind]
    submitted = db.get(LegalDocument, document_id) if document_id is not None else None
    if (
        submitted is None
        or submitted.edition_id != edition.id
        or submitted.kind != kind
        or not submitted.body_it
        or not submitted.body_it.strip()
        or not submitted.body_en
        or not submitted.body_en.strip()
    ):
        raise ConsentDocumentUnavailable()
    if current is None or not (current.body_it and current.body_en):
        raise ConsentDocumentUnavailable()
    if version is None or submitted.version != version:
        raise ConsentDocumentUnavailable()
    if (current.id, current.version) != (submitted.id, submitted.version):
        raise ConsentConflict()

    unchanged = consent_domain.choice_is_unchanged(
        event, granted=granted, current_document_id=current.id
    )
    if actual_event_id != expected_event_id and not unchanged:
        raise ConsentConflict()
    if unchanged:
        return None

    action, evidence_document_id = consent_domain.action_for_choice(
        event, granted=granted, current_document_id=current.id
    )
    created = ConsentEvent(
        edition_id=edition.id,
        participant_id=participant.id,
        kind=kind,
        action=action,
        document_id=evidence_document_id,
        locale=locale,
        recorded_at=now,
        source=source,
    )
    db.add(created)
    db.flush()
    return created
