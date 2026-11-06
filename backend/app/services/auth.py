import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import Settings
from app.email import EmailSender
from app.email.templates import magic_link_email
from app.models import AuthSession, MagicLinkToken, Participant
from app.services import edition as edition_service
from app.services import email_templates as email_templates_service

# Reusable until it expires, so mail scanners that open the link first do not burn it.
MAGIC_LINK_TTL = timedelta(minutes=10)
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
    return f"{settings.app_base_url.rstrip('/')}/login/verify?token={raw_token}"


def send_magic_link(
    db: Session,
    sender: EmailSender,
    settings: Settings,
    participant: Participant,
    now: datetime,
) -> None:
    raw = create_magic_link_token(db, participant, now)
    texts = email_templates_service.texts_for(
        db, edition_service.get_active_edition(db), participant, "magic_link"
    )
    sender.send(magic_link_email(participant, magic_link_url(settings, raw), texts))


def consume_magic_link(db: Session, raw_token: str, now: datetime) -> Participant | None:
    """Validate a magic link token. Returns the participant, or None if not valid or expired.

    The link works as many times as needed until it expires; `used_at` keeps the first use.
    """
    token_hash = hash_token(raw_token)
    token = db.scalar(select(MagicLinkToken).where(MagicLinkToken.token_hash == token_hash))
    if token is None or token.expires_at <= now:
        return None
    if token.used_at is None:
        # Conditional update: concurrent first uses record a single timestamp.
        db.execute(
            update(MagicLinkToken)
            .where(MagicLinkToken.id == token.id, MagicLinkToken.used_at.is_(None))
            .values(used_at=now)
        )
        db.commit()
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
