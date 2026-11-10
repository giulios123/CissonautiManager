"""What external guests owe and pay (MVP 25b).

A guest has no booking: the amount due is read from the current prices of their meals and
activities each time, so a price or destination change needs no recalculation. Payments and
refunds sit in their own register and never touch a booking. Admins only; no email is sent.
"""

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.external import (
    MOVEMENT_REFUND,
    GuestAccount,
    Movement,
    can_void,
    check_movement,
    guest_account,
    guest_due_cents,
)
from app.models import Edition, ExternalGuest, ExternalMovement, Participant
from app.services import audit
from app.services.activities import activity_sort_key
from app.services.amounts import activity_terms, meal_terms
from app.services.seats import lock_edition
from app.timefmt import format_activity, format_euro, format_meal


class MovementRefused(Exception):
    def __init__(self, reason: str):
        self.reason = reason  # "invalid_amount" or "refund_too_high"


class MovementRequestConflict(Exception):
    """The same request key came back with different data."""


class MovementNotFound(Exception):
    pass


class AlreadyVoided(Exception):
    pass


class VoidBlocked(Exception):
    """Voiding this payment would leave more refunded than paid."""


@dataclass(frozen=True)
class Item:
    label: str
    price_cents: int
    collectable_cents: int  # 0 when the provider is paid directly


def items_of(edition: Edition, guest: ExternalGuest, locale: str | None = None) -> list[Item]:
    """The meals and activities of the guest with what the organisation collects for each."""
    items: list[Item] = []
    for meal in sorted(guest.meals, key=lambda m: (m.date, m.kind != "lunch")):
        terms = meal_terms(edition, meal.date, meal.kind)
        items.append(
            Item(
                format_meal(meal.date, meal.kind, locale),
                terms["price_cents"],
                terms["collectable_cents"],
            )
        )
    for activity in sorted(guest.activities, key=activity_sort_key):
        terms = activity_terms(activity)
        items.append(
            Item(
                format_activity(activity.title, activity.date, activity.period, locale),
                terms["price_cents"],
                terms["collectable_cents"],
            )
        )
    return items


def movements_of(db: Session, guest: ExternalGuest) -> list[ExternalMovement]:
    return list(
        db.scalars(
            select(ExternalMovement)
            .where(ExternalMovement.guest_id == guest.id)
            .order_by(ExternalMovement.id)
        )
    )


def movements_by_guest(db: Session, edition: Edition) -> dict[int, list[ExternalMovement]]:
    """Every movement of the edition grouped by guest, in one query: lists and the report would
    otherwise ask once per guest."""
    grouped: dict[int, list[ExternalMovement]] = {}
    for movement in db.scalars(
        select(ExternalMovement)
        .where(ExternalMovement.edition_id == edition.id)
        .order_by(ExternalMovement.id)
    ):
        grouped.setdefault(movement.guest_id, []).append(movement)
    return grouped


def account_of(
    edition: Edition, guest: ExternalGuest, movements: list[ExternalMovement]
) -> GuestAccount:
    due = guest_due_cents(guest.payer, (i.collectable_cents for i in items_of(edition, guest)))
    return guest_account(
        due, [Movement(m.kind, m.amount_cents, m.voided_at is not None) for m in movements]
    )


def has_movements(db: Session, guest: ExternalGuest) -> bool:
    return (
        db.scalar(select(ExternalMovement.id).where(ExternalMovement.guest_id == guest.id).limit(1))
        is not None
    )


def _describe(guest: ExternalGuest) -> str:
    return f"{guest.first_name} {guest.last_name}"


def record_movement(
    db: Session,
    admin: Participant,
    edition: Edition,
    guest: ExternalGuest,
    kind: str,
    amount_cents: int,
    channel: str,
    paid_on: date,
    note: str | None,
    now: datetime,
    request_key: str | None = None,
) -> tuple[ExternalMovement, bool]:
    """Record a payment or a refund. Returns the movement and whether it was already there (the
    same request sent twice)."""
    lock_edition(db, edition.id)
    db.refresh(guest)
    if request_key is not None:
        existing = db.scalar(
            select(ExternalMovement).where(ExternalMovement.request_key == request_key)
        )
        if existing is not None:
            if (
                existing.guest_id != guest.id
                or existing.kind != kind
                or existing.amount_cents != amount_cents
                or existing.channel != channel
                or existing.paid_on != paid_on
                or existing.note != (note or None)
                or existing.recorded_by_id != admin.id
            ):
                raise MovementRequestConflict()
            return existing, True
    refusal = check_movement(
        kind, amount_cents, account_of(edition, guest, movements_of(db, guest))
    )
    if refusal is not None:
        raise MovementRefused(refusal)
    movement = ExternalMovement(
        edition_id=edition.id,
        guest_id=guest.id,
        kind=kind,
        amount_cents=amount_cents,
        channel=channel,
        paid_on=paid_on,
        note=note or None,
        recorded_by_id=admin.id,
        created_at=now,
        request_key=request_key,
    )
    db.add(movement)
    action = "guest_refund" if kind == MOVEMENT_REFUND else "guest_payment"
    verb = "Restituzione" if kind == MOVEMENT_REFUND else "Pagamento"
    audit.log(
        db,
        admin,
        action,
        f"{verb} di {format_euro(amount_cents)} ({channel}) per {_describe(guest)}",
    )
    db.commit()
    return movement, False


def void_movement(
    db: Session,
    admin: Participant,
    edition: Edition,
    movement_id: int,
    reason: str,
    now: datetime,
) -> ExternalGuest:
    """Void a movement with a reason. It stays on record and stops counting."""
    lock_edition(db, edition.id)
    movement = db.get(ExternalMovement, movement_id)
    if movement is None or movement.edition_id != edition.id:
        raise MovementNotFound()
    db.refresh(movement)
    if movement.voided_at is not None:
        raise AlreadyVoided()
    guest = db.get(ExternalGuest, movement.guest_id)
    assert guest is not None
    account = account_of(edition, guest, movements_of(db, guest))
    if not can_void(movement.kind, movement.amount_cents, account):
        raise VoidBlocked()
    movement.voided_at = now
    movement.voided_by_id = admin.id
    movement.void_reason = reason
    what = "restituzione" if movement.kind == MOVEMENT_REFUND else "pagamento"
    audit.log(
        db,
        admin,
        "guest_movement_voided",
        f"Annullata {what} di {format_euro(movement.amount_cents)} "
        f"per {_describe(guest)}: {reason}",
    )
    db.commit()
    return guest
