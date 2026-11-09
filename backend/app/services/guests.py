"""External guests: people without an account who join meals and activities (MVP 25a).

Admins only. A guest has no booking, no slot and no email, so nothing here touches amounts or
payments. Every change is recorded in the history and committed together with the change.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.activities import check_join
from app.domain.booking import effective_status, has_free_seat, occupies_seats
from app.domain.external import Duplicate, check_guest_meals, find_duplicates
from app.domain.meals import Meal, check_health_data, meal_sort_key
from app.models import (
    Activity,
    Booking,
    Edition,
    ExternalGuest,
    ExternalGuestMeal,
    Participant,
)
from app.services import audit
from app.services.activities import activity_sort_key
from app.services.seats import activities_for_update, free_by_activity
from app.timefmt import format_activity, format_meal


class GuestNotFound(Exception):
    pass


class DuplicateGuest(Exception):
    def __init__(self, duplicates: list[Duplicate]):
        self.duplicates = duplicates


class ConsentRequired(Exception):
    """Allergies are health data and need the consent the admin collected."""


class InvalidMeals(Exception):
    def __init__(self, reason: str, meals: tuple[Meal, ...]):
        self.reason = reason
        self.meals = meals


class InvalidActivities(Exception):
    pass


class ActivitiesFull(Exception):
    def __init__(self, activities: list[Activity]):
        self.activities = activities


@dataclass
class GuestData:
    first_name: str
    last_name: str
    payer: str
    phone: str | None = None
    reference: str | None = None
    internal_note: str | None = None
    diet: str | None = None
    allergies: str | None = None
    allergies_consent: bool = False


def edition_days(edition: Edition) -> list[date]:
    if edition.start_date is None or edition.end_date is None:
        return []
    count = (edition.end_date - edition.start_date).days + 1
    return [edition.start_date + timedelta(days=i) for i in range(count)]


def get_guest(db: Session, edition: Edition, guest_id: int) -> ExternalGuest:
    guest = db.get(ExternalGuest, guest_id)
    if guest is None or guest.edition_id != edition.id:
        raise GuestNotFound()
    return guest


def list_guests(db: Session, edition: Edition) -> list[ExternalGuest]:
    guests = db.scalars(select(ExternalGuest).where(ExternalGuest.edition_id == edition.id)).all()
    return sorted(guests, key=lambda g: (g.last_name.lower(), g.first_name.lower(), g.id))


def _duplicates(
    db: Session,
    edition: Edition,
    data: GuestData,
    now: datetime,
    ignore_guest_id: int | None = None,
) -> list[Duplicate]:
    guests = [
        (g.id, g.first_name, g.last_name)
        for g in db.scalars(select(ExternalGuest).where(ExternalGuest.edition_id == edition.id))
    ]
    bookings = db.scalars(select(Booking).where(Booking.edition_id == edition.id)).all()
    participants = [
        (b.participant.id, b.participant.first_name, b.participant.last_name)
        for b in bookings
        if occupies_seats(effective_status(b.status, b.hold_expires_at, now))
    ]
    return find_duplicates(
        data.first_name, data.last_name, guests, participants, ignore_guest_id=ignore_guest_id
    )


def _apply(guest: ExternalGuest, data: GuestData, admin: Participant, now: datetime) -> None:
    health = check_health_data(data.allergies, data.allergies_consent)
    if not health.ok:
        raise ConsentRequired()
    guest.first_name = data.first_name
    guest.last_name = data.last_name
    guest.payer = data.payer
    guest.phone = data.phone
    guest.reference = data.reference
    guest.internal_note = data.internal_note
    guest.diet = data.diet
    guest.allergies = health.allergies
    if data.allergies_consent:
        # The date and author of the consent stay as first recorded.
        if guest.allergies_consent_at is None:
            guest.allergies_consent_at = now
            guest.allergies_consent_by_id = admin.id
    else:
        guest.allergies_consent_at = None
        guest.allergies_consent_by_id = None


def _names_it(activities: Iterable[Activity]) -> str:
    # The history stays in Italian whatever the language of the admin (D-044).
    return ", ".join(
        format_activity(a.title, a.date, a.period, "it")
        for a in sorted(activities, key=activity_sort_key)
    )


def _describe(guest: ExternalGuest) -> str:
    payer = "pagante" if guest.payer == "paying" else "non pagante"
    return f"{guest.first_name} {guest.last_name} ({payer})"


def create(
    db: Session,
    admin: Participant,
    edition: Edition,
    data: GuestData,
    now: datetime,
    confirm_duplicate: bool = False,
) -> ExternalGuest:
    duplicates = _duplicates(db, edition, data, now)
    if duplicates and not confirm_duplicate:
        raise DuplicateGuest(duplicates)
    guest = ExternalGuest(edition_id=edition.id, created_by_id=admin.id, created_at=now)
    _apply(guest, data, admin, now)
    db.add(guest)
    db.flush()
    audit.log(db, admin, "guest_created", f"Esterno aggiunto: {_describe(guest)}")
    db.commit()
    return guest


def update(
    db: Session,
    admin: Participant,
    edition: Edition,
    guest: ExternalGuest,
    data: GuestData,
    now: datetime,
    confirm_duplicate: bool = False,
) -> ExternalGuest:
    duplicates = _duplicates(db, edition, data, now, ignore_guest_id=guest.id)
    if duplicates and not confirm_duplicate:
        raise DuplicateGuest(duplicates)
    before = _describe(guest)
    _apply(guest, data, admin, now)
    audit.log(db, admin, "guest_updated", f"Esterno modificato: {before} → {_describe(guest)}")
    db.commit()
    return guest


def delete(db: Session, admin: Participant, guest: ExternalGuest) -> None:
    audit.log(db, admin, "guest_deleted", f"Esterno eliminato: {_describe(guest)}")
    db.delete(guest)
    db.commit()


def set_meals(
    db: Session,
    admin: Participant,
    edition: Edition,
    guest: ExternalGuest,
    meals: Iterable[Meal],
) -> list[Meal]:
    """Replace the guest's meals. No presence is needed; any day of the edition is allowed."""
    wanted = set(meals)
    check = check_guest_meals(wanted, edition_days(edition))
    if not check.ok:
        assert check.reason is not None
        raise InvalidMeals(check.reason, check.meals)
    current = {(m.date, m.kind) for m in guest.meals}
    guest.meals = [ExternalGuestMeal(date=d, kind=k) for d, k in sorted(wanted, key=meal_sort_key)]
    added = sorted(wanted - current, key=meal_sort_key)
    removed = sorted(current - wanted, key=meal_sort_key)
    if added or removed:
        parts = []
        if added:
            parts.append("aggiunti " + ", ".join(format_meal(d, k, "it") for d, k in added))
        if removed:
            parts.append("tolti " + ", ".join(format_meal(d, k, "it") for d, k in removed))
        audit.log(
            db, admin, "guest_meals_changed", f"Pasti di {_describe(guest)}: {'; '.join(parts)}"
        )
    db.commit()
    return sorted(wanted, key=meal_sort_key)


