"""Versioned mandatory privacy acceptance and its one-time notification."""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.domain.consents import PRIVACY_ACCEPTED, privacy_acceptance_is_current
from app.models import (
    DOC_PRIVACY,
    STATUS_CONFIRMED,
    STATUS_PENDING,
    Booking,
    ConsentEvent,
    Edition,
    LegalDocument,
    Participant,
    PrivacyNoticeAttempt,
    Slot,
    WaitlistEntry,
)
from app.services import consents as consent_service
from app.services import edition as edition_service
from app.services.seats import lock_edition


class PrivacyDocumentConflict(Exception):
    """The submitted privacy version is no longer current."""


def latest_acceptance(
    db: Session, edition: Edition, participant: Participant
) -> ConsentEvent | None:
    return db.scalar(
        select(ConsentEvent)
        .join(LegalDocument, LegalDocument.id == ConsentEvent.document_id)
        .where(
            ConsentEvent.edition_id == edition.id,
            ConsentEvent.participant_id == participant.id,
            ConsentEvent.kind == DOC_PRIVACY,
            ConsentEvent.action == PRIVACY_ACCEPTED,
        )
        .order_by(
            LegalDocument.version.desc(),
            ConsentEvent.recorded_at.desc(),
            ConsentEvent.id.desc(),
        )
        .limit(1)
    )


def acceptance_history(
    db: Session, edition: Edition, participant: Participant
) -> list[ConsentEvent]:
    return list(
        db.scalars(
            select(ConsentEvent)
            .options(joinedload(ConsentEvent.document))
            .where(
                ConsentEvent.edition_id == edition.id,
                ConsentEvent.participant_id == participant.id,
                ConsentEvent.kind == DOC_PRIVACY,
                ConsentEvent.action == PRIVACY_ACCEPTED,
            )
            .order_by(ConsentEvent.recorded_at, ConsentEvent.id)
        )
    )


def is_currently_accepted(db: Session, edition: Edition, participant: Participant) -> bool:
    current = edition_service.latest_legal_document(db, edition, DOC_PRIVACY)
    accepted_ids = db.scalars(
        select(ConsentEvent.document_id).where(
            ConsentEvent.edition_id == edition.id,
            ConsentEvent.participant_id == participant.id,
            ConsentEvent.kind == DOC_PRIVACY,
            ConsentEvent.action == PRIVACY_ACCEPTED,
        )
    )
    return privacy_acceptance_is_current(accepted_ids, current)


def acceptance_required(db: Session, edition: Edition | None, participant: Participant) -> bool:
    if edition is None or not consent_service.has_edition_association(db, edition, participant):
        return False
    return not is_currently_accepted(db, edition, participant)


def accept_current(
    db: Session,
    edition: Edition,
    participant: Participant,
    *,
    document_id: int,
    version: int,
    locale: str,
    now: datetime,
    allow_legacy: bool = False,
    source: str = "self_service",
) -> ConsentEvent:
    if locale not in ("it", "en"):
        raise PrivacyDocumentConflict()
    lock_edition(db, edition.id)
    db.refresh(edition)
    current = edition_service.latest_legal_document(db, edition, DOC_PRIVACY)
    submitted = db.get(LegalDocument, document_id)
    if (
        current is None
        or submitted is None
        or submitted.id != current.id
        or submitted.version != version
        or submitted.edition_id != edition.id
        or submitted.kind != DOC_PRIVACY
        or (
            not allow_legacy
            and (
                not submitted.body_it
                or not submitted.body_it.strip()
                or not submitted.body_en
                or not submitted.body_en.strip()
            )
        )
    ):
        raise PrivacyDocumentConflict()
    existing = db.scalar(
        select(ConsentEvent).where(
            ConsentEvent.edition_id == edition.id,
            ConsentEvent.participant_id == participant.id,
            ConsentEvent.kind == DOC_PRIVACY,
            ConsentEvent.action == PRIVACY_ACCEPTED,
            ConsentEvent.document_id == current.id,
        )
    )
    if existing is not None:
        return existing
    event = ConsentEvent(
        edition_id=edition.id,
        participant_id=participant.id,
        kind=DOC_PRIVACY,
        action=PRIVACY_ACCEPTED,
        document_id=current.id,
        locale=locale,
        recorded_at=now,
        source=source,
    )
    db.add(event)
    db.flush()
    return event


def active_recipient_ids(db: Session, edition: Edition, now: datetime) -> list[int]:
    """Current pending/confirmed bookings and people on an open waitlist for this edition."""
    booking_ids = select(Booking.participant_id).where(
        Booking.edition_id == edition.id,
        (Booking.status == STATUS_CONFIRMED)
        | ((Booking.status == STATUS_PENDING) & (Booking.hold_expires_at > now)),
    )
    today = now.astimezone(ZoneInfo("Europe/Rome")).date()
    waitlist_ids = (
        select(WaitlistEntry.participant_id)
        .join(Slot, Slot.id == WaitlistEntry.slot_id)
        .where(
            Slot.edition_id == edition.id,
            WaitlistEntry.closed_at.is_(None),
            Slot.date >= today,
        )
    )
    return sorted(set(db.scalars(booking_ids).all()) | set(db.scalars(waitlist_ids).all()))


def claim_notice_attempt(
    db: Session,
    edition: Edition,
    participant: Participant,
    document: LegalDocument,
    now: datetime,
) -> bool:
    """Claim one email attempt; uniqueness makes concurrent job runs at-most-once."""
    if not acceptance_required(db, edition, participant):
        return False
    prior = db.scalar(
        select(PrivacyNoticeAttempt.id).where(
            PrivacyNoticeAttempt.edition_id == edition.id,
            PrivacyNoticeAttempt.participant_id == participant.id,
            PrivacyNoticeAttempt.document_id == document.id,
        )
    )
    if prior is not None:
        return False
    db.add(
        PrivacyNoticeAttempt(
            edition_id=edition.id,
            participant_id=participant.id,
            document_id=document.id,
            attempted_at=now,
        )
    )
    db.flush()
    return True
