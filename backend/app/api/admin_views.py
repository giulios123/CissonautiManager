from collections import Counter
from datetime import date, datetime, time
from itertools import groupby
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.csv_export import Amount, Cell, csv_filename, csv_response
from app.db import get_db
from app.deps import get_now, require_admin
from app.domain.meals import diet_counts, meal_counts_by_day
from app.domain.presence import presence_by_slot, week_summary
from app.models import MEAL_DINNER, MEAL_LUNCH
from app.services import views as views_service
from app.services import waitlist as waitlist_service
from app.timefmt import meal_label, period_label, status_label

router = APIRouter(prefix="/api/admin/views", tags=["admin"], dependencies=[Depends(require_admin)])

Format = Literal["json", "csv"]


class SlotPerson(BaseModel):
    booking_id: int
    first_name: str
    last_name: str
    email: str
    status: str
    # The evening of someone who booked morning and afternoon is derived, not booked (D-009).
    derived: bool


class WaitingPerson(BaseModel):
    entry_id: int
    # The person, for actions that are about them and not about a booking (they may have none).
    participant_id: int
    # Place in the real promotion order: verified +1s come first (MVP 7).
    position: int
    first_name: str
    last_name: str
    email: str
    since: datetime
    # An admin verified that they were invited by `invited_by`.
    plus_one: bool = False
    invited_by: str | None = None


class SlotPresenceOut(BaseModel):
    id: int
    period: str
    start_time: time
    end_time: time
    capacity: int | None
    present: int
    free: int | None
    people: list[SlotPerson]
    waitlist: list[WaitingPerson] = []


class DayPresenceOut(BaseModel):
    date: date
    slots: list[SlotPresenceOut]


class SlotsViewOut(BaseModel):
    days: list[DayPresenceOut]


