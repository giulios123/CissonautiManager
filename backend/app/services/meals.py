"""Lunch and dinner sign-ups of a booking."""

from collections.abc import Iterable
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.domain.booking import can_edit_slots, effective_status, is_past_day
from app.domain.meals import (
    Meal,
    allowed_meals,
    check_meal_change,
    meal_sort_key,
    periods_by_day,
)
from app.email import EmailSender
from app.models import STATUS_CONFIRMED, STATUS_PENDING, Booking, BookingMeal, Edition, Participant
from app.services import audit
from app.services.amounts import confirmation_covered, recompute_amount
from app.services.booking_changes import ChangeResult, NotEditable
from app.services.payments import (
    paid_total,
    queue_confirmation_notice,
    send_transition_confirmation,
)
from app.services.seats import expire_overdue, lock_booking
from app.timefmt import format_euro, format_meal


class MealsRefused(Exception):
    def __init__(self, reason: str, meals: tuple[Meal, ...]) -> None:
        self.reason = reason
        self.meals = meals
        super().__init__(reason)


def meals_of(booking: Booking) -> set[Meal]:
    return {(m.date, m.kind) for m in booking.meals}


def allowed_for(booking: Booking) -> set[Meal]:
    return allowed_meals(periods_by_day((s.date, s.period) for s in booking.slots))


def change_meals(
    db: Session,
    sender: EmailSender,
    booking: Booking,
    wanted: Iterable[Meal],
    now: datetime,
    allow_past: bool = False,
    actor: Participant | None = None,
) -> ChangeResult:
    """Replace the meals of a pending or confirmed booking and recompute the amount.

    Same rules as a change of slots (D-017): the hold does not move, a confirmed booking stays
    confirmed, a pending one already covered by its payments becomes confirmed. `allow_past`
    and `actor` are for admins.
    """
    expire_overdue(db, now)
    # Lock first, then read: a cancellation committed in between must be seen (as in
    # record_payment), or a cancelled booking could be edited and even confirmed again.
    lock_booking(db, booking.id)
    db.refresh(booking)
    if not can_edit_slots(effective_status(booking.status, booking.hold_expires_at, now)):
        raise NotEditable()
    current = meals_of(booking)
    wanted_set = set(wanted)
    past_days = {day for day, _ in current | wanted_set if is_past_day(day, now)}
    check = check_meal_change(current, wanted_set, allowed_for(booking), past_days, allow_past)
    if not check.ok:
        assert check.reason is not None
        raise MealsRefused(check.reason, check.meals)

    edition = db.get(Edition, booking.edition_id)
    assert edition is not None
    old_amount = booking.amount_due_cents
    kept = [m for m in booking.meals if (m.date, m.kind) in wanted_set]
    added = sorted(wanted_set - current, key=meal_sort_key)
    booking.meals = kept + [BookingMeal(date=day, kind=kind) for day, kind in added]
    recompute_amount(edition, booking)
    if actor is not None:
        audit.log(
            db,
            actor,
            "meals_changed",
            _describe(
                added,
                sorted(current - wanted_set, key=meal_sort_key),
                old_amount,
                booking.amount_due_cents,
            ),
            booking.id,
        )
    total = paid_total(booking)
    confirmed_now = booking.status == STATUS_PENDING and confirmation_covered(
        edition, booking, total
    )
    if confirmed_now:
        booking.status = STATUS_CONFIRMED
        queue_confirmation_notice(booking, now)
    db.commit()
    if confirmed_now:
        send_transition_confirmation(db, sender, booking, total, now)
    return ChangeResult(booking, confirmed_now)


def _describe(
    added: list[tuple[date, str]], removed: list[tuple[date, str]], old: int, new: int
) -> str:
    parts = ["Pasti modificati."]
    if added:
        parts.append("Aggiunti: " + ", ".join(format_meal(d, k) for d, k in added) + ".")
    if removed:
        parts.append("Tolti: " + ", ".join(format_meal(d, k) for d, k in removed) + ".")
    parts.append(f"Quota: {format_euro(old)} → {format_euro(new)}.")
    return " ".join(parts)
