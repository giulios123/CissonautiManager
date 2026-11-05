"""Waitlist for full slots: joining, leaving and, when a seat frees up, promotion."""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.domain.booking import (
    effective_status,
    has_free_seat,
    hold_deadline,
    is_past_day,
    occupies_seats,
)
from app.domain.fees import compute_fee, is_covered
from app.domain.reminders import reminders_to_keep_after_extension
from app.domain.waitlist import (
    JoinRefusal,
    PromotionKind,
    can_join,
    hold_after_promotion,
    promotion_kind,
    queue,
    waitlist_limit,
)
from app.email import EmailSender
from app.email.templates import waitlist_promoted_email
from app.models import (
    CLOSE_BOOKED,
    CLOSE_LEFT,
    CLOSE_PROMOTED,
    CLOSE_REMOVED,
    STATUS_CONFIRMED,
    STATUS_PENDING,
    Booking,
    Edition,
    Participant,
    Slot,
    WaitlistEntry,
    slot_sort_key,
)
from app.services import audit
from app.services import auth as auth_service
from app.services import edition as edition_service
from app.services.payments import paid_total
from app.services.seats import expire_overdue, free_by_slot, slots_for_update
from app.timefmt import format_slot


class WaitlistRefused(Exception):
    def __init__(self, reason: JoinRefusal) -> None:
        self.reason = reason
        super().__init__(reason)


class EntryNotFound(Exception):
    pass


class NoLegalAcceptance(Exception):
    """The person never accepted the legal texts: they must register through the form first."""


@dataclass(frozen=True)
class LegalAcceptance:
    privacy_document_id: int
    privacy_accepted_at: datetime
    disclaimer_document_id: int
    disclaimer_accepted_at: datetime


REFUSAL_MESSAGES: dict[str, str] = {
    "not_full": "Lo slot ha ancora posti liberi: prenotalo direttamente",
    "list_full": "La lista d'attesa di questo slot è completa",
    "already_booked": "Hai già questo slot",
    "already_listed": "Sei già in lista per questo slot",
    "past_day": "Il giorno di questo slot è già passato",
}


def active_entries(db: Session, slot_ids: Iterable[int]) -> dict[int, list[WaitlistEntry]]:
    """Active entries per slot, in promotion order."""
    ids = list(slot_ids)
    grouped: dict[int, list[WaitlistEntry]] = defaultdict(list)
    if not ids:
        return {}
    for entry in db.scalars(
        select(WaitlistEntry).where(
            WaitlistEntry.slot_id.in_(ids), WaitlistEntry.closed_at.is_(None)
        )
    ):
        grouped[entry.slot_id].append(entry)
    return {slot_id: queue(entries) for slot_id, entries in grouped.items()}


def entries_of(db: Session, participant: Participant, edition: Edition) -> list[WaitlistEntry]:
    """The person's active entries in the edition, in slot order."""
    entries = db.scalars(
        select(WaitlistEntry)
        .join(Slot, Slot.id == WaitlistEntry.slot_id)
        .where(
            WaitlistEntry.participant_id == participant.id,
            WaitlistEntry.closed_at.is_(None),
            Slot.edition_id == edition.id,
        )
        .order_by(Slot.date, Slot.start_time)
    )
    return list(entries)


def position_of(db: Session, entry: WaitlistEntry) -> int:
    ordered = active_entries(db, [entry.slot_id]).get(entry.slot_id, [])
    return next(i for i, e in enumerate(ordered, start=1) if e.id == entry.id)


def _active_booking(db: Session, participant: Participant, edition_id: int, now: datetime):
    booking = db.scalar(
        select(Booking)
        .where(Booking.participant_id == participant.id, Booking.edition_id == edition_id)
        .order_by(Booking.id.desc())
    )
    if booking is None:
        return None
    if not occupies_seats(effective_status(booking.status, booking.hold_expires_at, now)):
        return None
    return booking


def legal_of(db: Session, participant: Participant, edition: Edition) -> LegalAcceptance | None:
    """Legal texts the person already accepted in this edition: from their latest booking, or
    from a waitlist entry if they never had a booking."""
    booking = db.scalar(
        select(Booking)
        .where(Booking.participant_id == participant.id, Booking.edition_id == edition.id)
        .order_by(Booking.id.desc())
    )
    source: Booking | WaitlistEntry | None = booking
    if source is None:
        source = db.scalar(
            select(WaitlistEntry)
            .join(Slot, Slot.id == WaitlistEntry.slot_id)
            .where(WaitlistEntry.participant_id == participant.id, Slot.edition_id == edition.id)
            .order_by(WaitlistEntry.id.desc())
        )
    if source is None:
        return None
    return LegalAcceptance(
        source.privacy_document_id,
        source.privacy_accepted_at,
        source.disclaimer_document_id,
        source.disclaimer_accepted_at,
    )


