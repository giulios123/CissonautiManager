"""Preview and apply an edition's included-meal policy."""

import hashlib
import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.booking import effective_status
from app.models import (
    STATUS_CONFIRMED,
    STATUS_PENDING,
    Booking,
    Edition,
    Participant,
)
from app.services import audit
from app.services.amounts import calculate_amounts, confirmation_covered
from app.services.payments import paid_total, queue_confirmation_notice
from app.services.seats import lock_edition


class PreviewChanged(Exception):
    pass


class PolicyUnavailable(Exception):
    pass


def preview(db: Session, edition: Edition, policy: str, now: datetime) -> dict:
    if policy not in ("none", "first_organizer_meal"):
        raise PolicyUnavailable()
    lock_edition(db, edition.id)
    db.refresh(edition)
    if edition.confirmation_policy != "registration_fee":
        raise PolicyUnavailable()
    bookings = _load_bookings(db, edition.id)
    old_policy = edition.included_meal_policy
    original_flags = {
        booking.id: {(meal.date, meal.kind): meal.included_in_fee for meal in booking.meals}
        for booking in bookings
    }
    rows = []
    edition.included_meal_policy = policy
    for booking in bookings:
        status = effective_status(booking.status, booking.hold_expires_at, now)
        if status not in (STATUS_PENDING, STATUS_CONFIRMED):
            continue
        old_total = booking.amount_due_cents
        fee, total = calculate_amounts(edition, booking)
        included = next(
            ((meal.date.isoformat(), meal.kind) for meal in booking.meals if meal.included_in_fee),
            None,
        )
        paid = paid_total(booking)
        registration_fee = booking.registration_fee_cents
        booking.registration_fee_cents = fee
        status_after = (
            STATUS_CONFIRMED
            if status == STATUS_CONFIRMED or confirmation_covered(edition, booking, paid)
            else STATUS_PENDING
        )
        booking.registration_fee_cents = registration_fee
        rows.append(
            {
                "booking_id": booking.id,
                "name": f"{booking.participant.first_name} {booking.participant.last_name}",
                "status_before": status,
                "status_after": status_after,
                "included_meal": included,
                "registration_fee_cents": fee,
                "amount_due_cents": total,
                "paid_cents": paid,
                "balance_before_cents": old_total - paid,
                "balance_after_cents": total - paid,
            }
        )
    for booking in bookings:
        for meal in booking.meals:
            meal.included_in_fee = original_flags[booking.id][(meal.date, meal.kind)]
    edition.included_meal_policy = old_policy
    token = _fingerprint(edition, bookings, policy, now)
    return {
        "current_policy": old_policy,
        "proposed_policy": policy,
        "preview_token": token,
        "rows": rows,
    }


def apply(
    db: Session, edition: Edition, actor: Participant, policy: str, token: str, now: datetime
) -> dict:
    lock_edition(db, edition.id)
    db.refresh(edition)
    if edition.included_meal_preview_token == token and edition.included_meal_policy == policy:
        return {"already_applied": True, "updated_bookings": 0}
    current = preview(db, edition, policy, now)
    if current["preview_token"] != token:
        raise PreviewChanged()
    bookings = _load_bookings(db, edition.id)
    edition.included_meal_policy = policy
    count = 0
    for booking in bookings:
        status = effective_status(booking.status, booking.hold_expires_at, now)
        if status not in (STATUS_PENDING, STATUS_CONFIRMED):
            continue
        old = booking.amount_due_cents
        booking.registration_fee_cents, booking.amount_due_cents = calculate_amounts(
            edition, booking
        )
        if status == STATUS_PENDING and confirmation_covered(edition, booking, paid_total(booking)):
            booking.status = STATUS_CONFIRMED
            queue_confirmation_notice(booking, now)
        audit.log(
            db,
            actor,
            "included_meal_policy_applied",
            f"Policy {policy}; totale {old} → {booking.amount_due_cents} centesimi.",
            booking.id,
        )
        count += 1
    edition.included_meal_preview_token = token
    db.commit()
    return {"already_applied": False, "updated_bookings": count}


def _load_bookings(db: Session, edition_id: int) -> list[Booking]:
    db.execute(
        select(Booking.id)
        .where(Booking.edition_id == edition_id)
        .order_by(Booking.id)
        .with_for_update()
        .with_hint(Booking, "WITH (UPDLOCK, HOLDLOCK)", "mssql")
    )
    return list(
        db.scalars(
            select(Booking)
            .where(Booking.edition_id == edition_id)
            .order_by(Booking.id)
            .options(
                selectinload(Booking.participant),
                selectinload(Booking.slots),
                selectinload(Booking.meals),
                selectinload(Booking.activities),
                selectinload(Booking.payments),
                selectinload(Booking.refunds),
            )
            .execution_options(populate_existing=True)
        )
    )


def _fingerprint(edition: Edition, bookings: list[Booking], policy: str, now: datetime) -> str:
    data = [
        policy,
        edition.included_meal_policy,
        edition.confirmation_policy,
        edition.base_fee_cents,
        edition.per_day_fee_cents,
        edition.lunch_price_cents,
        edition.dinner_price_cents,
        sorted(
            (
                setting.date.isoformat(),
                setting.kind,
                setting.payment_mode,
                setting.price_cents,
            )
            for setting in edition.meal_settings
        ),
    ]
    for booking in bookings:
        data.append(
            [
                booking.id,
                booking.status,
                effective_status(booking.status, booking.hold_expires_at, now),
                booking.hold_expires_at.isoformat(),
                booking.amount_due_cents,
                booking.registration_fee_cents,
                booking.refund_cents,
                sorted((slot.date.isoformat(), slot.period) for slot in booking.slots),
                sorted((m.date.isoformat(), m.kind) for m in booking.meals),
                sorted(
                    (activity.id, activity.price_cents, activity.payment_mode)
                    for activity in booking.activities
                ),
                sorted(
                    (
                        p.id,
                        p.amount_cents,
                        p.voided_at.isoformat() if p.voided_at else None,
                    )
                    for p in booking.payments
                ),
                sorted(
                    (r.id, r.amount_cents, r.voided_at.isoformat() if r.voided_at else None)
                    for r in booking.refunds
                ),
                [
                    booking.fee_exempt,
                    sorted((m.date.isoformat(), m.kind) for m in booking.meals if m.exempt),
                    sorted(link.activity_id for link in booking.activity_links if link.exempt),
                ],
            ]
        )
    return hashlib.sha256(json.dumps(data, separators=(",", ":")).encode()).hexdigest()
