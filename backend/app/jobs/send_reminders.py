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
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import make_engine, make_session_factory, utcnow
from app.domain.fees import is_covered
from app.domain.reminders import due_reminder
from app.email import EmailSender, build_email_sender
from app.email.templates import reminder_email
from app.models import STATUS_PENDING, Booking, Edition, PaymentChannel
from app.services import edition as edition_service
from app.services import registration as registration_service
from app.services import waitlist as waitlist_service
from app.services.payments import paid_total, send_due_confirmations
from app.services.seats import expire_overdue

logger = logging.getLogger("app.jobs.send_reminders")


@dataclass
class ReminderSummary:
    examined: int = 0
    mid: int = 0
    final: int = 0
    promoted: int = 0
    confirmations: int = 0


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

    pending = db.scalars(
        select(Booking)
        .where(Booking.status == STATUS_PENDING, Booking.hold_expires_at > now)
        .order_by(Booking.id)
    ).all()
    for booking in pending:
        summary.examined += 1
        paid = paid_total(booking)
        if is_covered(booking.amount_due_cents, paid):
            continue
        kind = due_reminder(
            booking.hold_started_at,
            booking.hold_expires_at,
            booking.reminder_mid_sent_at,
            booking.reminder_final_sent_at,
            now,
        )
        if kind is None or not _claim(db, booking, kind, now):
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
                booking.amount_due_cents - paid,
                login_url,
            )
        )
        if kind == "final":
            summary.final += 1
        else:
            summary.mid += 1
    summary.promoted = promote_open_slots(db, sender, settings, now)
    # Safety net for the confirmation emails whose timer was lost (restart, scale to zero).
    summary.confirmations = send_due_confirmations(db, sender, now)
    return summary


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
        "Reminders: examined=%d mid=%d final=%d; waitlist promotions=%d; confirmations=%d",
        summary.examined,
        summary.mid,
        summary.final,
        summary.promoted,
        summary.confirmations,
    )


if __name__ == "__main__":
    main()