@router.get("/slots", response_model=None)
def slots_view(
    fmt: Format = Query(default="json", alias="format"),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> SlotsViewOut | Response:
    data = views_service.load_presence(db, now)
    grouped = presence_by_slot(data.rows)
    queues = waitlist_service.active_entries(db, [s.id for s in data.slots])
    days: list[DayPresenceOut] = []
    for day, day_slots in groupby(data.slots, key=lambda s: s.date):
        slot_views = []
        for slot in day_slots:
            rows = grouped.get((slot.date, slot.period), [])
            people = sorted(
                (
                    SlotPerson(
                        booking_id=data.people[r.person_id].booking_id,
                        first_name=data.people[r.person_id].first_name,
                        last_name=data.people[r.person_id].last_name,
                        email=data.people[r.person_id].email,
                        status=data.people[r.person_id].status,
                        derived=r.derived,
                    )
                    for r in rows
                ),
                key=lambda p: (p.last_name.lower(), p.first_name.lower()),
            )
            slot_views.append(
                SlotPresenceOut(
                    id=slot.id,
                    period=slot.period,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    capacity=slot.capacity,
                    present=len(people),
                    free=None if slot.capacity is None else max(slot.capacity - len(people), 0),
                    people=people,
                    waitlist=[
                        WaitingPerson(
                            entry_id=entry.id,
                            participant_id=entry.participant_id,
                            position=position,
                            first_name=entry.participant.first_name,
                            last_name=entry.participant.last_name,
                            email=entry.participant.email,
                            since=entry.created_at,
                            plus_one=entry.participant.plus_one_verified_at is not None,
                            invited_by=entry.participant.invited_by,
                        )
                        for position, entry in enumerate(queues.get(slot.id, []), start=1)
                    ],
                )
            )
        days.append(DayPresenceOut(date=day, slots=slot_views))
    if fmt == "csv":
        rows = [
            [
                day.date,
                period_label(slot.period),
                f"{slot.start_time:%H:%M}-{slot.end_time:%H:%M}",
                person.first_name,
                person.last_name,
                person.email,
                status_label(person.status),
                person.derived,
                None,
                None,
                None,
            ]
            for day in days
            for slot in day.slots
            for person in slot.people
        ] + [
            [
                day.date,
                period_label(slot.period),
                f"{slot.start_time:%H:%M}-{slot.end_time:%H:%M}",
                waiting.first_name,
                waiting.last_name,
                waiting.email,
                "In lista d'attesa",
                False,
                waiting.position,
                waiting.plus_one,
                waiting.invited_by,
            ]
            for day in days
            for slot in day.slots
            for waiting in slot.waitlist
        ]
        header = [
            "Giorno",
            "Slot",
            "Orario",
            "Nome",
            "Cognome",
            "Email",
            "Stato",
            "Sera derivata",
            "Posizione in lista",
            "+1 verificato",
            "Invitato da",
        ]
        return csv_response(csv_filename("giorni-slot", now), header, rows)
    return SlotsViewOut(days=days)


class MealPerson(BaseModel):
    booking_id: int
    first_name: str
    last_name: str
    email: str
    diet: str | None
    allergies: str | None


class MealOut(BaseModel):
    kind: str
    count: int
    diets: dict[str, int]
    people: list[MealPerson]


class MealDayOut(BaseModel):
    date: date
    meals: list[MealOut]


class MealsViewOut(BaseModel):
    days: list[MealDayOut]


DIET_LABELS = {"omnivore": "Onnivoro", "vegetarian": "Vegetariano", "vegan": "Vegano"}


@router.get("/meals", response_model=None)
def meals_view(
    fmt: Format = Query(default="json", alias="format"),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> MealsViewOut | Response:
    """Who eats when, with diets and allergies. Contains health data: admins only."""
    data = views_service.load_meals(db, now)
    if fmt == "csv":
        header = [
            "Giorno",
            "Pasto",
            "Nome",
            "Cognome",
            "Email",
            "Regime",
            "Allergie e intolleranze",
        ]
        rows = [
            [
                r.day,
                meal_label(r.kind),
                r.first_name,
                r.last_name,
                r.email,
                DIET_LABELS.get(r.diet or "", "Non indicato"),
                r.allergies,
            ]
            for r in data.rows
        ]
        return csv_response(csv_filename("pasti", now), header, rows)
    days = []
    for day in data.days:
        meals = []
        for kind in (MEAL_LUNCH, MEAL_DINNER):
            people = [r for r in data.rows if r.day == day and r.kind == kind]
            meals.append(
                MealOut(
                    kind=kind,
                    count=len(people),
                    diets=diet_counts(r.diet for r in people),
                    people=[
                        MealPerson(
                            booking_id=r.booking_id,
                            first_name=r.first_name,
                            last_name=r.last_name,
                            email=r.email,
                            diet=r.diet,
                            allergies=r.allergies,
                        )
                        for r in people
                    ],
                )
            )
        days.append(MealDayOut(date=day, meals=meals))
    return MealsViewOut(days=days)


class WeekDayOut(BaseModel):
    date: date
    morning: int
    afternoon: int
    evening: int
    evening_derived: int
    people: int
    lunches: int = 0
    dinners: int = 0
    activities: int = 0


class WeekOut(BaseModel):
    days: list[WeekDayOut]
    total_people: int
    total_lunches: int = 0
    total_dinners: int = 0
    total_activities: int = 0


@router.get("/week", response_model=None)
def week_view(
    fmt: Format = Query(default="json", alias="format"),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> WeekOut | Response:
    data = views_service.load_presence(db, now)
    day_list = {slot.date for slot in data.slots}
    summary = week_summary(data.rows, day_list)
    meals = meal_counts_by_day(
        ((r.day, r.kind) for r in views_service.load_meals(db, now).rows), day_list
    )
    signups = Counter(views_service.activity_signup_days(db, now))
    days = [
        WeekDayOut(
            date=s.day,
            morning=s.morning,
            afternoon=s.afternoon,
            evening=s.evening,
            evening_derived=s.evening_derived,
            people=s.people,
            lunches=meals[s.day][MEAL_LUNCH],
            dinners=meals[s.day][MEAL_DINNER],
            activities=signups.get(s.day, 0),
        )
        for s in summary
    ]
    total = len({row.person_id for row in data.rows})
    lunches = sum(d.lunches for d in days)
    dinners = sum(d.dinners for d in days)
    activities = sum(d.activities for d in days)
    if fmt == "csv":
        header = [
            "Giorno",
            "Mattina",
            "Pomeriggio",
            "Sera",
            "di cui sera derivata",
            "Persone",
            "Pranzi",
            "Cene",
            "Adesioni alle attività",
        ]
        rows: list[list[Cell]] = [
            [
                d.date,
                d.morning,
                d.afternoon,
                d.evening,
                d.evening_derived,
                d.people,
                d.lunches,
                d.dinners,
                d.activities,
            ]
            for d in days
        ]
        rows.append(
            [
                "Totale (persone diverse)",
                None,
                None,
                None,
                None,
                total,
                lunches,
                dinners,
                activities,
            ]
        )
        return csv_response(csv_filename("settimana", now), header, rows)
    return WeekOut(
        days=days,
        total_people=total,
        total_lunches=lunches,
        total_dinners=dinners,
        total_activities=activities,
    )


class ContributionOut(BaseModel):
    id: int
    kind: str
    title: str
    description: str | None
    booking_id: int
    first_name: str
    last_name: str
    email: str
    status: str
    active: bool
    created_at: datetime


KIND_LABELS = {"talk": "Talk", "topic": "Tema per l'unconference", "skill": "Competenza"}


@router.get("/contributions", response_model=None)
def contributions_view(
    kind: Literal["talk", "topic", "skill"] | None = None,
    fmt: Format = Query(default="json", alias="format"),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> list[ContributionOut] | Response:
    rows = views_service.contribution_rows(db, now, kind)
    if fmt == "csv":
        header = [
            "Tipo",
            "Titolo",
            "Descrizione",
            "Nome",
            "Cognome",
            "Email",
            "Stato",
            "Proposto il",
        ]
        csv_rows = [
            [
                KIND_LABELS.get(r.kind, r.kind),
                r.title,
                r.description,
                r.first_name,
                r.last_name,
                r.email,
                status_label(r.status),
                r.created_at,
            ]
            for r in rows
        ]
        return csv_response(csv_filename("contributi", now), header, csv_rows)
    return [ContributionOut(**vars(r)) for r in rows]


class ReviewRowOut(BaseModel):
    booking_id: int
    first_name: str
    last_name: str
    email: str
    personal_code: str
    status: str
    amount_due_cents: int
    paid_cents: int
    balance_cents: int
    reason: str
    reason_label: str


@router.get("/payments-review", response_model=None)
def payments_review(
    fmt: Format = Query(default="json", alias="format"),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> list[ReviewRowOut] | Response:
    rows = views_service.review_rows(db, now)
    if fmt == "csv":
        header = [
            "Nome",
            "Cognome",
            "Email",
            "Codice",
            "Stato",
            "Dovuto",
            "Versato",
            "Saldo",
            "Motivo",
        ]
        csv_rows: list[list[Cell]] = [
            [
                r.first_name,
                r.last_name,
                r.email,
                r.personal_code,
                status_label(r.status),
                Amount(r.amount_due_cents),
                Amount(r.paid_cents),
                Amount(r.balance_cents),
                r.reason_label,
            ]
            for r in rows
        ]
        return csv_response(csv_filename("pagamenti-da-verificare", now), header, csv_rows)
    return [
        ReviewRowOut(
            booking_id=r.booking_id,
            first_name=r.first_name,
            last_name=r.last_name,
            email=r.email,
            personal_code=r.personal_code,
            status=r.status,
            amount_due_cents=r.amount_due_cents,
            paid_cents=r.paid_cents,
            balance_cents=r.balance_cents,
            reason=r.reason,
            reason_label=r.reason_label,
        )
        for r in rows
    ]
