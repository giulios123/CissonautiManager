from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.domain.booking import effective_status, has_free_seat, hold_deadline
from app.domain.fees import compute_fee
from app.email import EmailSender
from app.email.templates import already_registered_email, registration_email
from app.models import (
    STATUS_CONFIRMED,
    STATUS_PENDING,
    Booking,
    Edition,
    Participant,
    PaymentChannel,
    Slot,
)
from app.services import auth as auth_service
from app.services import edition as edition_service
from app.services.participants import get_by_email, new_unique_personal_code, normalize_email
from app.services.seats import expire_overdue, free_by_slot, slots_for_update


class RegistrationClosed(Exception):
    pass


class InvalidSlots(Exception):
    pass


class LegalTextsChanged(Exception):
    pass


class SlotsFull(Exception):
    def __init__(self, slots: list[Slot]) -> None:
        self.slots = slots
        super().__init__("Some slots are full")


@dataclass
class RegistrationData:
    first_name: str
    last_name: str
    email: str
    phone: str | None
    invited_by: str | None
    can_bring: str
    slot_ids: list[int]
    privacy_version: int
    disclaimer_version: int


@dataclass
class RegistrationResult:
    created: bool
    booking: Booking | None
    participant: Participant


def is_registration_open(db: Session, edition: Edition | None) -> bool:
    if edition is None or not edition.slots:
        return False
    return all(
        edition_service.latest_legal_document(db, edition, kind) is not None
        for kind in edition_service.LEGAL_KINDS
    )


def enabled_channels(db: Session, edition: Edition) -> list[PaymentChannel]:
    return [c for c in edition_service.list_channels(db, edition) if c.enabled]


def _has_active_booking(db: Session, participant: Participant, edition: Edition, now) -> bool:
    bookings = db.scalars(
        select(Booking).where(
            Booking.participant_id == participant.id, Booking.edition_id == edition.id
        )
    )
    return any(
        effective_status(b.status, b.hold_expires_at, now) in (STATUS_PENDING, STATUS_CONFIRMED)
        for b in bookings
    )


def register(
    db: Session,
    sender: EmailSender,
    settings: Settings,
    data: RegistrationData,
    now: datetime,
) -> RegistrationResult:
    edition = edition_service.get_active_edition(db)
    if not is_registration_open(db, edition):
        raise RegistrationClosed()
    assert edition is not None

    privacy = edition_service.latest_legal_document(db, edition, "privacy")
    disclaimer = edition_service.latest_legal_document(db, edition, "disclaimer")
    assert privacy is not None and disclaimer is not None
    if (privacy.version, disclaimer.version) != (data.privacy_version, data.disclaimer_version):
        raise LegalTextsChanged()

    wanted_ids = set(data.slot_ids)
    expire_overdue(db, now)

    existing = get_by_email(db, data.email)
    if existing is not None and _has_active_booking(db, existing, edition, now):
        _send_link_only(db, sender, settings, existing, now)
        return RegistrationResult(created=False, booking=None, participant=existing)

    # Lock the chosen slots so two concurrent registrations cannot take the last seat together.
    slots = list(db.scalars(slots_for_update(wanted_ids, edition.id)))
    if len(slots) != len(wanted_ids):
        raise InvalidSlots()
    free = free_by_slot(db, slots, now)
    full = [s for s in slots if not has_free_seat(free[s.id])]
    if full:
        raise SlotsFull(full)

    participant = existing
    if participant is None:
        participant = Participant(
            first_name=data.first_name,
            last_name=data.last_name,
            email=normalize_email(data.email),
            phone=data.phone or None,
            invited_by=data.invited_by or None,
            can_bring=data.can_bring,
            personal_code=new_unique_personal_code(db),
        )
        db.add(participant)
        db.flush()

    booking = Booking(
        edition_id=edition.id,
        participant_id=participant.id,
        status=STATUS_PENDING,
        hold_expires_at=hold_deadline(now, edition.hold_days),
        hold_started_at=now,
        amount_due_cents=compute_fee(
            [s.date for s in slots], edition.base_fee_cents, edition.per_day_fee_cents
        ),
        privacy_document_id=privacy.id,
        privacy_accepted_at=now,
        disclaimer_document_id=disclaimer.id,
        disclaimer_accepted_at=now,
        created_at=now,
    )
    booking.slots = slots
    db.add(booking)
    db.commit()

    raw = auth_service.create_magic_link_token(db, participant, now)
    sender.send(
        registration_email(
            participant,
            booking,
            enabled_channels(db, edition),
            auth_service.magic_link_url(settings, raw),
        )
    )
    return RegistrationResult(created=True, booking=booking, participant=participant)


def _send_link_only(
    db: Session, sender: EmailSender, settings: Settings, participant: Participant, now: datetime
) -> None:
    raw = auth_service.create_magic_link_token(db, participant, now)
    sender.send(already_registered_email(participant, auth_service.magic_link_url(settings, raw)))
