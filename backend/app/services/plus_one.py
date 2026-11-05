"""The +1 of a participant: an admin confirms who invited them, and the waitlist puts them first.

The verification sits on the person, not on a booking, because someone who is only on a waitlist
has no booking. Every change is recorded in the audit log (D-022), on the person's latest booking
when there is one so that it shows in that booking's history.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.waitlist import can_verify_plus_one
from app.models import Booking, Participant
from app.services import audit


class NothingToVerify(Exception):
    """The person did not say who invited them."""


def _latest_booking_id(db: Session, participant: Participant) -> int | None:
    return db.scalar(
        select(Booking.id)
        .where(Booking.participant_id == participant.id)
        .order_by(Booking.id.desc())
        .limit(1)
    )


def _who(participant: Participant) -> str:
    return f"{participant.first_name} {participant.last_name} ({participant.email})"


def is_verified(participant: Participant) -> bool:
    return participant.plus_one_verified_at is not None


def set_verified(
    db: Session, admin: Participant, participant: Participant, verified: bool, now: datetime
) -> None:
    """Verify or unverify. Doing what is already done changes nothing and logs nothing."""
    if verified == is_verified(participant):
        return
    if verified:
        if not can_verify_plus_one(participant.invited_by):
            raise NothingToVerify()
        participant.plus_one_verified_at = now
        participant.plus_one_verified_by_id = admin.id
        audit.log(
            db,
            admin,
            "plus_one_verified",
            f"+1 verificato: {_who(participant)}, invitato da '{participant.invited_by}'.",
            _latest_booking_id(db, participant),
        )
    else:
        participant.plus_one_verified_at = None
        participant.plus_one_verified_by_id = None
        audit.log(
            db,
            admin,
            "plus_one_removed",
            f"Verifica del +1 tolta: {_who(participant)}.",
            _latest_booking_id(db, participant),
        )
    db.commit()


def drop_if_uninvited(db: Session, admin: Participant, participant: Participant) -> None:
    """Without anyone who invited them there is no +1: the verification falls. The caller
    commits."""
    if not is_verified(participant) or can_verify_plus_one(participant.invited_by):
        return
    participant.plus_one_verified_at = None
    participant.plus_one_verified_by_id = None
    audit.log(
        db,
        admin,
        "plus_one_removed",
        f"Verifica del +1 caduta: «invitato da» è stato svuotato ({_who(participant)}).",
        _latest_booking_id(db, participant),
    )


def verified_by_name(db: Session, participant: Participant) -> str | None:
    if participant.plus_one_verified_by_id is None:
        return None
    admin = db.get(Participant, participant.plus_one_verified_by_id)
    return f"{admin.first_name} {admin.last_name}" if admin else None
