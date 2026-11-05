from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.booking import (
    can_edit_slots,
    can_request_cancellation,
    effective_status,
    has_free_seat,
    is_past_day,
)
from app.domain.fees import compute_fee, is_covered
from app.email import EmailSender
from app.email.templates import cancellation_email
from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_PENDING,
    Booking,
    Edition,
    Participant,
    Slot,
    slot_sort_key,
)
from app.services import audit
from app.services import edition as edition_service
from app.services.payments import paid_total, send_confirmation
from app.services.registration import InvalidSlots, SlotsFull
from app.services.seats import expire_overdue, free_by_slot, slots_for_update
from app.timefmt import format_euro, format_slot


class NotEditable(Exception):
    pass


class EmptySelection(Exception):
    pass


class PastDay(Exception):
    pass


@dataclass
class ChangeResult:
    booking: Booking
    confirmed_now: bool = False
    # Slots that went over capacity because an admin forced the change.
    over_capacity: list[Slot] = field(default_factory=list)


def get_current_booking(db: Session, participant: Participant) -> Booking | None:
    """The participant's latest booking in the active edition (only one can be active)."""
    edition = edition_service.get_active_edition(db)
    if edition is None:
        return None
    return db.scalar(
        select(Booking)
        .where(Booking.participant_id == participant.id, Booking.edition_id == edition.id)
        .order_by(Booking.id.desc())
    )


def change_slots(
    db: Session,
    sender: EmailSender,
    booking: Booking,
    slot_ids: list[int],
    now: datetime,
    force: bool = False,
    allow_past: bool = False,
    actor: Participant | None = None,
) -> ChangeResult:
    """Replace the slots of a pending or confirmed booking and recompute the amount due.

    The hold deadline never changes, and a confirmed booking stays confirmed whatever the new
    amount (the balance shows what is left to pay, or the credit). Seats are checked only for
    the slots being added. The next arguments are for admins: `force` accepts full slots,
    `allow_past` accepts days already over, and `actor` records the change in the audit log.
    """
    expire_overdue(db, now)
    db.refresh(booking)
    if not can_edit_slots(effective_status(booking.status, booking.hold_expires_at, now)):
        raise NotEditable()
    wanted = set(slot_ids)
    if not wanted:
        raise EmptySelection()

    # Lock the chosen slots so two concurrent changes cannot take the last seat together.
    slots = list(db.scalars(slots_for_update(wanted, booking.edition_id)))
    if len(slots) != len(wanted):
        raise InvalidSlots()
    current = {s.id: s for s in booking.slots}
    added = [s for s in slots if s.id not in current]
    removed = [s for sid, s in current.items() if sid not in wanted]

    if not (force or allow_past) and any(is_past_day(s.date, now) for s in added + removed):
        raise PastDay()
    free = free_by_slot(db, added, now)
    full = [s for s in added if not has_free_seat(free[s.id])]
    if full and not force:
        raise SlotsFull(full)

    edition = db.get(Edition, booking.edition_id)
    assert edition is not None
    old_amount = booking.amount_due_cents
    booking.slots = sorted(slots, key=slot_sort_key)
    booking.amount_due_cents = compute_fee(
        [s.date for s in slots], edition.base_fee_cents, edition.per_day_fee_cents
    )
    if actor is not None:
        audit.log(
            db,
            actor,
            "slots_changed",
            _describe_slot_change(added, removed, full, old_amount, booking.amount_due_cents),
            booking.id,
        )

    # Fewer days can bring the amount down to what was already paid: the booking is then done.
    total = paid_total(booking)
    confirmed_now = booking.status == STATUS_PENDING and is_covered(booking.amount_due_cents, total)
    if confirmed_now:
        booking.status = STATUS_CONFIRMED
    db.commit()
    if confirmed_now:
        send_confirmation(sender, booking, total)
    return ChangeResult(booking, confirmed_now, full)


def _labels(slots: list[Slot]) -> str:
    return ", ".join(
        format_slot(s.date, s.period, s.start_time, s.end_time)
        for s in sorted(slots, key=slot_sort_key)
    )


def _describe_slot_change(
    added: list[Slot], removed: list[Slot], full: list[Slot], old_cents: int, new_cents: int
) -> str:
    parts = ["Slot modificati."]
    if added:
        parts.append(f"Aggiunti: {_labels(added)}.")
    if removed:
        parts.append(f"Tolti: {_labels(removed)}.")
    parts.append(f"Quota: {format_euro(old_cents)} → {format_euro(new_cents)}.")
    if full:
        parts.append(f"Oltre la capienza: {_labels(full)}.")
    return " ".join(parts)


CancelOutcome = Literal["removed", "requested"]


def request_cancellation(
    db: Session,
    sender: EmailSender,
    booking: Booking,
    now: datetime,
    actor: Participant | None = None,
) -> CancelOutcome:
    """Cancel a pending or confirmed booking; its seats are free right away.

    With no payment on record the booking is simply removed (the person stays registered and can
    sign up again). Otherwise it becomes `disdetta_richiesta`, and an admin refunds outside the
    system and closes it. With an `actor` (an admin cancelling on someone's behalf) the action is
    recorded in the audit log, with the person's name since the booking itself may be gone.
    """
    expire_overdue(db, now)
    db.refresh(booking)
    if not can_request_cancellation(effective_status(booking.status, booking.hold_expires_at, now)):
        raise NotEditable()
    # Read before a possible delete: the email goes out after the commit.
    to, first_name = booking.participant.email, booking.participant.first_name

    outcome: CancelOutcome
    if booking.payments:
        booking.status = STATUS_CANCEL_REQUESTED
        booking.cancel_requested_at = now
        outcome = "requested"
    else:
        booking.slots = []
        db.delete(booking)
        outcome = "removed"
    if actor is not None:
        participant = booking.participant
        result = (
            "iscrizione rimossa, nessun pagamento" if outcome == "removed" else "disdetta richiesta"
        )
        audit.log(
            db,
            actor,
            "cancelled_by_admin",
            f"Disdetta registrata a nome di {participant.first_name} {participant.last_name} "
            f"({participant.email}): {result}",
            booking.id,
        )
    db.commit()
    sender.send(cancellation_email(to, first_name, removed=outcome == "removed"))
    return outcome
