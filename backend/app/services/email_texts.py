"""Load the editable texts of the emails for an edition."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import utcnow
from app.domain import email_texts as domain
from app.domain.email_texts import DEFAULT_EVENT_NAME, EmailTexts
from app.models import Edition, EmailText, Participant
from app.services.edition import get_active_edition


def stored_texts(db: Session, edition: Edition) -> dict[str, EmailText]:
    rows = db.scalars(select(EmailText).where(EmailText.edition_id == edition.id))
    return {row.kind: row for row in rows}


def load_texts(db: Session, kind: str, edition: Edition | None = None) -> EmailTexts:
    """Texts for one kind of email. Without an edition, the active one; without any, defaults."""
    edition = edition or get_active_edition(db)
    if edition is None:
        return domain.default_texts(kind)
    row = db.scalar(
        select(EmailText).where(EmailText.edition_id == edition.id, EmailText.kind == kind)
    )
    stored = {"subject": row.subject, "intro": row.intro, "closing": row.closing} if row else None
    return EmailTexts(edition.name or DEFAULT_EVENT_NAME, domain.resolve(kind, stored))


def save_texts(
    db: Session,
    edition: Edition,
    kind: str,
    subject: str | None,
    intro: str | None,
    closing: str | None,
    actor: Participant,
    now: datetime | None = None,
) -> EmailText:
    """Store the three fields; blank ones become null (default). The caller commits."""
    row = db.scalar(
        select(EmailText).where(EmailText.edition_id == edition.id, EmailText.kind == kind)
    )
    if row is None:
        row = EmailText(edition_id=edition.id, kind=kind)
        db.add(row)
    row.subject = (subject or "").strip() or None
    row.intro = (intro or "").strip() or None
    row.closing = (closing or "").strip() or None
    row.updated_at = now or utcnow()
    row.updated_by_id = actor.id
    return row
