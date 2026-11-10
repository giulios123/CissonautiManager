"""Category and exemptions of an active booking, with preview and apply (MVP 25c).

An admin exempts the fee and/or single meals and activities of one booking. Nothing is written
until the admin applies a preview that is still valid; the payments are never touched. A pending
booking that the new amounts leave covered is confirmed and gets its confirmation notice.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.booking import effective_status, occupies_seats
from app.domain.confirmation import confirmation_due_cents
from app.domain.exemptions import CATEGORIES, Exemptions
from app.domain.meals import Meal
from app.models import (
    STATUS_CONFIRMED,
    STATUS_PENDING,
    Booking,
    BookingActivity,
    Edition,
    Participant,
)
from app.services import audit
from app.services.amounts import calculate_amounts, calculate_meal_selection, exemptions_of
from app.services.payments import paid_total, queue_confirmation_notice
from app.services.seats import lock_booking, lock_edition
from app.timefmt import format_euro, status_label


class NotActive(Exception):
    """Exemptions apply to a pending or confirmed booking only."""


class InvalidChange(Exception):
    """An unknown category, or an item that is not on the booking."""


class PreviewChanged(Exception):
    """The booking changed after the preview was made."""


@dataclass(frozen=True)
class Change:
    category: str
    fee_exempt: bool = False
    meals: frozenset[Meal] = field(default_factory=frozenset)
    activities: frozenset[int] = field(default_factory=frozenset)

    @property
    def exemptions(self) -> Exemptions:
        return Exemptions(self.fee_exempt, self.meals, self.activities)


@dataclass
class ApplyResult:
    already_applied: bool
    confirmed_now: bool = False
    paid_cents: int = 0


def current_change(booking: Booking) -> Change:
    exempt = exemptions_of(booking)
    return Change(booking.category, exempt.fee, exempt.meals, exempt.activities)


def _validate(booking: Booking, change: Change) -> None:
    if change.category not in CATEGORIES:
        raise InvalidChange()
    on_booking_meals = {(m.date, m.kind) for m in booking.meals}
    on_booking_activities = {a.id for a in booking.activities}
    if not change.meals <= on_booking_meals or not change.activities <= on_booking_activities:
        raise InvalidChange()


def _status(booking: Booking, now: datetime) -> str:
    status = effective_status(booking.status, booking.hold_expires_at, now)
    if not occupies_seats(status):
        raise NotActive()
    return status


def preview(db: Session, booking: Booking, change: Change, now: datetime) -> dict:
    """The amounts and the status after the change, without writing anything."""
    db.refresh(booking)
    status = _status(booking, now)
    _validate(booking, change)
    edition = booking.edition
    meals = [(m.date, m.kind) for m in booking.meals]
    fee, total, included = calculate_meal_selection(edition, booking, meals, change.exemptions)
    paid = paid_total(booking)
    due_after = confirmation_due_cents(edition.confirmation_policy, total, fee)
    covered = due_after is not None and paid >= due_after
    status_after = STATUS_CONFIRMED if status == STATUS_CONFIRMED or covered else STATUS_PENDING
    return {
        "booking_id": booking.id,
        "category": change.category,
        "fee_exempt": change.fee_exempt,
        "exempt_meals": sorted((d.isoformat(), k) for d, k in change.meals),
        "exempt_activities": sorted(change.activities),
        "included_meal": (included[0].isoformat(), included[1]) if included else None,
        "status_before": status,
        "status_after": status_after,
        "registration_fee_before_cents": booking.registration_fee_cents,
        "registration_fee_after_cents": fee,
        "amount_due_before_cents": booking.amount_due_cents,
        "amount_due_after_cents": total,
        "paid_cents": paid,
        "balance_before_cents": booking.amount_due_cents - paid,
        "balance_after_cents": total - paid,
        "preview_token": _fingerprint(edition, booking, status, change),
    }


def apply(
    db: Session,
    admin: Participant,
    booking: Booking,
    change: Change,
    token: str,
    now: datetime,
) -> ApplyResult:
    """Apply a valid preview in one transaction. Applying the same preview again does nothing."""
    edition = booking.edition
    lock_edition(db, edition.id)
    lock_booking(db, booking.id)
    db.refresh(booking)
    if booking.exemption_preview_token == token and current_change(booking) == change:
        return ApplyResult(already_applied=True)
    current = preview(db, booking, change, now)
    if current["preview_token"] != token:
        raise PreviewChanged()
    status = _status(booking, now)
    before = (booking.registration_fee_cents, booking.amount_due_cents)
    old_change = current_change(booking)

    booking.category = change.category
    booking.fee_exempt = change.fee_exempt
    for meal in booking.meals:
        meal.exempt = (meal.date, meal.kind) in change.meals
    for activity in booking.activities:
        link = db.get(BookingActivity, (booking.id, activity.id))
        assert link is not None
        link.exempt = activity.id in change.activities
    db.flush()
    booking.registration_fee_cents, booking.amount_due_cents = calculate_amounts(edition, booking)

    paid = paid_total(booking)
    confirmed_now = False
    if status == STATUS_PENDING and _covered(edition, booking, paid):
        booking.status = STATUS_CONFIRMED
        queue_confirmation_notice(booking, now)
        confirmed_now = True
    booking.exemption_preview_token = token
    audit.log(
        db,
        admin,
        "exemptions_applied",
        _describe(old_change, change, before, booking, status, booking.status),
        booking.id,
    )
    db.commit()
    return ApplyResult(already_applied=False, confirmed_now=confirmed_now, paid_cents=paid)


def set_category(db: Session, admin: Participant, booking: Booking, category: str) -> None:
    """The category is a label: it changes no amount, so it needs no preview."""
    if category not in CATEGORIES:
        raise InvalidChange()
    if booking.category == category:
        return
    audit.log(
        db,
        admin,
        "category_changed",
        f"Categoria: {_category_name(booking.category)} → {_category_name(category)}",
        booking.id,
    )
    booking.category = category
    db.commit()


def _covered(edition: Edition, booking: Booking, paid: int) -> bool:
    due = confirmation_due_cents(
        edition.confirmation_policy, booking.amount_due_cents, booking.registration_fee_cents
    )
    return due is not None and paid >= due


def _category_name(category: str) -> str:
    return "interno non pagante" if category == "internal_non_paying" else "ordinaria"


def _describe(
    old: Change, new: Change, before: tuple, booking: Booking, status_before: str, status_after: str
) -> str:
    parts = [f"Esenzioni modificate. Quota esente: {'sì' if new.fee_exempt else 'no'}"]
    parts.append(f"pasti esenti: {len(new.meals)}, attività esenti: {len(new.activities)}")
    if old.category != new.category:
        parts.append(f"categoria {_category_name(old.category)} → {_category_name(new.category)}")
    parts.append(f"totale {format_euro(before[1])} → {format_euro(booking.amount_due_cents)}")
    if status_before != status_after:
        parts.append(f"stato {status_label(status_before)} → {status_label(status_after)}")
    return "; ".join(parts) + "."


def _fingerprint(edition: Edition, booking: Booking, status: str, change: Change) -> str:
    data = [
        [
            edition.id,
            edition.confirmation_policy,
            edition.included_meal_policy,
            edition.base_fee_cents,
            edition.per_day_fee_cents,
            edition.lunch_price_cents,
            edition.dinner_price_cents,
            sorted(
                (s.date.isoformat(), s.kind, s.price_cents, s.payment_mode)
                for s in edition.meal_settings
            ),
        ],
        [
            booking.id,
            status,
            booking.status,
            booking.hold_expires_at.isoformat(),
            booking.amount_due_cents,
            booking.registration_fee_cents,
            booking.category,
            booking.fee_exempt,
            sorted((s.date.isoformat(), s.period) for s in booking.slots),
            sorted((m.date.isoformat(), m.kind, m.exempt) for m in booking.meals),
            sorted(
                (a.id, a.price_cents, a.payment_mode, a.id in exemptions_of(booking).activities)
                for a in booking.activities
            ),
            sorted(
                (p.id, p.amount_cents, p.voided_at.isoformat() if p.voided_at else None)
                for p in booking.payments
            ),
            sorted(
                (r.id, r.amount_cents, r.voided_at.isoformat() if r.voided_at else None)
                for r in booking.refunds
            ),
        ],
        [
            change.category,
            change.fee_exempt,
            sorted((d.isoformat(), k) for d, k in change.meals),
            sorted(change.activities),
        ],
    ]
    return hashlib.sha256(json.dumps(data, separators=(",", ":")).encode()).hexdigest()
