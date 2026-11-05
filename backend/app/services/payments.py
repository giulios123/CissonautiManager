from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domain.booking import can_reactivate, has_free_seat, hold_deadline, status_after_void
from app.domain.fees import is_covered
from app.email import EmailSender
from app.email.templates import payment_confirmation_email
from app.models import (
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    Activity,
    Booking,
    Edition,
    Participant,
    Payment,
    active_payments,
)
from app.services import audit
from app.services import edition as edition_service
from app.services.amounts import recompute_amount
from app.services.seats import (
    activities_for_update,
    expire_overdue,
    free_by_activity,
    free_by_slot,
    has_other_active_booking,
    lock_booking,
    slots_for_update,
)
from app.timefmt import format_activity, format_euro, status_label

EXPIRED_ALREADY_ACTIVE = (
    "Pagamento registrato, ma la persona ha già un'altra iscrizione attiva: questa prenotazione "
    "resta scaduta. Decidi come procedere con la persona."
)
EXPIRED_NO_ROOM = (
    "Pagamento registrato, ma la prenotazione è scaduta e almeno uno slot è ormai pieno: "
    "la prenotazione resta scaduta. Decidi come procedere con la persona."
)


# How long the confirmation email of a quick payment waits, so a mistaken click can be undone.
CONFIRMATION_EMAIL_DELAY = timedelta(seconds=30)


@dataclass
class PaymentResult:
    payment: Payment
    confirmed_now: bool
    reactivated: bool
    warning: str | None
    # Set when the confirmation email was deferred instead of sent.
    email_due_at: datetime | None = None
    # Activities dropped on reactivation because they had no seat left.
    dropped_activities: list[Activity] = field(default_factory=list)


def paid_total(booking: Booking) -> int:
    return sum(p.amount_cents for p in active_payments(booking))


def send_confirmation(sender: EmailSender, booking: Booking, paid_cents: int) -> None:
    sender.send(payment_confirmation_email(booking, paid_cents))


REVIVED = "revived"
NO_ROOM = "no_room"
ALREADY_ACTIVE = "already_active"


def revive_expired(
    db: Session, booking: Booking, now: datetime, dropped: list[Activity] | None = None
) -> str:
    """Bring an expired booking back for a new hold. Returns REVIVED, or why it could not be
    (changing nothing): NO_ROOM when a slot is full, ALREADY_ACTIVE when the person has signed up
    again and holds another booking, which would leave them with two.

    The hold starts now and the payment reminders start over. Activities that filled up while
    the booking was expired are dropped (and the amount recomputed); they are appended to
    `dropped` so the caller can say so.
    """
    if has_other_active_booking(db, booking, now):
        return ALREADY_ACTIVE
    slots = list(db.scalars(slots_for_update([s.id for s in booking.slots])))
    if not can_reactivate(free_by_slot(db, slots, now).values()):
        return NO_ROOM
    # Same locks as a sign-up, so a reactivation and a sign-up cannot both take the last seat.
    activities = list(
        db.scalars(activities_for_update([a.id for a in booking.activities], booking.edition_id))
    )
    free = free_by_activity(db, activities, now)
    full = [a for a in activities if not has_free_seat(free[a.id])]
    if full:
        booking.activities = [a for a in booking.activities if a not in full]
        edition = db.get(Edition, booking.edition_id)
        assert edition is not None
        recompute_amount(edition, booking)
        if dropped is not None:
            dropped.extend(full)
    booking.status = STATUS_PENDING
    booking.hold_expires_at = hold_deadline(now, _hold_days(db, booking))
    booking.hold_started_at = now
    booking.reminder_mid_sent_at = None
    booking.reminder_final_sent_at = None
    return REVIVED


