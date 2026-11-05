from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, Participant


def log(
    db: Session, actor: Participant, action: str, detail: str, booking_id: int | None = None
) -> None:
    """Record something an admin did by hand. The caller commits together with the change."""
    db.add(AuditLog(actor_id=actor.id, booking_id=booking_id, action=action, detail=detail))


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
