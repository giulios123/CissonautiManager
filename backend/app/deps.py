from datetime import datetime

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import get_db
from app.email import EmailSender
from app.models import ROLE_ADMIN, Participant
from app.services import auth as auth_service

SESSION_COOKIE = "csc_session"


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def get_now(request: Request) -> datetime:
    return request.app.state.clock()


def get_email_sender(request: Request) -> EmailSender:
    return request.app.state.email_sender


def current_user(
    request: Request, db: Session = Depends(get_db), now: datetime = Depends(get_now)
) -> Participant:
    raw = request.cookies.get(SESSION_COOKIE)
    participant = auth_service.get_session_participant(db, raw, now) if raw else None
    if participant is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return participant


def require_admin(user: Participant = Depends(current_user)) -> Participant:
    if user.role != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Admin only")
    return user


def require_privacy_acceptance(
    user: Participant = Depends(current_user), db: Session = Depends(get_db)
) -> None:
    """Block participant-side edits until the current edition's privacy is accepted."""
    from app.i18n import t
    from app.services import edition as edition_service
    from app.services import privacy as privacy_service

    edition = edition_service.get_active_edition(db)
    if privacy_service.acceptance_required(db, edition, user):
        raise HTTPException(
            status_code=428,
            detail={
                "code": "privacy_acceptance_required",
                "message": t("privacy.acceptance_required"),
            },
        )
