import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import Settings
from app.email import EmailMessage, EmailSender
from app.models import AuthSession, MagicLinkToken, Participant

MAGIC_LINK_TTL = timedelta(minutes=30)
SESSION_TTL = timedelta(days=14)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def create_magic_link_token(db: Session, participant: Participant, now: datetime) -> str:
    raw = secrets.token_urlsafe(32)
    db.add(
        MagicLinkToken(
            participant_id=participant.id,
            token_hash=hash_token(raw),
            expires_at=now + MAGIC_LINK_TTL,
        )
    )
    db.commit()
    return raw


def magic_link_url(settings: Settings, raw_token: str) -> str:
    return f"{settings.app_base_url.rstrip('/')}/accedi/verifica?token={raw_token}"


def send_magic_link(
    db: Session,
    sender: EmailSender,
    settings: Settings,
    participant: Participant,
    now: datetime,
) -> None:
    raw = create_magic_link_token(db, participant, now)
    sender.send(
        EmailMessage(
            to=participant.email,
            subject="Il tuo link di accesso ai Cisonauti",
            body=(
                f"Ciao {participant.first_name},\n\n"
                f"apri questo link per entrare: {magic_link_url(settings, raw)}\n\n"
                "Il link vale 30 minuti e si può usare una sola volta."
            ),
        )
    )


def consume_magic_link(db: Session, raw_token: str, now: datetime) -> Participant | None:
    """Validate and burn a magic link token. Returns the participant, or None if not valid."""
    token_hash = hash_token(raw_token)
    token = db.scalar(select(MagicLinkToken).where(MagicLinkToken.token_hash == token_hash))
    if token is None or token.used_at is not None or token.expires_at <= now:
        return None
    # Atomic "use once": only one concurrent request can flip used_at from NULL.
    result = db.execute(
        update(MagicLinkToken)
        .where(MagicLinkToken.id == token.id, MagicLinkToken.used_at.is_(None))
        .values(used_at=now)
    )
    db.commit()
    if result.rowcount != 1:
        return None
    return db.get(Participant, token.participant_id)


def create_session(db: Session, participant: Participant, now: datetime) -> str:
    raw = secrets.token_urlsafe(32)
    db.add(
        AuthSession(
            participant_id=participant.id, token_hash=hash_token(raw), expires_at=now + SESSION_TTL
        )
    )
    db.commit()
    return raw


def get_session_participant(db: Session, raw_token: str, now: datetime) -> Participant | None:
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(raw_token)))
    if session is None or session.expires_at <= now:
        return None
    return db.get(Participant, session.participant_id)


def delete_session(db: Session, raw_token: str) -> None:
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(raw_token)))
    if session is not None:
        db.delete(session)
        db.commit()
