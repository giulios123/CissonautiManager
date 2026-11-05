from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    Time,
    Unicode,
    UnicodeText,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, UtcDateTime, utcnow

# String constants for enum-like columns. Stored as short strings, validated in the domain layer.
ROLE_PARTICIPANT = "participant"
ROLE_ADMIN = "admin"

PERIOD_MORNING = "morning"
PERIOD_AFTERNOON = "afternoon"
PERIOD_EVENING = "evening"

STATUS_PENDING = "in_attesa_pagamento"
STATUS_CONFIRMED = "confermata"
STATUS_EXPIRED = "scaduta"
STATUS_CANCEL_REQUESTED = "disdetta_richiesta"
STATUS_REFUNDED = "rimborsata"

DOC_PRIVACY = "privacy"
DOC_DISCLAIMER = "disclaimer"


class Edition(Base):
    __tablename__ = "edition"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Unicode(200))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    morning_start: Mapped[time] = mapped_column(Time, default=time(9, 0))
    morning_end: Mapped[time] = mapped_column(Time, default=time(13, 0))
    afternoon_start: Mapped[time] = mapped_column(Time, default=time(14, 0))
    afternoon_end: Mapped[time] = mapped_column(Time, default=time(18, 0))
    # Evening runs until midnight: an end time of 00:00 means the end of the day.
    evening_start: Mapped[time] = mapped_column(Time, default=time(19, 0))
    evening_end: Mapped[time] = mapped_column(Time, default=time(0, 0))
    default_capacity: Mapped[int] = mapped_column(Integer, default=25)
    hold_days: Mapped[int] = mapped_column(Integer, default=3)
    base_fee_cents: Mapped[int] = mapped_column(Integer, default=1000)
    per_day_fee_cents: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    slots: Mapped[list["Slot"]] = relationship(back_populates="edition")


class Slot(Base):
    __tablename__ = "slot"
    __table_args__ = (UniqueConstraint("edition_id", "date", "period"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    edition_id: Mapped[int] = mapped_column(ForeignKey("edition.id"))
    date: Mapped[date] = mapped_column(Date)
    period: Mapped[str] = mapped_column(Unicode(12))
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    # None means no limit (the evening slot).
    capacity: Mapped[int | None] = mapped_column(Integer)

    edition: Mapped[Edition] = relationship(back_populates="slots")


class Participant(Base):
    __tablename__ = "participant"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(Unicode(100))
    last_name: Mapped[str] = mapped_column(Unicode(100))
    email: Mapped[str] = mapped_column(Unicode(320), unique=True)
    phone: Mapped[str | None] = mapped_column(Unicode(50))
    invited_by: Mapped[str | None] = mapped_column(Unicode(200))
    can_bring: Mapped[str | None] = mapped_column(UnicodeText)
    personal_code: Mapped[str] = mapped_column(Unicode(16), unique=True)
    role: Mapped[str] = mapped_column(Unicode(16), default=ROLE_PARTICIPANT)
    password_hash: Mapped[str | None] = mapped_column(Unicode(255))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)


class LegalDocument(Base):
    __tablename__ = "legal_document"
    __table_args__ = (UniqueConstraint("edition_id", "kind", "version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    edition_id: Mapped[int] = mapped_column(ForeignKey("edition.id"))
    kind: Mapped[str] = mapped_column(Unicode(16))
    version: Mapped[int] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(UnicodeText)
    published_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)


class Booking(Base):
    __tablename__ = "booking"

    id: Mapped[int] = mapped_column(primary_key=True)
    edition_id: Mapped[int] = mapped_column(ForeignKey("edition.id"))
    participant_id: Mapped[int] = mapped_column(ForeignKey("participant.id"))
    status: Mapped[str] = mapped_column(Unicode(32), default=STATUS_PENDING)
    hold_expires_at: Mapped[datetime] = mapped_column(UtcDateTime)
    # Start of the current hold. Changes only when an expired booking is reactivated, because
    # payment reminders are relative to the hold, not to the creation of the booking.
    hold_started_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)
    reminder_mid_sent_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    reminder_final_sent_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    cancel_requested_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    refund_cents: Mapped[int | None] = mapped_column(Integer)
    refunded_on: Mapped[date | None] = mapped_column(Date)
    refund_note: Mapped[str | None] = mapped_column(UnicodeText)
    refunded_by_id: Mapped[int | None] = mapped_column(ForeignKey("participant.id"))
    amount_due_cents: Mapped[int] = mapped_column(Integer)
    privacy_document_id: Mapped[int] = mapped_column(ForeignKey("legal_document.id"))
    privacy_accepted_at: Mapped[datetime] = mapped_column(UtcDateTime)
    disclaimer_document_id: Mapped[int] = mapped_column(ForeignKey("legal_document.id"))
    disclaimer_accepted_at: Mapped[datetime] = mapped_column(UtcDateTime)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)

    participant: Mapped[Participant] = relationship(foreign_keys=[participant_id])
    slots: Mapped[list[Slot]] = relationship(secondary="booking_slot")
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="booking", order_by="Payment.id"
    )


class BookingSlot(Base):
    __tablename__ = "booking_slot"

    booking_id: Mapped[int] = mapped_column(ForeignKey("booking.id"), primary_key=True)
    slot_id: Mapped[int] = mapped_column(ForeignKey("slot.id"), primary_key=True)


class PaymentChannel(Base):
    __tablename__ = "payment_channel"
    __table_args__ = (UniqueConstraint("edition_id", "code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    edition_id: Mapped[int] = mapped_column(ForeignKey("edition.id"))
    code: Mapped[str] = mapped_column(Unicode(32))
    label: Mapped[str] = mapped_column(Unicode(100))
    instructions: Mapped[str] = mapped_column(UnicodeText, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Payment(Base):
    __tablename__ = "payment"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("booking.id"))
    amount_cents: Mapped[int] = mapped_column(Integer)
    channel: Mapped[str] = mapped_column(Unicode(32))
    paid_on: Mapped[date] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(UnicodeText)
    recorded_by_id: Mapped[int] = mapped_column(ForeignKey("participant.id"))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)
    # A payment entered by mistake is voided, never deleted: it stays visible but does not count.
    voided_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    voided_by_id: Mapped[int | None] = mapped_column(ForeignKey("participant.id"))
    void_reason: Mapped[str | None] = mapped_column(UnicodeText)

    booking: Mapped[Booking] = relationship(back_populates="payments")


class MagicLinkToken(Base):
    __tablename__ = "magic_link_token"

    id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participant.id"))
    token_hash: Mapped[str] = mapped_column(Unicode(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime)
    used_at: Mapped[datetime | None] = mapped_column(UtcDateTime)


class AuthSession(Base):
    __tablename__ = "auth_session"

    id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participant.id"))
    token_hash: Mapped[str] = mapped_column(Unicode(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)


class AuditLog(Base):
    """What an admin changed by hand. `booking_id` is deliberately not a foreign key: the history
    must outlive a booking that gets removed."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)
    actor_id: Mapped[int] = mapped_column(ForeignKey("participant.id"))
    booking_id: Mapped[int | None] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(Unicode(40))
    detail: Mapped[str] = mapped_column(UnicodeText, default="")


def active_payments(booking: Booking) -> list[Payment]:
    """Payments that count: voided ones stay on record but are ignored everywhere."""
    return [p for p in booking.payments if p.voided_at is None]


def slot_sort_key(slot: Slot) -> tuple[date, time]:
    """Chronological order: by day, then by start time (so morning comes before afternoon)."""
    return (slot.date, slot.start_time)