def record_payment(
    db: Session,
    sender: EmailSender,
    booking: Booking,
    admin: Participant,
    amount_cents: int,
    channel: str,
    paid_on: date,
    note: str | None,
    now: datetime,
    defer_confirmation_email: bool = False,
) -> PaymentResult:
    """Register a payment and update the booking: confirm it when covered, revive it if expired.

    With `defer_confirmation_email` the confirmation email is not sent here: its due time is
    stored on the payment and `send_due_confirmations` sends it later, unless the payment is
    voided in the meantime.

    An expired booking is revived only if every one of its slots still has a free seat. Otherwise
    the payment is kept and the booking stays expired, with a warning for the admin.
    """
    lock_booking(db, booking.id)
    expire_overdue(db, now)
    db.refresh(booking)

    payment = Payment(
        booking_id=booking.id,
        amount_cents=amount_cents,
        channel=channel,
        paid_on=paid_on,
        note=note or None,
        recorded_by_id=admin.id,
        created_at=now,
    )
    db.add(payment)
    db.flush()
    db.refresh(booking)
    total = paid_total(booking)

    reactivated = False
    warning = None
    dropped: list[Activity] = []
    if booking.status == STATUS_EXPIRED:
        outcome = revive_expired(db, booking, now, dropped)
        if outcome == REVIVED:
            reactivated = True
            if dropped:
                warning = dropped_activities_warning(dropped)
        else:
            warning = EXPIRED_ALREADY_ACTIVE if outcome == ALREADY_ACTIVE else EXPIRED_NO_ROOM

    confirmed_now = False
    if booking.status == STATUS_PENDING and is_covered(booking.amount_due_cents, total):
        booking.status = STATUS_CONFIRMED
        confirmed_now = True

    email_due_at = None
    if confirmed_now and defer_confirmation_email:
        email_due_at = now + CONFIRMATION_EMAIL_DELAY
        payment.confirmation_email_due_at = email_due_at

    db.commit()
    if confirmed_now and not defer_confirmation_email:
        send_confirmation(sender, booking, total)
    return PaymentResult(
        payment,
        confirmed_now,
        reactivated,
        warning,
        email_due_at=email_due_at,
        dropped_activities=dropped,
    )


def send_due_confirmations(db: Session, sender: EmailSender, now: datetime) -> int:
    """Send the deferred confirmation emails that are due. Returns how many went out.

    Each one is claimed with a conditional UPDATE before sending, so two runs (the timer of the
    web app and the hourly job) never send the same email twice. A voided payment never sends,
    and neither does a booking that is no longer confirmed. A failed delivery is not retried.
    """
    due = db.scalars(
        select(Payment).where(
            Payment.confirmation_email_due_at <= now,
            Payment.confirmation_email_sent_at.is_(None),
            Payment.voided_at.is_(None),
        )
    ).all()
    sent = 0
    for payment in due:
        claimed = db.execute(
            update(Payment)
            .where(
                Payment.id == payment.id,
                Payment.confirmation_email_sent_at.is_(None),
                Payment.voided_at.is_(None),
            )
            .values(confirmation_email_sent_at=now)
        )
        db.commit()
        if claimed.rowcount != 1:
            continue
        booking = db.get(Booking, payment.booking_id)
        if booking is None:
            continue
        db.refresh(booking)
        if booking.status != STATUS_CONFIRMED:
            continue
        send_confirmation(sender, booking, paid_total(booking))
        sent += 1
    return sent


def dropped_activities_warning(dropped: list[Activity]) -> str:
    names = ", ".join(format_activity(a.title, a.date, a.period) for a in dropped)
    return (
        "Prenotazione riattivata senza queste attività, che nel frattempo sono al completo: "
        f"{names}."
    )


def _hold_days(db: Session, booking: Booking) -> int:
    edition = edition_service.get_active_edition(db)
    return edition.hold_days if edition else 3


class PaymentNotFound(Exception):
    pass


class AlreadyVoided(Exception):
    pass


def void_payment(
    db: Session,
    admin: Participant,
    booking: Booking,
    payment_id: int,
    reason: str,
    now: datetime,
) -> Payment:
    """Cancel a payment entered by mistake. It stays on record, struck out, and stops counting.

    A confirmed booking that the remaining payments no longer cover goes back to waiting for
    payment, with a new hold counted from now (and fresh reminders).
    """
    lock_booking(db, booking.id)
    expire_overdue(db, now)
    db.refresh(booking)
    payment = next((p for p in booking.payments if p.id == payment_id), None)
    if payment is None:
        raise PaymentNotFound()
    if payment.voided_at is not None:
        raise AlreadyVoided()

    old_status = booking.status
    payment.voided_at = now
    payment.voided_by_id = admin.id
    payment.void_reason = reason
    new_status = status_after_void(old_status, booking.amount_due_cents, paid_total(booking))
    if new_status != old_status:
        booking.status = new_status
        booking.hold_started_at = now
        booking.hold_expires_at = hold_deadline(now, _hold_days(db, booking))
        booking.reminder_mid_sent_at = None
        booking.reminder_final_sent_at = None

    channel = edition_service.PAYMENT_CHANNELS.get(payment.channel, payment.channel)
    detail = (
        f"Pagamento annullato: {format_euro(payment.amount_cents)} del "
        f"{payment.paid_on:%d/%m/%Y} ({channel}). Motivo: {reason}."
    )
    if new_status != old_status:
        detail += (
            f" Stato: {status_label(old_status)} → {status_label(new_status)}, con un nuovo blocco."
        )
    audit.log(db, admin, "payment_voided", detail, booking.id)
    db.commit()
    return payment
