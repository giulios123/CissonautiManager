from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session, object_session

from app.config import Settings, get_settings
from app.domain.booking import can_reactivate, has_free_seat, hold_deadline, status_after_void
from app.domain.confirmation import POLICY_REGISTRATION_FEE
from app.email import EmailSender
from app.email.templates import booking_confirmation_email, payment_confirmation_email
from app.i18n import t
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
from app.services import email_templates as email_templates_service
from app.services.amounts import confirmation_covered, confirmation_due, recompute_amount
from app.services.seats import (
    activities_for_update,
    expire_overdue,
    free_by_activity,
    free_by_slot,
    has_other_active_booking,
    lock_booking,
    lock_edition,
    slots_for_update,
)
from app.timefmt import format_activity, format_euro, status_label

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
    db = object_session(booking)
    assert db is not None
    texts = email_templates_service.texts_for_booking(db, booking, "payment_confirmation")
    sender.send(payment_confirmation_email(booking, paid_cents, texts))


def queue_confirmation_notice(
    booking: Booking,
    now: datetime,
    *,
    payment_id: int | None = None,
    due_at: datetime | None = None,
) -> bool:
    """Persist one notification cycle for a newly confirmed booking under the fee policy."""
    if booking.edition.confirmation_policy != POLICY_REGISTRATION_FEE:
        return False
    booking.confirmation_cycle = (
        max(booking.confirmation_cycle, booking.confirmation_claimed_cycle) + 1
    )
    booking.confirmation_notice_due_at = due_at or now
    booking.confirmation_notice_payment_id = payment_id
    return True


def send_transition_confirmation(
    db: Session,
    sender: EmailSender,
    booking: Booking,
    paid_cents: int,
    now: datetime,
) -> None:
    """Dispatch the queued fee-policy notice or preserve the legacy payment email."""
    if booking.edition.confirmation_policy == POLICY_REGISTRATION_FEE:
        send_due_confirmations(db, sender, now)
    else:
        send_confirmation(sender, booking, paid_cents)


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
        if dropped is not None:
            dropped.extend(full)
    # Prices and collection policies may have changed while this booking was expired.
    edition = db.get(Edition, booking.edition_id)
    assert edition is not None
    db.refresh(edition)
    recompute_amount(edition, booking)
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
    settings: Settings | None = None,
) -> PaymentResult:
    """Register a payment and update the booking: confirm it when covered, revive it if expired.

    With `defer_confirmation_email` the confirmation email is not sent here: its due time is
    stored on the payment and `send_due_confirmations` sends it later, unless the payment is
    voided in the meantime.

    An expired booking is revived only if every one of its slots still has a free seat. Otherwise
    the payment is kept and the booking stays expired, with a warning for the admin.
    """
    lock_edition(db, booking.edition_id)
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
            warning = t(
                "warn.payment_expired_already_active"
                if outcome == ALREADY_ACTIVE
                else "warn.payment_expired_no_room"
            )

    confirmed_now = False
    if booking.status == STATUS_PENDING and confirmation_covered(booking.edition, booking, total):
        booking.status = STATUS_CONFIRMED
        confirmed_now = True

    email_due_at = None
    if confirmed_now and defer_confirmation_email:
        email_due_at = now + CONFIRMATION_EMAIL_DELAY
    queued_cycle = False
    if confirmed_now and booking.edition.confirmation_policy == POLICY_REGISTRATION_FEE:
        queued_cycle = queue_confirmation_notice(
            booking,
            now,
            payment_id=payment.id,
            due_at=email_due_at or now,
        )
    elif confirmed_now and defer_confirmation_email:
        payment.confirmation_email_due_at = email_due_at

    db.commit()
    if confirmed_now and not defer_confirmation_email:
        if queued_cycle:
            send_due_confirmations(db, sender, now, settings)
        else:
            send_confirmation(sender, booking, total)
    return PaymentResult(
        payment,
        confirmed_now,
        reactivated,
        warning,
        email_due_at=email_due_at,
        dropped_activities=dropped,
    )


