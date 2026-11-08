"""Sends the payment reminders that are due. Run hourly: `python -m app.jobs.send_reminders`.

It also hands the seats freed by expired holds to the first people on the waitlists: expiry is
evaluated on read, so nothing else would notice it and send the email.

The web app scales to zero, so a separate scheduled job wakes up, sends what is due and exits.
Each reminder is marked as sent with a conditional UPDATE before the email goes out, so a
rerun (or two overlapping runs) never sends the same reminder twice. The price of that is that
a failed delivery is not retried; the error is in the logs.
"""

import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import make_engine, make_session_factory, utcnow
from app.domain.reminders import due_reminder
from app.email import EmailSender, build_email_sender
from app.email.templates import privacy_renewal_email, reminder_email
from app.models import (
    DOC_PRIVACY,
    STATUS_PENDING,
    Booking,
    Edition,
    Participant,
    PaymentChannel,
)
from app.services import edition as edition_service
from app.services import email_templates as email_templates_service
from app.services import privacy as privacy_service
from app.services import registration as registration_service
from app.services import waitlist as waitlist_service
from app.services.amounts import confirmation_due
from app.services.payments import paid_total, send_due_confirmations
from app.services.seats import expire_overdue, lock_booking, lock_edition

logger = logging.getLogger("app.jobs.send_reminders")


@dataclass
class ReminderSummary:
    examined: int = 0
    mid: int = 0
    final: int = 0
    promoted: int = 0
    confirmations: int = 0
    privacy_notices: int = 0


def _claim(db: Session, booking: Booking, kind: str, now: datetime) -> bool:
    """Mark the reminder as sent. False if another run got there first, or if the booking changed
    since it was evaluated (paid, cancelled, hold extended or amount changed): the decision to send
    was taken on the old state, so it no longer holds."""
    column = Booking.reminder_final_sent_at if kind == "final" else Booking.reminder_mid_sent_at
    result = db.execute(
        update(Booking)
        .where(
            Booking.id == booking.id,
            column.is_(None),
            Booking.status == STATUS_PENDING,
            Booking.hold_started_at == booking.hold_started_at,
            Booking.hold_expires_at == booking.hold_expires_at,
            Booking.amount_due_cents == booking.amount_due_cents,
            Booking.registration_fee_cents == booking.registration_fee_cents,
        )
        .values({column.key: now})
    )
    db.commit()
    return result.rowcount == 1


def send_due_reminders(
    db: Session, sender: EmailSender, settings: Settings, now: datetime
) -> ReminderSummary:
    expire_overdue(db, now)
    db.commit()
    summary = ReminderSummary()
    channels: dict[int, list[PaymentChannel]] = {}
    login_url = f"{settings.app_base_url.rstrip('/')}/login"

    pending_ids = db.scalars(
        select(Booking.id)
        .where(Booking.status == STATUS_PENDING, Booking.hold_expires_at > now)
        .order_by(Booking.id)
    ).all()
    for booking_id in pending_ids:
        booking = db.get(Booking, booking_id)
        if booking is None:
            continue
        if booking.status != STATUS_PENDING or booking.hold_expires_at <= now:
            continue
        summary.examined += 1
        evaluated_state = (
            booking.status,
            booking.hold_started_at,
            booking.hold_expires_at,
            booking.amount_due_cents,
            booking.registration_fee_cents,
        )
        initial_paid = paid_total(booking)
        initial_due = confirmation_due(booking.edition, booking)
        if initial_due is None or initial_paid >= initial_due:
            continue
        kind = due_reminder(
            booking.hold_started_at,
            booking.hold_expires_at,
            booking.reminder_mid_sent_at,
            booking.reminder_final_sent_at,
            now,
        )
        if kind is None:
            continue
        lock_edition(db, booking.edition_id)
        lock_booking(db, booking_id)
        db.refresh(booking)
        edition = db.get(Edition, booking.edition_id)
        if edition is None:
            db.rollback()
            continue
        db.refresh(edition)
        paid = paid_total(booking)
        due = confirmation_due(edition, booking)
        if (
            booking.status != STATUS_PENDING
            or (
                booking.status,
                booking.hold_started_at,
                booking.hold_expires_at,
                booking.amount_due_cents,
                booking.registration_fee_cents,
            )
            != evaluated_state
            or booking.hold_expires_at <= now
            or due is None
            or due != initial_due
            or paid >= due
        ):
            db.rollback()
            continue
        if not _claim(db, booking, kind, now):
            continue
        if booking.edition_id not in channels:
            edition = db.get(Edition, booking.edition_id)
            assert edition is not None
            channels[booking.edition_id] = registration_service.enabled_channels(db, edition)
        sender.send(
            reminder_email(
                booking,
                kind,
                channels[booking.edition_id],
                due - paid,
                login_url,
                email_templates_service.texts_for_booking(
                    db, booking, "reminder_final" if kind == "final" else "reminder_mid"
                ),
            )
        )
        if kind == "final":
            summary.final += 1
        else:
            summary.mid += 1
    summary.promoted = promote_open_slots(db, sender, settings, now)
    summary.privacy_notices = send_due_privacy_notices(db, sender, settings, now)
    # Safety net for the confirmation emails whose timer was lost (restart, scale to zero).
    summary.confirmations = send_due_confirmations(db, sender, now, settings)
    return summary