def join(
    db: Session,
    participant: Participant,
    slot_id: int,
    now: datetime,
    legal: LegalAcceptance | None = None,
) -> WaitlistEntry:
    """Put the person on the waitlist of a full slot. The caller commits.

    The slot is locked first, so two people cannot take the last place on the list together.
    Without `legal`, the texts already accepted in this edition are used.
    """
    edition = edition_service.get_active_edition(db)
    if edition is None:
        raise EntryNotFound()
    expire_overdue(db, now)
    slot = db.scalar(slots_for_update([slot_id], edition.id))
    if slot is None:
        raise EntryNotFound()
    if legal is None:
        legal = legal_of(db, participant, edition)
        if legal is None:
            raise NoLegalAcceptance()

    free = free_by_slot(db, [slot], now)[slot.id]
    entries = active_entries(db, [slot.id]).get(slot.id, [])
    booking = _active_booking(db, participant, edition.id, now)
    check = can_join(
        free=free,
        active_entries=len(entries),
        limit=waitlist_limit(slot.capacity, edition.waitlist_percent),
        already_booked=booking is not None and slot in booking.slots,
        already_listed=any(e.participant_id == participant.id for e in entries),
        past_day=is_past_day(slot.date, now),
    )
    if not check.ok:
        assert check.reason is not None
        raise WaitlistRefused(check.reason)

    entry = WaitlistEntry(
        slot_id=slot.id,
        participant_id=participant.id,
        created_at=now,
        privacy_document_id=legal.privacy_document_id,
        privacy_accepted_at=legal.privacy_accepted_at,
        disclaimer_document_id=legal.disclaimer_document_id,
        disclaimer_accepted_at=legal.disclaimer_accepted_at,
    )
    db.add(entry)
    db.flush()
    return entry


def close(entry: WaitlistEntry, reason: str, now: datetime) -> None:
    entry.closed_at = now
    entry.close_reason = reason


def leave(db: Session, participant: Participant, entry_id: int, now: datetime) -> None:
    entry = db.get(WaitlistEntry, entry_id)
    if entry is None or entry.participant_id != participant.id or entry.closed_at is not None:
        raise EntryNotFound()
    close(entry, CLOSE_LEFT, now)
    db.commit()


def remove(db: Session, admin: Participant, entry_id: int, now: datetime) -> None:
    """An admin takes someone off a waitlist. No email: the admin tells the person."""
    entry = db.get(WaitlistEntry, entry_id)
    if entry is None or entry.closed_at is not None:
        raise EntryNotFound()
    close(entry, CLOSE_REMOVED, now)
    slot, person = entry.slot, entry.participant
    booking = _latest_booking(db, person.id, slot.edition_id)
    audit.log(
        db,
        admin,
        "waitlist_removed",
        f"{person.first_name} {person.last_name} ({person.email}) tolto dalla lista d'attesa di "
        f"{format_slot(slot.date, slot.period, slot.start_time, slot.end_time)}",
        booking.id if booking is not None else None,
    )
    db.commit()


def waitlist_availability(
    db: Session, edition: Edition, slots: list[Slot], free: dict[int, int | None], now: datetime
) -> dict[int, int | None]:
    """Places left on the waitlist of each full slot that can still be joined; None otherwise."""
    entries = active_entries(db, [s.id for s in slots])
    result: dict[int, int | None] = {}
    for slot in slots:
        limit = waitlist_limit(slot.capacity, edition.waitlist_percent)
        full = free[slot.id] is not None and free[slot.id] == 0
        if not full or limit == 0 or is_past_day(slot.date, now):
            result[slot.id] = None
        else:
            result[slot.id] = max(limit - len(entries.get(slot.id, [])), 0)
    return result


@dataclass
class Promotion:
    entry: WaitlistEntry
    slot: Slot
    booking: Booking
    kind: PromotionKind


def promote_freed(
    db: Session, sender: EmailSender, settings: Settings, slot_ids: Iterable[int], now: datetime
) -> list[Promotion]:
    """Give the seats free in these slots to the first people on their waitlists.

    Call it after committing whatever freed the seats. Each slot is handled in its own
    transaction, under the slot lock, so two concurrent calls cannot hand out the same seat.
    Emails go out after each commit.
    """
    edition = edition_service.get_active_edition(db)
    if edition is None:
        return []
    done: list[Promotion] = []
    for slot_id in sorted(set(slot_ids)):
        expire_overdue(db, now)
        promotions = _promote_slot(db, edition, slot_id, now)
        db.commit()
        for promotion in promotions:
            _notify(db, sender, settings, edition, promotion, now)
        done.extend(promotions)
    return done


