from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, Participant


def log(
    db: Session, actor: Participant, action: str, detail: str, booking_id: int | None = None
) -> None:
    """Record something an admin did by hand. The caller commits together with the change."""
    db.add(AuditLog(actor_id=actor.id, booking_id=booking_id, action=action, detail=detail))


def cancellation(
    db: Session,
    *,
    participant_id: int,
    edition_id: int,
    actor_id: int | None,
    booking_id: int | None,
    outcome: str,
    at,
    detail: str,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor_id,
        participant_id=participant_id,
        edition_id=edition_id,
        booking_id=booking_id,
        action="cancelled_by_admin" if actor_id is not None else "cancelled_by_participant",
        outcome=outcome,
        at=at,
        detail=detail,
    )
    db.add(entry)
    return entry


def history(db: Session, booking_id: int) -> list[tuple[AuditLog, Participant]]:
    """Entries for a booking, newest first, each with the admin who made the change."""
    return list(
        db.execute(
            select(AuditLog, Participant)
            .join(Participant, Participant.id == AuditLog.actor_id)
            .where(AuditLog.booking_id == booking_id)
            .order_by(AuditLog.at.desc(), AuditLog.id.desc())
        ).all()
    )