def send_due_privacy_notices(
    db: Session, sender: EmailSender, settings: Settings, now: datetime
) -> int:
    """Notify each active participant once about the current privacy version."""
    edition = edition_service.get_active_edition(db)
    if edition is None:
        return 0
    document = edition_service.latest_legal_document(db, edition, DOC_PRIVACY)
    if document is None:
        return 0

    count = 0
    login_root = f"{settings.app_base_url.rstrip('/')}/login"
    for participant_id in privacy_service.active_recipient_ids(db, edition, now):
        try:
            lock_edition(db, edition.id)
            db.refresh(edition)
            current = edition_service.latest_legal_document(db, edition, DOC_PRIVACY)
            participant = db.get(Participant, participant_id)
            if (
                current is None
                or current.id != document.id
                or participant is None
                or not privacy_service.is_active_recipient(db, edition, participant, now)
            ):
                db.rollback()
                continue
            if not privacy_service.claim_notice_attempt(db, edition, participant, current, now):
                db.rollback()
                continue
            db.commit()
        except IntegrityError:
            db.rollback()
            continue

        locale = participant.locale if participant.locale in ("it", "en") else "it"
        link = f"{login_root}?lang={locale}"
        try:
            sender.send(
                privacy_renewal_email(
                    participant,
                    event_name=edition.name,
                    version=document.version,
                    link=link,
                    locale=locale,
                )
            )
        except Exception:
            logger.exception(
                "Privacy renewal email attempt failed participant_id=%d document_id=%d",
                participant.id,
                document.id,
            )
        count += 1
    return count


def promote_open_slots(db: Session, sender: EmailSender, settings: Settings, now: datetime) -> int:
    """Give the seats freed by expired holds to the people waiting. Returns how many."""
    edition = edition_service.get_active_edition(db)
    if edition is None:
        return 0
    slot_ids = waitlist_service.slots_with_waiting_people(db, edition)
    return len(waitlist_service.promote_freed(db, sender, settings, slot_ids, now))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = get_settings()
    engine = make_engine(settings.database_url)
    sender = build_email_sender(settings)
    with make_session_factory(engine)() as db:
        summary = send_due_reminders(db, sender, settings, utcnow())
    engine.dispose()
    logger.info(
        "Reminders: examined=%d mid=%d final=%d; waitlist promotions=%d; confirmations=%d; "
        "privacy=%d",
        summary.examined,
        summary.mid,
        summary.final,
        summary.promoted,
        summary.confirmations,
        summary.privacy_notices,
    )


if __name__ == "__main__":
    main()
