"""Manual changes an admin makes to a registration. Each one is recorded in the audit log."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.booking import can_extend_hold
from app.domain.fees import is_covered
from app.domain.reminders import reminders_to_keep_after_extension
from app.email import EmailSender
from app.models import STATUS_CONFIRMED, STATUS_EXPIRED, STATUS_PENDING, Booking, Participant
from app.services import audit
from app.services.participants import get_by_email, normalize_email
from app.services.payments import paid_total, revive_expired, send_confirmation
from app.services.registration import SlotsFull
from app.services.seats import expire_overdue, free_by_slot
from app.timefmt import format_deadline

PERSON_FIELDS = {
    "first_name": "nome",
    "last_name": "cognome",
    "email": "email",
    "phone": "telefono",
    "invited_by": "invitato da",
    "can_bring": "cosa porta",
}


class EmailTaken(Exception):
    pass


class NotExtendable(Exception):
    pass


class InvalidDeadline(Exception):
    pass


class NotExpired(Exception):
    pass


def _shown(value: str | None) -> str:
    if not value:
        return "vuoto"
    return f"'{value[:60]}…'" if len(value) > 60 else f"'{value}'"


def update_details(
    db: Session,
    admin: Participant,
    booking: Booking,
    changes: dict[str, str | None],
    new_expires: datetime | None,
    now: datetime,
) -> None:
    """Edit the person's details and/or extend the hold, all or nothing.

    `changes` holds only the fields to set; None clears an optional one. Extending the hold moves
    the reminder thresholds, so reminders that are due again are cleared and will go out again.
    """
    expire_overdue(db, now)
    db.refresh(booking)
    if new_expires is not None:
        if not can_extend_hold(booking.status):
            raise NotExtendable()
        if new_expires <= booking.hold_expires_at or new_expires <= now:
            raise InvalidDeadline()

    participant = booking.participant
    if "email" in changes and changes["email"] is not None:
        changes["email"] = normalize_email(changes["email"])
        taken = get_by_email(db, changes["email"])
        if taken is not None and taken.id != participant.id:
            raise EmailTaken()

    differences = []
    for field, value in changes.items():
        old = getattr(participant, field)
        if old != value:
            differences.append(f"{PERSON_FIELDS[field]}: {_shown(old)} → {_shown(value)}")
            setattr(participant, field, value)
    if differences:
        audit.log(
            db, admin, "details_changed", "Dati modificati. " + "; ".join(differences), booking.id
        )

    if new_expires is not None:
        old_deadline = booking.hold_expires_at
        booking.hold_expires_at = new_expires
        booking.reminder_mid_sent_at, booking.reminder_final_sent_at = (
            reminders_to_keep_after_extension(
                booking.hold_started_at,
                new_expires,
                booking.reminder_mid_sent_at,
                booking.reminder_final_sent_at,
                now,
            )
        )
        audit.log(
            db,
            admin,
            "hold_extended",
            f"Scadenza del blocco prorogata: {format_deadline(old_deadline)} → "
            f"{format_deadline(new_expires)}",
            booking.id,
        )
    db.commit()


def reactivate(
    db: Session, sender: EmailSender, admin: Participant, booking: Booking, now: datetime
) -> bool:
    """Bring an expired booking back for a new hold. Returns True if it was confirmed at once.

    Raises SlotsFull, changing nothing, if a slot has no seat left. A booking whose payments
    already cover the amount (possible after a correction) is confirmed straight away.
    """
    expire_overdue(db, now)
    db.refresh(booking)
    if booking.status != STATUS_EXPIRED:
        raise NotExpired()
    if not revive_expired(db, booking, now):
        free = free_by_slot(db, booking.slots, now)
        raise SlotsFull([s for s in booking.slots if free[s.id] is not None and free[s.id] < 1])
    total = paid_total(booking)
    confirmed = booking.status == STATUS_PENDING and is_covered(booking.amount_due_cents, total)
    if confirmed:
        booking.status = STATUS_CONFIRMED
    if confirmed:
        detail = "Prenotazione riattivata e confermata: i pagamenti coprono già la quota"
    else:
        until = format_deadline(booking.hold_expires_at)
        detail = f"Prenotazione riattivata: nuovo blocco fino al {until}"
    audit.log(db, admin, "reactivated", detail, booking.id)
    db.commit()
    if confirmed:
        send_confirmation(sender, booking, total)
    return confirmed