def send_due_confirmations(
    db: Session, sender: EmailSender, now: datetime, settings: Settings | None = None
) -> int:
    """Claim and send legacy receipts or the current confirmed-status notification cycle.

    Claims commit before delivery. A failed email is logged by the caller and is not retried,
    while the conditional update prevents a timer and the hourly job from sending it twice.
    """
    settings = settings or get_settings()
    sent = 0

    legacy_payment_ids = list(
        db.scalars(
            select(Payment.id)
            .join(Booking, Booking.id == Payment.booking_id)
            .join(Edition, Edition.id == Booking.edition_id)
            .where(
                Edition.confirmation_policy != POLICY_REGISTRATION_FEE,
                Payment.confirmation_email_due_at <= now,
                Payment.confirmation_email_sent_at.is_(None),
                Payment.voided_at.is_(None),
            )
            .order_by(Payment.id)
        )
    )
    for payment_id in legacy_payment_ids:
        payment = db.get(Payment, payment_id)
        if payment is None:
            continue
        booking = db.get(Booking, payment.booking_id)
        if booking is None:
            continue
        lock_edition(db, booking.edition_id)
        lock_booking(db, booking.id)
        db.refresh(booking)
        db.refresh(payment)
        edition = db.get(Edition, booking.edition_id)
        if edition is None:
            db.rollback()
            continue
        db.refresh(edition)
        if (
            edition.confirmation_policy == POLICY_REGISTRATION_FEE
            or payment.confirmation_email_due_at is None
            or payment.confirmation_email_due_at > now
            or payment.confirmation_email_sent_at is not None
            or payment.voided_at is not None
        ):
            db.rollback()
            continue
        claimed = db.execute(
            update(Payment)
            .where(
                Payment.id == payment.id,
                Payment.confirmation_email_sent_at.is_(None),
                Payment.voided_at.is_(None),
                Payment.confirmation_email_due_at <= now,
            )
            .values(confirmation_email_sent_at=now)
        )
        db.commit()
        if claimed.rowcount != 1 or booking.status != STATUS_CONFIRMED:
            continue
        db.refresh(booking)
        send_confirmation(sender, booking, paid_total(booking))
        sent += 1

    cycle_candidates = list(
        db.execute(
            select(Booking.id, Booking.confirmation_cycle)
            .join(Edition, Edition.id == Booking.edition_id)
            .where(
                Edition.confirmation_policy == POLICY_REGISTRATION_FEE,
                Booking.confirmation_notice_due_at <= now,
                Booking.confirmation_cycle > Booking.confirmation_claimed_cycle,
            )
            .order_by(Booking.id)
        ).all()
    )
    login_url = f"{settings.app_base_url.rstrip('/')}/login"
    for booking_id, candidate_cycle in cycle_candidates:
        booking = db.get(Booking, booking_id)
        if booking is None:
            continue
        lock_edition(db, booking.edition_id)
        lock_booking(db, booking.id)
        db.refresh(booking)
        edition = db.get(Edition, booking.edition_id)
        if edition is None:
            db.rollback()
            continue
        db.refresh(edition)
        due_at = booking.confirmation_notice_due_at
        if (
            edition.confirmation_policy != POLICY_REGISTRATION_FEE
            or booking.confirmation_cycle != candidate_cycle
            or booking.confirmation_claimed_cycle >= candidate_cycle
            or due_at is None
            or due_at > now
        ):
            db.rollback()
            continue

        source_payment = None
        if booking.confirmation_notice_payment_id is not None:
            source_payment = db.get(Payment, booking.confirmation_notice_payment_id)
        invalid_source = booking.confirmation_notice_payment_id is not None and (
            source_payment is None
            or source_payment.booking_id != booking.id
            or source_payment.voided_at is not None
        )
        if booking.status != STATUS_CONFIRMED or invalid_source:
            db.execute(
                update(Booking)
                .where(
                    Booking.id == booking.id,
                    Booking.confirmation_cycle == candidate_cycle,
                )
                .values(
                    confirmation_claimed_cycle=candidate_cycle,
                    confirmation_notice_due_at=None,
                    confirmation_notice_payment_id=None,
                )
            )
            db.commit()
            continue

        claimed = db.execute(
            update(Booking)
            .where(
                Booking.id == booking.id,
                Booking.status == STATUS_CONFIRMED,
                Booking.confirmation_cycle == candidate_cycle,
                Booking.confirmation_claimed_cycle < candidate_cycle,
                Booking.confirmation_notice_due_at == due_at,
                Booking.confirmation_notice_due_at <= now,
            )
            .values(
                confirmation_claimed_cycle=candidate_cycle,
                confirmation_notice_due_at=None,
            )
        )
        if claimed.rowcount == 1 and source_payment is not None:
            db.execute(
                update(Payment)
                .where(Payment.id == source_payment.id, Payment.booking_id == booking.id)
                .values(confirmation_email_sent_at=now)
            )
        db.commit()
        if claimed.rowcount != 1:
            continue
        db.refresh(booking)
        paid = paid_total(booking)
        if source_payment is not None:
            send_confirmation(sender, booking, paid)
        else:
            texts = email_templates_service.texts_for_booking(db, booking, "booking_confirmation")
            sender.send(booking_confirmation_email(booking, paid, login_url, texts))
        sent += 1
    return sent


def dropped_activities_warning(dropped: list[Activity]) -> str:
    names = ", ".join(format_activity(a.title, a.date, a.period) for a in dropped)
    return t("warn.revived_without_activities", names=names)


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
    lock_edition(db, booking.edition_id)
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
    if booking.confirmation_notice_payment_id == payment.id:
        booking.confirmation_notice_due_at = None
        booking.confirmation_notice_payment_id = None
    new_status = status_after_void(
        old_status, confirmation_due(booking.edition, booking), paid_total(booking)
    )
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
