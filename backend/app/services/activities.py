"""Activities created by the admins, seats and sign-ups."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.activities import (
    check_activity_delete,
    check_activity_edit,
    check_join,
    check_leave,
    is_eligible,
)
from app.domain.booking import (
    can_edit_slots,
    effective_status,
    has_free_seat,
    is_past_day,
    occupies_seats,
)
from app.domain.meals import periods_by_day
from app.email import EmailSender
from app.models import (
    PERIOD_AFTERNOON,
    PERIOD_EVENING,
    PERIOD_MORNING,
    STATUS_CONFIRMED,
    STATUS_PENDING,
    Activity,
    Booking,
    BookingActivity,
    Edition,
    ExternalGuestActivity,
    Participant,
)
from app.services import audit
from app.services.amounts import confirmation_covered, recompute_amount
from app.services.booking_changes import ChangeResult, NotEditable
from app.services.payments import (
    paid_total,
    queue_confirmation_notice,
    send_transition_confirmation,
)
from app.services.pricing import reprice
from app.services.seats import (
    activities_for_update,
    expire_overdue,
    free_by_activity,
    lock_booking,
    occupied_by_activity,
)
from app.timefmt import format_activity, format_euro

PERIOD_ORDER = {PERIOD_MORNING: 0, PERIOD_AFTERNOON: 1, PERIOD_EVENING: 2}


class ActivityNotFound(Exception):
    pass


class ActivityRefused(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


@dataclass
class ActivityData:
    title: str
    description: str | None
    date: date
    period: str
    time_label: str | None
    price_cents: int
    capacity: int | None
    title_it: str | None = None
    title_en: str | None = None
    description_it: str | None = None
    description_en: str | None = None
    internal_note: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    payment_mode: str = "organizer"
    payment_instructions: str | None = None


def activity_times(
    edition: Edition, day: date, period: str, start: time | None, end: time | None
) -> dict:
    if start is None or end is None:
        raise ActivityRefused("invalid_time")
    slot = next((s for s in edition.slots if (s.date, s.period) == (day, period)), None)

    def minute(t: time) -> int:
        return t.hour * 60 + t.minute

    start_minute, end_minute = minute(start), minute(end) or 1440
    if (
        slot is None
        or start.tzinfo is not None
        or end.tzinfo is not None
        or start.second
        or end.second
        or start.microsecond
        or end.microsecond
        or not minute(slot.start_time)
        <= start_minute
        < end_minute
        <= (minute(slot.end_time) or 1440)
    ):
        raise ActivityRefused("invalid_time")
    zone = ZoneInfo("Europe/Rome")
    ends = datetime.combine(day, end, zone) + (
        timedelta(days=1) if end_minute == 1440 else timedelta()
    )
    return dict(
        starts_at=datetime.combine(day, start, zone).astimezone(UTC),
        ends_at=ends.astimezone(UTC),
        time_label=f"{start:%H:%M}-{end:%H:%M}",
    )


def activity_sort_key(activity: Activity) -> tuple[date, int, str, int]:
    return (
        activity.date,
        PERIOD_ORDER.get(activity.period, 9),
        activity.title.lower(),
        activity.id,
    )


def list_activities(db: Session, edition: Edition) -> list[Activity]:
    activities = db.scalars(select(Activity).where(Activity.edition_id == edition.id)).all()
    return sorted(activities, key=activity_sort_key)


def get_activity(db: Session, edition: Edition, activity_id: int) -> Activity:
    activity = db.get(Activity, activity_id)
    if activity is None or activity.edition_id != edition.id:
        raise ActivityNotFound()
    return activity


def linked_count(db: Session, activity_id: int) -> int:
    """Bookings of any status that hold this activity (an expired one may come back), plus the
    external guests signed up."""
    bookings = (
        db.scalar(
            select(func.count())
            .select_from(BookingActivity)
            .where(BookingActivity.activity_id == activity_id)
        )
        or 0
    )
    guests = (
        db.scalar(
            select(func.count())
            .select_from(ExternalGuestActivity)
            .where(ExternalGuestActivity.activity_id == activity_id)
        )
        or 0
    )
    return bookings + guests


def participants(db: Session, activity: Activity, now: datetime) -> list[tuple[Booking, str]]:
    """Bookings that occupy a seat in the activity, with their effective status."""
    bookings = db.scalars(
        select(Booking)
        .join(BookingActivity, BookingActivity.booking_id == Booking.id)
        .where(BookingActivity.activity_id == activity.id)
    ).all()
    result = []
    for booking in bookings:
        status = effective_status(booking.status, booking.hold_expires_at, now)
        if occupies_seats(status):
            result.append((booking, status))
    result.sort(
        key=lambda item: (
            item[0].participant.last_name.lower(),
            item[0].participant.first_name.lower(),
        )
    )
    return result


def _check_inside(edition: Edition, day: date) -> None:
    if edition.start_date is None or edition.end_date is None:
        raise ActivityRefused("outside_edition")
    if not edition.start_date <= day <= edition.end_date:
        raise ActivityRefused("outside_edition")


def create(db: Session, admin: Participant, edition: Edition, data: ActivityData) -> Activity:
    _check_inside(edition, data.date)
    activity = Activity(edition_id=edition.id, **vars(data))
    db.add(activity)
    db.flush()
    audit.log(db, admin, "activity_created", f"Attività creata: {_describe(activity)}")
    db.commit()
    return activity


def update(
    db: Session,
    admin: Participant,
    edition: Edition,
    activity: Activity,
    data: ActivityData,
    now: datetime,
    sender: EmailSender | None = None,
) -> Activity:
    _check_inside(edition, data.date)
    db.scalar(activities_for_update([activity.id], edition.id))
    check = check_activity_edit(
        joined=linked_count(db, activity.id),
        price_changed=False,
        when_changed=(data.date, data.period) != (activity.date, activity.period),
        new_capacity=None,
    )
    occupied = occupied_by_activity(db, [activity.id], now)[activity.id]
    capacity_check = check_activity_edit(occupied, False, False, data.capacity)
    for result in (check, capacity_check):
        if not result.ok:
            assert result.reason is not None
            raise ActivityRefused(result.reason)
    before = _describe(activity)
    previous_time = activity.time_label
    financial_change = (activity.price_cents, activity.payment_mode) != (
        data.price_cents,
        data.payment_mode,
    )
    for key, value in vars(data).items():
        setattr(activity, key, value)
    db.flush()
    confirmed = (
        reprice(db, edition, admin, now, activity_id=activity.id) if financial_change else []
    )
    audit.log(
        db,
        admin,
        "activity_updated",
        f"Attività modificata: {before} → {_describe(activity)}. "
        f"Orario: {previous_time or 'non indicato'} → {activity.time_label or 'non indicato'}",
    )
    db.commit()
    if sender is not None:
        for booking in confirmed:
            send_transition_confirmation(db, sender, booking, paid_total(booking), now)
    return activity


def delete(db: Session, admin: Participant, activity: Activity) -> None:
    check = check_activity_delete(linked_count(db, activity.id))
    if not check.ok:
        assert check.reason is not None
        raise ActivityRefused(check.reason)
    audit.log(db, admin, "activity_deleted", f"Attività eliminata: {_describe(activity)}")
    db.delete(activity)
    db.commit()


def _describe(activity: Activity) -> str:
    price = "gratuita" if activity.price_cents == 0 else format_euro(activity.price_cents)
    seats = "senza limite" if activity.capacity is None else f"{activity.capacity} posti"
    description = (
        f"{format_activity(activity.title, activity.date, activity.period)}, {price}, {seats}"
    )
    if activity.payment_mode == "provider":
        description += f", pagamento diretto: {activity.payment_instructions}"
    return description


class InvalidActivities(Exception):
    pass


class ActivitiesRefused(Exception):
    def __init__(self, reason: str, activities: list[Activity]) -> None:
        self.reason = reason
        self.activities = activities
        super().__init__(reason)


def offers_for(
    db: Session, booking: Booking, now: datetime
) -> list[tuple[Activity, int | None, bool, bool]]:
    """Activities the booking can see: those it holds and those its presence allows.
    Each with free seats, whether it is joined and whether its day is over."""
    edition = db.get(Edition, booking.edition_id)
    assert edition is not None
    periods = periods_by_day((s.date, s.period) for s in booking.slots)
    joined = {a.id for a in booking.activities}
    visible = [
        a
        for a in list_activities(db, edition)
        if a.id in joined or is_eligible(periods.get(a.date, ()), a.period)
    ]
    free = free_by_activity(db, visible, now)
    return [(a, free[a.id], a.id in joined, is_past_day(a.date, now)) for a in visible]


def change_activities(
    db: Session,
    sender: EmailSender,
    booking: Booking,
    activity_ids: Iterable[int],
    now: datetime,
    allow_past: bool = False,
    force: bool = False,
    actor: Participant | None = None,
) -> ChangeResult:
    """Replace the activities of a pending or confirmed booking and recompute the amount.

    Same rules as a change of slots (D-017). Joining needs presence in that part of the day and a
    free seat; the activities being added are locked so two people cannot take the last seat
    together. `allow_past`, `force` and `actor` are for admins.
    """
    expire_overdue(db, now)
    # Lock first, then read: a cancellation committed in between must be seen (as in
    # record_payment), or a cancelled booking could be edited and even confirmed again.
    lock_booking(db, booking.id)
    db.refresh(booking)
    if not can_edit_slots(effective_status(booking.status, booking.hold_expires_at, now)):
        raise NotEditable()
    wanted = set(activity_ids)
    current = {a.id: a for a in booking.activities}
    added_ids = wanted - set(current)
    added = (
        list(db.scalars(activities_for_update(added_ids, booking.edition_id))) if added_ids else []
    )
    if len(added) != len(added_ids):
        raise InvalidActivities()
    removed = [a for activity_id, a in current.items() if activity_id not in wanted]

    periods = periods_by_day((s.date, s.period) for s in booking.slots)
    free = free_by_activity(db, added, now)
    refusals: dict[str, list[Activity]] = {}
    for activity in added:
        check = check_join(
            is_eligible(periods.get(activity.date, ()), activity.period),
            free[activity.id],
            is_past_day(activity.date, now),
            allow_past,
            force,
        )
        if not check.ok:
            assert check.reason is not None
            refusals.setdefault(check.reason, []).append(activity)
    for activity in removed:
        if not check_leave(is_past_day(activity.date, now), allow_past).ok:
            refusals.setdefault("past_day", []).append(activity)
    for reason in ("not_present", "past_day", "full"):
        if reason in refusals:
            raise ActivitiesRefused(reason, refusals[reason])

    edition = db.get(Edition, booking.edition_id)
    assert edition is not None
    old_amount = booking.amount_due_cents
    over = [a for a in added if not has_free_seat(free[a.id])]
    booking.activities = sorted(
        [a for a in booking.activities if a.id in wanted] + added, key=activity_sort_key
    )
    recompute_amount(edition, booking)
    if actor is not None:
        audit.log(
            db,
            actor,
            "activities_changed",
            _describe_change(added, removed, over, old_amount, booking.amount_due_cents),
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
    return ChangeResult(booking, confirmed_now, over_capacity_activities=over)


def labels(activities: Iterable[Activity]) -> str:
    return ", ".join(
        format_activity(a.title, a.date, a.period)
        for a in sorted(activities, key=activity_sort_key)
    )


def _describe_change(
    added: list[Activity], removed: list[Activity], over: list[Activity], old: int, new: int
) -> str:
    parts = ["Attività modificate."]
    if added:
        parts.append(f"Aggiunte: {labels(added)}.")
    if removed:
        parts.append(f"Tolte: {labels(removed)}.")
    parts.append(f"Quota: {format_euro(old)} → {format_euro(new)}.")
    if over:
        parts.append(f"Oltre la capienza: {labels(over)}.")
    return " ".join(parts)
