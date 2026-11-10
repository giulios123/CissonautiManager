"""Preview and atomically apply the edition's registration-fee confirmation policy."""

import hashlib
import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.booking import effective_status
from app.domain.confirmation import (
    POLICY_LEGACY_TOTAL,
    POLICY_REGISTRATION_FEE,
)
from app.models import (
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    Booking,
    Edition,
    EmailTemplate,
    Participant,
    Slot,
    WaitlistEntry,
    active_payments,
)
from app.services import audit
from app.services.amounts import calculate_amounts
from app.services.payments import paid_total, queue_confirmation_notice
from app.services.seats import lock_edition
from app.timefmt import format_euro

EMAIL_TEMPLATES_TO_REVIEW = (
    "registration",
    "payment_confirmation",
    "booking_confirmation",
    "reminder_mid",
    "reminder_final",
    "waitlist_promoted",
)


class PreviewOutOfDate(Exception):
    pass


class PolicyAlreadyActive(Exception):
    pass


class PreviewNotReady(Exception):
    pass


def preview(db: Session, edition: Edition, now: datetime) -> dict:
    """Read a coherent, non-writing preview while holding the edition and booking locks."""
    lock_edition(db, edition.id)
    db.refresh(edition)
    bookings = _lock_and_load_bookings(db, edition.id)
    return _build_preview(db, edition, bookings, now)


def activate(
    db: Session,
    edition: Edition,
    actor: Participant,
    now: datetime,
    preview_token: str,
) -> dict:
    """Recheck the preview under locks and apply all active reprices in one commit."""
    lock_edition(db, edition.id)
    db.refresh(edition)

    if edition.confirmation_policy == POLICY_REGISTRATION_FEE:
        if edition.confirmation_policy_preview_token == preview_token:
            return {
                "already_applied": True,
                "activated_at": edition.confirmation_policy_activated_at,
                "updated_bookings": 0,
                "new_confirmations": 0,
                "transferred_notices": 0,
            }
        raise PolicyAlreadyActive()
    if edition.confirmation_policy != POLICY_LEGACY_TOTAL:
        raise PolicyAlreadyActive()

    bookings = _lock_and_load_bookings(db, edition.id)
    current = _build_preview(db, edition, bookings, now)
    if not current["ready"]:
        raise PreviewNotReady()
    if current["preview_token"] != preview_token:
        raise PreviewOutOfDate()

    edition.confirmation_policy = POLICY_REGISTRATION_FEE
    changed = 0
    newly_confirmed = 0
    transferred_notices = 0
    for row in current["_rows"]:
        booking = row["booking"]
        old_fee = booking.registration_fee_cents
        old_total = booking.amount_due_cents
        booking.registration_fee_cents = row["registration_fee_cents"]
        booking.amount_due_cents = row["amount_due_cents"]
        if row["status_after"] == STATUS_CONFIRMED and booking.status != STATUS_CONFIRMED:
            booking.status = STATUS_CONFIRMED
            queue_confirmation_notice(booking, now)
            newly_confirmed += 1
        elif row["transfer_legacy_notice"]:
            queue_confirmation_notice(
                booking,
                now,
                payment_id=row["legacy_notice_payment_id"],
                due_at=row["legacy_notice_due_at"],
            )
            for payment in booking.payments:
                if payment.id == row["legacy_notice_payment_id"]:
                    payment.confirmation_email_due_at = None
                    break
            transferred_notices += 1
        detail = (
            "Attivata conferma sulla quota: "
            f"quota {format_euro(old_fee) if old_fee is not None else 'non salvata'} → "
            f"{format_euro(booking.registration_fee_cents)}, totale "
            f"{format_euro(old_total)} → {format_euro(booking.amount_due_cents)}, "
            f"saldo {format_euro(old_total - row['paid_cents'])} → "
            f"{format_euro(booking.amount_due_cents - row['paid_cents'])}."
        )
        audit.log(db, actor, "confirmation_policy_activated", detail, booking.id)
        changed += 1

    edition.confirmation_policy_activated_at = now
    edition.confirmation_policy_preview_token = preview_token
    audit.log(
        db,
        actor,
        "confirmation_policy_activated",
        f"Attivata la conferma sulla quota per {changed} prenotazioni; "
        f"{newly_confirmed} nuove conferme.",
    )
    db.commit()
    return {
        "already_applied": False,
        "activated_at": now,
        "updated_bookings": changed,
        "new_confirmations": newly_confirmed,
        "transferred_notices": transferred_notices,
    }


