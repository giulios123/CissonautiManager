from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import get_db
from app.deps import (
    SESSION_COOKIE,
    get_email_sender,
    get_now,
    get_settings_dep,
)
from app.email import EmailSender
from app.models import ROLE_ADMIN, Participant
from app.services import auth as auth_service
from app.services.participants import get_by_email
from app.services.passwords import verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

MAGIC_LINK_REQUESTED = "Se l'email è registrata riceverai un link per entrare."


class MagicLinkRequest(BaseModel):
    email: EmailStr


class VerifyRequest(BaseModel):
    token: str


class PasswordLogin(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class LoginResult(BaseModel):
    role: str
    redirect: str


def set_session_cookie(response: Response, settings: Settings, raw_session: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        raw_session,
        max_age=int(auth_service.SESSION_TTL.total_seconds()),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def login_result(participant: Participant) -> LoginResult:
    is_admin = participant.role == ROLE_ADMIN
    return LoginResult(role=participant.role, redirect="/admin" if is_admin else "/me")


@router.post("/magic-link")
def request_magic_link(
    body: MagicLinkRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    sender: EmailSender = Depends(get_email_sender),
    now: datetime = Depends(get_now),
) -> dict[str, str]:
    participant = get_by_email(db, body.email)
    if participant is not None:
        auth_service.send_magic_link(db, sender, settings, participant, now)
    # Same answer whether or not the email exists: do not reveal who is registered.
    return {"message": MAGIC_LINK_REQUESTED}


@router.post("/verify")
def verify_magic_link(
    body: VerifyRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    now: datetime = Depends(get_now),
) -> LoginResult:
    participant = auth_service.consume_magic_link(db, body.token, now)
    if participant is None:
        raise HTTPException(status_code=400, detail="Link non valido o scaduto")
    set_session_cookie(response, settings, auth_service.create_session(db, participant, now))
    return login_result(participant)


@router.post("/login")
def login_with_password(
    body: PasswordLogin,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    now: datetime = Depends(get_now),
) -> LoginResult:
    participant = get_by_email(db, body.email)
    stored_hash = participant.password_hash if participant else None
    # One generic error for unknown email, no password set and wrong password.
    if participant is None or not verify_password(stored_hash, body.password):
        raise HTTPException(status_code=401, detail="Email o password non corretti")
    set_session_cookie(response, settings, auth_service.create_session(db, participant, now))
    return login_result(participant)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> None:
    raw = request.cookies.get(SESSION_COOKIE)
    if raw:
        auth_service.delete_session(db, raw)
    response.delete_cookie(SESSION_COOKIE, path="/")
