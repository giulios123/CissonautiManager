from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.codes import generate_personal_code
from app.models import ROLE_ADMIN, Participant


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_by_email(db: Session, email: str) -> Participant | None:
    return db.scalar(select(Participant).where(Participant.email == normalize_email(email)))


def new_unique_personal_code(db: Session) -> str:
    for _ in range(20):
        code = generate_personal_code()
        if db.scalar(select(Participant.id).where(Participant.personal_code == code)) is None:
            return code
    raise RuntimeError("Could not generate a unique personal code")


def ensure_admin(db: Session, email: str) -> Participant:
    """Create the participant with this email as admin, or promote the existing one."""
    participant = get_by_email(db, email)
    if participant is None:
        participant = Participant(
            first_name="Admin",
            last_name="",
            email=normalize_email(email),
            personal_code=new_unique_personal_code(db),
            role=ROLE_ADMIN,
        )
        db.add(participant)
    else:
        participant.role = ROLE_ADMIN
    db.commit()
    return participant
