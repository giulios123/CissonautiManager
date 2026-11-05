"""Talks, unconference themes and skills a participant offers to the camp."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.activities import validate_contribution
from app.domain.booking import can_edit_slots, effective_status
from app.models import Booking, Contribution, Participant
from app.services.booking_changes import NotEditable


class ContributionNotFound(Exception):
    pass


class InvalidContribution(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _validate(kind: str, title: str) -> None:
    check = validate_contribution(kind, title)
    if not check.ok:
        assert check.reason is not None
        raise InvalidContribution(check.reason)


def add(
    db: Session, booking: Booking, kind: str, title: str, description: str | None, now: datetime
) -> Contribution:
    if not can_edit_slots(effective_status(booking.status, booking.hold_expires_at, now)):
        raise NotEditable()
    _validate(kind, title)
    contribution = Contribution(
        booking_id=booking.id,
        kind=kind,
        title=title.strip(),
        description=(description or "").strip() or None,
        created_at=now,
        updated_at=now,
    )
    db.add(contribution)
    db.commit()
    return contribution


def _own(db: Session, participant: Participant, contribution_id: int) -> Contribution:
    contribution = db.get(Contribution, contribution_id)
    if contribution is None:
        raise ContributionNotFound()
    booking = db.get(Booking, contribution.booking_id)
    if booking is None or booking.participant_id != participant.id:
        raise ContributionNotFound()
    return contribution


def update(
    db: Session,
    participant: Participant,
    contribution_id: int,
    kind: str,
    title: str,
    description: str | None,
    now: datetime,
) -> Contribution:
    contribution = _own(db, participant, contribution_id)
    _validate(kind, title)
    contribution.kind = kind
    contribution.title = title.strip()
    contribution.description = (description or "").strip() or None
    contribution.updated_at = now
    db.commit()
    return contribution


def remove(db: Session, participant: Participant, contribution_id: int) -> None:
    db.delete(_own(db, participant, contribution_id))
    db.commit()
