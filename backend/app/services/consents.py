"""Read and write optional consent evidence for the active edition."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain import consents as consent_domain
from app.domain.consents import ConsentState
from app.models import (
    OPTIONAL_CONSENT_KINDS,
    ConsentEvent,
    Edition,
    LegalDocument,
    Participant,
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
    document_id: int,
    version: int,
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

    current = _current_documents(db, edition)[kind]
    submitted = db.get(LegalDocument, document_id)
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
    if submitted.version != version:
        raise ConsentDocumentUnavailable()
    if (current.id, current.version) != (submitted.id, submitted.version):
        raise ConsentConflict()

    event = _latest_event(db, edition, participant, kind)
    unchanged = consent_domain.choice_is_unchanged(
        event, granted=granted, current_document_id=current.id
    )
    actual_event_id = event.id if event is not None else None
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