def _lock_and_load_bookings(db: Session, edition_id: int) -> list[Booking]:
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


def _build_preview(db: Session, edition: Edition, bookings: list[Booking], now: datetime) -> dict:
    rows = []
    fingerprint_bookings = []
    expired = 0
    closed = 0
    blockers: list[dict] = []
    for booking in bookings:
        status = effective_status(booking.status, booking.hold_expires_at, now)
        if status not in (STATUS_PENDING, STATUS_CONFIRMED):
            if status == STATUS_EXPIRED:
                expired += 1
            else:
                closed += 1
            continue
        if not booking.slots or any(slot.edition_id != edition.id for slot in booking.slots):
            blockers.append(
                {
                    "booking_id": booking.id,
                    "name": f"{booking.participant.first_name} {booking.participant.last_name}",
                    "reason": "invalid_slots",
                }
            )
            continue

        registration_fee, amount_due = calculate_amounts(edition, booking)
        if (
            registration_fee < 0
            or amount_due < registration_fee
            or any(payment.amount_cents <= 0 for payment in active_payments(booking))
        ):
            blockers.append(
                {
                    "booking_id": booking.id,
                    "name": f"{booking.participant.first_name} {booking.participant.last_name}",
                    "reason": "invalid_amounts",
                }
            )
            continue
        paid = paid_total(booking)
        pending_notice = next(
            (
                payment
                for payment in sorted(
                    active_payments(booking),
                    key=lambda item: (item.confirmation_email_due_at or now, item.id),
                )
                if payment.confirmation_email_due_at is not None
                and payment.confirmation_email_sent_at is None
            ),
            None,
        )
        transfer_legacy_notice = status == STATUS_CONFIRMED and pending_notice is not None
        status_after = (
            STATUS_CONFIRMED
            if status == STATUS_CONFIRMED or paid >= registration_fee
            else STATUS_PENDING
        )
        row = {
            "booking": booking,
            "booking_id": booking.id,
            "name": f"{booking.participant.first_name} {booking.participant.last_name}",
            "email": booking.participant.email,
            "status_before": status,
            "status_after": status_after,
            "registration_fee_cents": registration_fee,
            "amount_due_cents": amount_due,
            "paid_cents": paid,
            "balance_before_cents": booking.amount_due_cents - paid,
            "balance_after_cents": amount_due - paid,
            "confirmation_balance_after_cents": max(0, registration_fee - paid)
            if status_after == STATUS_PENDING
            else 0,
            "sends_confirmation": status == STATUS_PENDING and status_after == STATUS_CONFIRMED,
            "legacy_notice_payment_id": pending_notice.id if transfer_legacy_notice else None,
            "legacy_notice_due_at": (
                pending_notice.confirmation_email_due_at if transfer_legacy_notice else None
            ),
            "transfer_legacy_notice": transfer_legacy_notice,
        }
        if transfer_legacy_notice:
            row["sends_confirmation"] = True
        rows.append(row)
        fingerprint_bookings.append(_booking_fingerprint(booking, status))

    waitlist_participants = set(
        db.scalars(
            select(WaitlistEntry.participant_id)
            .join(Slot, Slot.id == WaitlistEntry.slot_id)
            .where(Slot.edition_id == edition.id, WaitlistEntry.closed_at.is_(None))
            .distinct()
        )
    )
    participants_with_bookings = {booking.participant_id for booking in bookings}
    only_waitlisted = len(waitlist_participants - participants_with_bookings)
    email_templates = list(
        db.scalars(
            select(EmailTemplate)
            .where(
                EmailTemplate.edition_id == edition.id,
                EmailTemplate.kind.in_(EMAIL_TEMPLATES_TO_REVIEW),
            )
            .order_by(EmailTemplate.kind, EmailTemplate.locale)
            .with_for_update()
            .with_hint(EmailTemplate, "WITH (UPDLOCK, HOLDLOCK)", "mssql")
        )
    )
    custom_email_templates = [
        template
        for template in email_templates
        if (template.subject or "").strip() or (template.body or "").strip()
    ]
    payload = {
        "edition": _edition_fingerprint(edition),
        "bookings": fingerprint_bookings,
        "only_waitlisted": only_waitlisted,
        "email_templates": [
            {
                "kind": template.kind,
                "locale": template.locale,
                "subject": template.subject,
                "body": template.body,
            }
            for template in email_templates
        ],
    }
    token = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    public_rows = [{k: v for k, v in row.items() if k != "booking"} for row in rows]
    return {
        "current_policy": edition.confirmation_policy,
        "proposed_policy": POLICY_REGISTRATION_FEE,
        "ready": not blockers and edition.confirmation_policy == POLICY_LEGACY_TOTAL,
        "already_active": edition.confirmation_policy == POLICY_REGISTRATION_FEE,
        "preview_token": token if not blockers else None,
        "eligible_count": len(rows),
        "excluded_expired_count": expired,
        "excluded_closed_count": closed,
        "waitlist_only_count": only_waitlisted,
        "new_confirmation_count": sum(row["sends_confirmation"] for row in rows),
        "email_templates_to_review": [
            {"kind": template.kind, "locale": template.locale}
            for template in custom_email_templates
        ],
        "blockers": blockers,
        "rows": public_rows,
        "_rows": rows,
    }


