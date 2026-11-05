from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.domain.booking import can_reactivate, hold_deadline
from app.domain.fees import is_covered
from app.email import EmailMessage, EmailSender
from app.models import (
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    Booking,
    Participant,
    Payment,
    slot_sort_key,
)
from app.services import edition as edition_service
from app.services.seats import expire_overdue, free_by_slot, slots_for_update
from app.timefmt import format_euro, format_slot

EXPIRED_NO_ROOM = (
    "Pagamento registrato, ma la prenotazione è scaduta e almeno uno slot è ormai pieno: "
    "la prenotazione resta scaduta. Decidi come procedere con la persona."
)


@dataclass
class PaymentResult:
    payment: Payment
    confirmed_now: bool
    reactivated: bool
    warning: str | None


def paid_total(booking: Booking) -> int:
    return sum(p.amount_cents for p in booking.payments)


def send_confirmation(sender: EmailSender, booking: Booking, paid_cents: int) -> None:
    participant = booking.participant
    slots = "\n".join(
        f"- {format_slot(s.date, s.period, s.start_time, s.end_time)}"
        for s in sorted(booking.slots, key=slot_sort_key)
    )
    sender.send(
        EmailMessage(
            to=participant.email,
            subject="Pagamento ricevuto: sei dentro!",
            body=(
                f"Ciao {participant.first_name},\n\n"
                f"abbiamo registrato il tuo pagamento ({format_euro(paid_cents)}): "
                "la tua iscrizione al Cissonauti Summer Camp è confermata.\n\n"
                f"I tuoi slot:\n{slots}\n\nCi vediamo presto!\n"
            ),
        )
    )


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
) -> PaymentResult:
    """Register a payment and update the booking: confirm it when covered, revive it if expired.

    An expired booking is revived only if every one of its slots still has a free seat. Otherwise
    the payment is kept and the booking stays expired, with a warning for the admin.
    """
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
    if booking.status == STATUS_EXPIRED:
        slots = list(db.scalars(slots_for_update([s.id for s in booking.slots])))
        if can_reactivate(free_by_slot(db, slots, now).values()):
            booking.status = STATUS_PENDING
            booking.hold_expires_at = hold_deadline(now, _hold_days(db, booking))
            reactivated = True
        else:
            warning = EXPIRED_NO_ROOM

    confirmed_now = False
    if booking.status == STATUS_PENDING and is_covered(booking.amount_due_cents, total):
        booking.status = STATUS_CONFIRMED
        confirmed_now = True

    db.commit()
    if confirmed_now:
        send_confirmation(sender, booking, total)
    return PaymentResult(payment, confirmed_now, reactivated, warning)


def _hold_days(db: Session, booking: Booking) -> int:
    edition = edition_service.get_active_edition(db)
    return edition.hold_days if edition else 3
