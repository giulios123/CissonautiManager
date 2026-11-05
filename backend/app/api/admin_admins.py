from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import get_db
from app.deps import get_settings_dep, require_admin
from app.domain import admins as admin_rules
from app.models import Participant
from app.services import admins as admins_service

router = APIRouter(prefix="/api/admin/admins", tags=["admin"])

REMOVAL_MESSAGES = {
    admin_rules.SELF: "Non puoi rimuovere te stesso: chiedi a un altro admin.",
    admin_rules.SEED: (
        "Questo admin è quello iniziale, definito dalla variabile ADMIN_EMAIL: "
        "per cambiarlo si modifica la configurazione."
    ),
    admin_rules.LAST: "Deve restare almeno un admin.",
}


class AdminOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    is_you: bool
    removable: bool
    # Why it cannot be removed, in words for the person using the panel.
    blocked_reason: str | None = None


class AddAdminIn(BaseModel):
    email: EmailStr
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)


class AddAdminOut(AdminOut):
    created: bool


def _out(db: Session, person: Participant, actor: Participant, settings: Settings) -> AdminOut:
    check = admins_service.removal_check(db, person, actor, settings.admin_email)
    return AdminOut(
        id=person.id,
        first_name=person.first_name,
        last_name=person.last_name,
        email=person.email,
        is_you=person.id == actor.id,
        removable=check.allowed,
        blocked_reason=REMOVAL_MESSAGES.get(check.reason) if check.reason else None,
    )


@router.get("")
def list_admins(
    actor: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
) -> list[AdminOut]:
    return [_out(db, p, actor, settings) for p in admins_service.list_admins(db)]


@router.post("", status_code=201)
def add_admin(
    body: AddAdminIn,
    actor: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
) -> AddAdminOut:
    try:
        person, created = admins_service.add_admin(
            db, actor, body.email, body.first_name, body.last_name
        )
    except admins_service.AlreadyAdmin as exc:
        raise HTTPException(status_code=409, detail="Questa persona è già admin.") from exc
    except admins_service.NameRequired as exc:
        raise HTTPException(
            status_code=422,
            detail="Questa email non è ancora registrata: scrivi anche nome e cognome.",
        ) from exc
    return AddAdminOut(**_out(db, person, actor, settings).model_dump(), created=created)


@router.delete("/{admin_id}", status_code=204)
def remove_admin(
    admin_id: int,
    actor: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
) -> None:
    try:
        admins_service.remove_admin(db, actor, admin_id, settings.admin_email)
    except admins_service.NotAnAdmin as exc:
        raise HTTPException(status_code=404, detail="Admin non trovato.") from exc
    except admins_service.RemovalRefused as exc:
        raise HTTPException(
            status_code=409,
            detail=REMOVAL_MESSAGES.get(exc.reason or "", "Non si può rimuovere questo admin."),
        ) from exc