def _edition_fingerprint(edition: Edition) -> dict:
    return {
        "id": edition.id,
        "policy": edition.confirmation_policy,
        "base_fee_cents": edition.base_fee_cents,
        "per_day_fee_cents": edition.per_day_fee_cents,
        "lunch_price_cents": edition.lunch_price_cents,
        "dinner_price_cents": edition.dinner_price_cents,
        "meal_settings": sorted(
            (
                setting.date.isoformat(),
                setting.kind,
                setting.price_cents,
                setting.payment_mode,
            )
            for setting in edition.meal_settings
        ),
    }


def _booking_fingerprint(booking: Booking, status: str) -> dict:
    return {
        "id": booking.id,
        "status": status,
        "stored_status": booking.status,
        "hold_expires_at": booking.hold_expires_at.isoformat(),
        "amount_due_cents": booking.amount_due_cents,
        "registration_fee_cents": booking.registration_fee_cents,
        "slots": sorted((s.id, s.date.isoformat(), s.period) for s in booking.slots),
        "meals": sorted((m.date.isoformat(), m.kind) for m in booking.meals),
        "activities": sorted(
            (a.id, a.price_cents, a.payment_mode, a.date.isoformat(), a.period)
            for a in booking.activities
        ),
        "payments": sorted(
            (
                p.id,
                p.amount_cents,
                p.voided_at.isoformat() if p.voided_at else None,
                p.confirmation_email_due_at.isoformat() if p.confirmation_email_due_at else None,
                p.confirmation_email_sent_at.isoformat() if p.confirmation_email_sent_at else None,
            )
            for p in booking.payments
        ),
        "refunds": sorted(
            (r.id, r.amount_cents, r.voided_at.isoformat() if r.voided_at else None)
            for r in booking.refunds
        ),
        "exemptions": [
            booking.category,
            booking.fee_exempt,
            sorted((m.date.isoformat(), m.kind) for m in booking.meals if m.exempt),
            sorted(link.activity_id for link in booking.activity_links if link.exempt),
        ],
        "notice_cycle": booking.confirmation_cycle,
        "claimed_cycle": booking.confirmation_claimed_cycle,
        "notice_due_at": (
            booking.confirmation_notice_due_at.isoformat()
            if booking.confirmation_notice_due_at
            else None
        ),
        "notice_payment_id": booking.confirmation_notice_payment_id,
    }
