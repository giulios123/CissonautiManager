"""Read models behind the admin views: who is present, and what needs a look."""

from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.booking import effective_status, occupies_seats
from app.domain.presence import Presence, presences
from app.models import Booking, Edition, Slot, slot_sort_key
from app.services import edition as edition_service
from app.services.seats import expire_overdue


@dataclass(frozen=True)
class Person:
    participant_id: int
    booking_id: int
    first_name: str
    last_name: str
    email: str
    status: str


@dataclass
class PresenceData:
    edition: Edition | None = None
    slots: list[Slot] = field(default_factory=list)
    rows: list[Presence] = field(default_factory=list)
    people: dict[int, Person] = field(default_factory=dict)


def load_presence(db: Session, now: datetime) -> PresenceData:
    """Presences of the active edition: only bookings that occupy seats, derived evenings included.

    Expired holds, requested cancellations and refunds are left out, as they are for seat counts.
    """
    edition = edition_service.get_active_edition(db)
    if edition is None:
        return PresenceData()
    expire_overdue(db, now)
    db.commit()
    people: dict[int, Person] = {}
    booked: list[tuple[int, date, str]] = []
    bookings = db.scalars(select(Booking).where(Booking.edition_id == edition.id)).all()
    for booking in bookings:
        status = effective_status(booking.status, booking.hold_expires_at, now)
        if not occupies_seats(status):
            continue
        participant = booking.participant
        people[participant.id] = Person(
            participant_id=participant.id,
            booking_id=booking.id,
            first_name=participant.first_name,
            last_name=participant.last_name,
            email=participant.email,
            status=status,
        )
        booked.extend((participant.id, s.date, s.period) for s in booking.slots)
    return PresenceData(
        edition=edition,
        slots=sorted(edition.slots, key=slot_sort_key),
        rows=presences(booked),
        people=people,
    )
