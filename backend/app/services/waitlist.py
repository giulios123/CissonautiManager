"""Waitlist for full slots: joining, leaving and, when a seat frees up, promotion."""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.booking import effective_status, is_past_day, occupies_seats
from app.domain.waitlist import JoinRefusal, can_join, queue, waitlist_limit
from app.models import (
    CLOSE_LEFT,
    Booking,
    Edition,
    Participant,
    Slot,
    WaitlistEntry,
)
from app.services import edition as edition_service
from app.services.seats import expire_overdue, free_by_slot, slots_for_update


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
