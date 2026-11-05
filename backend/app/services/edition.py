from datetime import date, time, timedelta

from sqlalchemy import func, select, true
from sqlalchemy.orm import Session

from app.models import (
    DOC_DISCLAIMER,
    DOC_PRIVACY,
    PERIOD_AFTERNOON,
    PERIOD_EVENING,
    PERIOD_MORNING,
    BookingSlot,
    Edition,
    LegalDocument,
    PaymentChannel,
    Slot,
    WaitlistEntry,
)

PAYMENT_CHANNELS = {
    "revolut": "Revolut",
    "satispay": "Satispay",
    "paypal": "PayPal",
    "iban": "Bonifico (IBAN)",
}
LEGAL_KINDS = (DOC_PRIVACY, DOC_DISCLAIMER)


class SlotsInUseError(Exception):
    def __init__(self, days: list[date]) -> None:
        self.days = days
        super().__init__(f"Days with booked slots: {days}")


def get_active_edition(db: Session) -> Edition | None:
    return db.scalar(select(Edition).where(Edition.is_active == true()).order_by(Edition.id.desc()))


def _daterange(start: date, end: date):
    for offset in range((end - start).days + 1):
        yield start + timedelta(days=offset)


def sync_slots(db: Session, edition: Edition) -> None:
    """Make the edition's slots match its dates, hours and capacity.

    Raises SlotsInUseError, changing nothing, if a day to remove has booked slots.
    """
    wanted_days = (
        set(_daterange(edition.start_date, edition.end_date))
        if edition.start_date and edition.end_date
        else set()
    )
    existing = {(s.date, s.period): s for s in edition.slots}

    removed = [s for s in existing.values() if s.date not in wanted_days]
    if removed:
        removed_ids = [s.id for s in removed]
        # Waitlist entries are kept as history, so a slot that had any is in use too.
        used = [
            *db.scalars(select(BookingSlot.slot_id).where(BookingSlot.slot_id.in_(removed_ids))),
            *db.scalars(
                select(WaitlistEntry.slot_id).where(WaitlistEntry.slot_id.in_(removed_ids))
            ),
        ]
        blocked = sorted({s.date for s in removed if s.id in set(used)})
        if blocked:
            raise SlotsInUseError(blocked)
    for slot in removed:
        db.delete(slot)

    hours: dict[str, tuple[time, time]] = {
        PERIOD_MORNING: (edition.morning_start, edition.morning_end),
        PERIOD_AFTERNOON: (edition.afternoon_start, edition.afternoon_end),
        PERIOD_EVENING: (edition.evening_start, edition.evening_end),
    }
    for day in sorted(wanted_days):
        for period, (start, end) in hours.items():
            slot = existing.get((day, period))
            if slot is None:
                slot = Slot(edition_id=edition.id, date=day, period=period)
                db.add(slot)
            slot.start_time, slot.end_time = start, end
            # The evening has no seat limit.
            slot.capacity = None if period == PERIOD_EVENING else edition.default_capacity
    db.flush()


def ensure_payment_channels(db: Session, edition: Edition) -> None:
    present = set(
        db.scalars(select(PaymentChannel.code).where(PaymentChannel.edition_id == edition.id))
    )
    for order, (code, label) in enumerate(PAYMENT_CHANNELS.items()):
        if code not in present:
            db.add(
                PaymentChannel(
                    edition_id=edition.id, code=code, label=label, sort_order=order, enabled=False
                )
            )
    db.flush()


def save_edition(db: Session, values: dict) -> Edition:
    """Create the active edition or update it, then align slots and payment channels."""
    edition = get_active_edition(db)
    if edition is None:
        edition = Edition(is_active=True)
        db.add(edition)
    for key, value in values.items():
        setattr(edition, key, value)
    db.flush()
    db.refresh(edition)
    try:
        sync_slots(db, edition)
    except SlotsInUseError:
        db.rollback()
        raise
    ensure_payment_channels(db, edition)
    db.commit()
    db.refresh(edition)
    return edition


def list_channels(db: Session, edition: Edition) -> list[PaymentChannel]:
    return list(
        db.scalars(
            select(PaymentChannel)
            .where(PaymentChannel.edition_id == edition.id)
            .order_by(PaymentChannel.sort_order, PaymentChannel.id)
        )
    )


def latest_legal_document(db: Session, edition: Edition, kind: str) -> LegalDocument | None:
    return db.scalar(
        select(LegalDocument)
        .where(LegalDocument.edition_id == edition.id, LegalDocument.kind == kind)
        .order_by(LegalDocument.version.desc())
    )


def publish_legal_document(db: Session, edition: Edition, kind: str, body: str) -> LegalDocument:
    """Publish a new version. Older versions stay, because bookings reference what was accepted."""
    current = db.scalar(
        select(func.max(LegalDocument.version)).where(
            LegalDocument.edition_id == edition.id, LegalDocument.kind == kind
        )
    )
    document = LegalDocument(
        edition_id=edition.id, kind=kind, version=(current or 0) + 1, body=body
    )
    db.add(document)
    db.commit()
    return document
