from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.admins import RemoveCheck, can_remove_admin
from app.models import ROLE_ADMIN, ROLE_PARTICIPANT, Participant
from app.services import audit
from app.services.participants import get_by_email, new_unique_personal_code, normalize_email


class AlreadyAdmin(Exception):
    pass


class NameRequired(Exception):
    """A person who is not registered yet needs a name to be created."""


class NotAnAdmin(Exception):
    pass


class RemovalRefused(Exception):
    def __init__(self, reason: str | None) -> None:
        self.reason = reason
        super().__init__(reason)


def list_admins(db: Session) -> list[Participant]:
    return list(
        db.scalars(
            select(Participant)
            .where(Participant.role == ROLE_ADMIN)
            .order_by(func.lower(Participant.last_name), func.lower(Participant.first_name))
        )
    )


def removal_check(
    db: Session, target: Participant, actor: Participant, seed_email: str | None
) -> RemoveCheck:
    count = db.scalar(
        select(func.count()).select_from(Participant).where(Participant.role == ROLE_ADMIN)
    )
    return can_remove_admin(target.id, actor.id, count or 0, target.email, seed_email)


def add_admin(
    db: Session,
    actor: Participant,
    email: str,
    first_name: str | None,
    last_name: str | None,
) -> tuple[Participant, bool]:
    """Make someone an admin: promote a registered person, or create a new one with a name.

    Returns the person and whether they were newly created. They sign in with a magic link.
    """
    person = get_by_email(db, email)
    created = person is None
    if person is None:
        if not (first_name and first_name.strip() and last_name and last_name.strip()):
            raise NameRequired()
        person = Participant(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            email=normalize_email(email),
            personal_code=new_unique_personal_code(db),
            role=ROLE_ADMIN,
        )
        db.add(person)
    elif person.role == ROLE_ADMIN:
        raise AlreadyAdmin()
    else:
        person.role = ROLE_ADMIN
    db.flush()
    audit.log(
        db,
        actor,
        "admin_added",
        f"Aggiunto admin: {person.first_name} {person.last_name} ({person.email})"
        + (" (persona nuova)" if created else ""),
    )
    db.commit()
    return person, created


def remove_admin(
    db: Session, actor: Participant, target_id: int, seed_email: str | None
) -> Participant:
    """Take the admin role away. The person, and any booking they have, stay as they are."""
    target = db.get(Participant, target_id)
    if target is None or target.role != ROLE_ADMIN:
        raise NotAnAdmin()
    check = removal_check(db, target, actor, seed_email)
    if not check.allowed:
        raise RemovalRefused(check.reason)
    target.role = ROLE_PARTICIPANT
    audit.log(
        db,
        actor,
        "admin_removed",
        f"Rimosso admin: {target.first_name} {target.last_name} ({target.email})",
    )
    db.commit()
    return target