def slots_with_waiting_people(db: Session, edition: Edition) -> list[int]:
    return list(
        db.scalars(
            select(WaitlistEntry.slot_id)
            .join(Slot, Slot.id == WaitlistEntry.slot_id)
            .where(WaitlistEntry.closed_at.is_(None), Slot.edition_id == edition.id)
            .distinct()
        )
    )


def _promote_slot(db: Session, edition: Edition, slot_id: int, now: datetime) -> list[Promotion]:
    slot = db.scalar(slots_for_update([slot_id], edition.id))
    if slot is None or slot.capacity is None or is_past_day(slot.date, now):
        return []
    entries = active_entries(db, [slot.id]).get(slot.id, [])
    promotions: list[Promotion] = []
    free = free_by_slot(db, [slot], now)[slot.id]
    while entries and has_free_seat(free):
        entry = entries.pop(0)
        current = _latest_booking(db, entry.participant_id, edition.id)
        status = effective_status(current.status, current.hold_expires_at, now) if current else None
        if current is not None and occupies_seats(status or "") and slot in current.slots:
            # Got the seat some other way (an admin forced it): nothing to give.
            close(entry, CLOSE_BOOKED, now)
            continue
        kind = promotion_kind(status)
        if kind == "new_booking" or current is None:
            booking = _new_booking(db, edition, entry, slot, now)
        else:
            booking = current
            _add_slot(booking, edition, slot, kind, now)
        db.flush()
        close(entry, CLOSE_PROMOTED, now)
        entry.promoted_booking_id = booking.id
        promotions.append(Promotion(entry, slot, booking, kind))
        free = free_by_slot(db, [slot], now)[slot.id]
    return promotions


def _latest_booking(db: Session, participant_id: int, edition_id: int) -> Booking | None:
    return db.scalar(
        select(Booking)
        .where(Booking.participant_id == participant_id, Booking.edition_id == edition_id)
        .order_by(Booking.id.desc())
    )


def _new_booking(
    db: Session, edition: Edition, entry: WaitlistEntry, slot: Slot, now: datetime
) -> Booking:
    booking = Booking(
        edition_id=edition.id,
        participant_id=entry.participant_id,
        status=STATUS_PENDING,
        hold_expires_at=hold_deadline(now, edition.hold_days),
        hold_started_at=now,
        amount_due_cents=compute_fee(
            [slot.date], edition.base_fee_cents, edition.per_day_fee_cents
        ),
        privacy_document_id=entry.privacy_document_id,
        privacy_accepted_at=entry.privacy_accepted_at,
        disclaimer_document_id=entry.disclaimer_document_id,
        disclaimer_accepted_at=entry.disclaimer_accepted_at,
        created_at=now,
    )
    booking.slots = [slot]
    db.add(booking)
    return booking


def _add_slot(booking: Booking, edition: Edition, slot: Slot, kind: str, now: datetime) -> None:
    """Add the slot to a pending or confirmed booking and recompute the amount.

    A pending booking gets at least a full hold from now; a confirmed one stays confirmed and its
    balance shows the difference (D-017).
    """
    booking.slots = sorted([*booking.slots, slot], key=slot_sort_key)
    booking.amount_due_cents = compute_fee(
        [s.date for s in booking.slots], edition.base_fee_cents, edition.per_day_fee_cents
    )
    if kind != "add_to_pending":
        return
    new_expiry = hold_after_promotion(booking.hold_expires_at, now, edition.hold_days)
    if new_expiry != booking.hold_expires_at:
        booking.reminder_mid_sent_at, booking.reminder_final_sent_at = (
            reminders_to_keep_after_extension(
                booking.hold_started_at,
                new_expiry,
                booking.reminder_mid_sent_at,
                booking.reminder_final_sent_at,
                now,
            )
        )
        booking.hold_expires_at = new_expiry
    if is_covered(booking.amount_due_cents, paid_total(booking)):
        booking.status = STATUS_CONFIRMED


def _notify(
    db: Session,
    sender: EmailSender,
    settings: Settings,
    edition: Edition,
    promotion: Promotion,
    now: datetime,
) -> None:
    from app.services.registration import enabled_channels

    booking = promotion.booking
    if promotion.kind == "new_booking":
        participant = db.get(Participant, booking.participant_id)
        assert participant is not None
        raw = auth_service.create_magic_link_token(db, participant, now)
        link = auth_service.magic_link_url(settings, raw)
    else:
        link = f"{settings.app_base_url.rstrip('/')}/accedi"
    sender.send(
        waitlist_promoted_email(
            booking,
            promotion.slot,
            promotion.kind,
            enabled_channels(db, edition),
            booking.amount_due_cents - paid_total(booking),
            link,
        )
    )
