"""Talks, unconference themes and skills a participant offers to the camp."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.activities import validate_contribution
from app.domain.booking import can_edit_slots, effective_status, occupies_seats
from app.models import CONTRIBUTION_KINDS, ROLE_ADMIN, Booking, Contribution, Participant
from app.services import audit
from app.services import consents as consent_service
from app.services import edition as edition_service
from app.services.booking_changes import NotEditable, get_current_booking
from app.services.seats import expire_overdue


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


class ProposalsNotAllowed(Exception):
    """Only people with an active booking in the current edition, and admins, can read them."""


@dataclass(frozen=True)
class Proposal:
    id: int
    kind: str
    title: str
    description: str | None
    # None when the author has no valid attendance consent: the proposal stays, anonymous.
    author_name: str | None


def proposals_for(
    db: Session, viewer: Participant, now: datetime, kind: str | None = None
) -> list[Proposal]:
    """What the other participants offer or look for (MVP 27).

    Only bookings that occupy seats count; the viewer's own contributions and those an admin hid
    are left out. A name appears only for an author whose attendance consent is valid right now,
    so a revoked consent takes effect on the next read.
    """
    edition = edition_service.get_active_edition(db)
    if edition is None:
        raise ProposalsNotAllowed()
    expire_overdue(db, now)
    db.commit()
    if viewer.role != ROLE_ADMIN:
        own = get_current_booking(db, viewer)
        if own is None or not occupies_seats(
            effective_status(own.status, own.hold_expires_at, now)
        ):
            raise ProposalsNotAllowed()
    shown: list[tuple[Booking, Contribution]] = []
    bookings = db.scalars(
        select(Booking)
        .where(Booking.edition_id == edition.id)
        .options(selectinload(Booking.contributions), selectinload(Booking.participant))
    )
    for booking in bookings:
        if booking.participant_id == viewer.id:
            continue
        if not occupies_seats(effective_status(booking.status, booking.hold_expires_at, now)):
            continue
        shown.extend(
            (booking, c)
            for c in booking.contributions
            if c.hidden_at is None and (kind is None or c.kind == kind)
        )
    named = consent_service.attendance_authorized(
        db, edition, {booking.participant_id for booking, _ in shown}
    )
    shown.sort(
        key=lambda item: (CONTRIBUTION_KINDS.index(item[1].kind), item[1].created_at, item[1].id)
    )
    return [
        Proposal(
            id=c.id,
            kind=c.kind,
            title=c.title,
            description=c.description,
            author_name=(
                f"{b.participant.first_name} {b.participant.last_name}".strip()
                if b.participant_id in named
                else None
            ),
        )
        for b, c in shown
    ]


def set_hidden(
    db: Session,
    admin: Participant,
    contribution_id: int,
    hidden: bool,
    reason: str | None,
    now: datetime,
) -> bool:
    """Hide a proposal from the other participants, or show it again. Idempotent.

    The proposal is not deleted or changed: its author still sees it. Returns whether something
    changed, so a repeated request leaves no second trace in the history.
    """
    contribution = db.get(Contribution, contribution_id)
    if contribution is None:
        raise ContributionNotFound()
    if (contribution.hidden_at is not None) == hidden:
        return False
    if hidden:
        contribution.hidden_at = now
        contribution.hidden_by_id = admin.id
        contribution.hidden_reason = (reason or "").strip() or None
        note = f" Motivo: {contribution.hidden_reason}." if contribution.hidden_reason else ""
        text = f"Proposta nascosta agli altri partecipanti: «{contribution.title}».{note}"
        action = "contribution_hidden"
    else:
        contribution.hidden_at = None
        contribution.hidden_by_id = None
        contribution.hidden_reason = None
        text = f"Proposta di nuovo visibile agli altri partecipanti: «{contribution.title}»."
        action = "contribution_shown"
    audit.log(db, admin, action, text, contribution.booking_id)
    db.commit()
    return True
