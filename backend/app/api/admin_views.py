from datetime import date, datetime, time
from itertools import groupby
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.csv_export import Cell, csv_filename, csv_response
from app.db import get_db
from app.deps import get_now, require_admin
from app.domain.presence import presence_by_slot, week_summary
from app.services import views as views_service
from app.timefmt import period_label, status_label

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


class SlotPresenceOut(BaseModel):
    id: int
    period: str
    start_time: time
    end_time: time
    capacity: int | None
    present: int
    free: int | None
    people: list[SlotPerson]


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
            ]
            for day in days
            for slot in day.slots
            for person in slot.people
        ]
        header = ["Giorno", "Slot", "Orario", "Nome", "Cognome", "Email", "Stato", "Sera derivata"]
        return csv_response(csv_filename("giorni-slot", now), header, rows)
    return SlotsViewOut(days=days)


class WeekDayOut(BaseModel):
    date: date
    morning: int
    afternoon: int
    evening: int
    evening_derived: int
    people: int


class WeekOut(BaseModel):
    days: list[WeekDayOut]
    total_people: int


@router.get("/week", response_model=None)
def week_view(
    fmt: Format = Query(default="json", alias="format"),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> WeekOut | Response:
    data = views_service.load_presence(db, now)
    summary = week_summary(data.rows, {slot.date for slot in data.slots})
    days = [
        WeekDayOut(
            date=s.day,
            morning=s.morning,
            afternoon=s.afternoon,
            evening=s.evening,
            evening_derived=s.evening_derived,
            people=s.people,
        )
        for s in summary
    ]
    total = len({row.person_id for row in data.rows})
    if fmt == "csv":
        header = ["Giorno", "Mattina", "Pomeriggio", "Sera", "di cui sera derivata", "Persone"]
        rows: list[list[Cell]] = [
            [d.date, d.morning, d.afternoon, d.evening, d.evening_derived, d.people] for d in days
        ]
        rows.append(["Totale persone diverse", None, None, None, None, total])
        return csv_response(csv_filename("settimana", now), header, rows)
    return WeekOut(days=days, total_people=total)