def set_activities(
    db: Session,
    admin: Participant,
    edition: Edition,
    guest: ExternalGuest,
    activity_ids: Iterable[int],
    now: datetime,
    force: bool = False,
) -> list[Activity]:
    """Replace the guest's activities. A guest takes a seat of the capacity; going over needs
    `force`. Returns the activities that ended up over capacity."""
    wanted = set(activity_ids)
    current = {a.id: a for a in guest.activities}
    added_ids = wanted - set(current)
    added = list(db.scalars(activities_for_update(added_ids, edition.id))) if added_ids else []
    if len(added) != len(added_ids):
        raise InvalidActivities()
    removed = [a for activity_id, a in current.items() if activity_id not in wanted]
    free = free_by_activity(db, added, now)
    full = [a for a in added if not check_join(True, free[a.id], False, True, force).ok]
    if full:
        raise ActivitiesFull(full)
    over = [a for a in added if not has_free_seat(free[a.id])]
    guest.activities = sorted(
        [a for a in guest.activities if a.id in wanted] + added, key=activity_sort_key
    )
    if added or removed:
        parts = []
        if added:
            parts.append("aggiunte " + _names_it(added))
        if removed:
            parts.append("tolte " + _names_it(removed))
        if over:
            parts.append("oltre la capienza: " + _names_it(over))
        audit.log(
            db,
            admin,
            "guest_activities_changed",
            f"Attività di {_describe(guest)}: {'; '.join(parts)}",
        )
    db.commit()
    return over
