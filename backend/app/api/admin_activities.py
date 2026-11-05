from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy.orm import Session

from app.csv_export import Amount, csv_filename, csv_response
from app.db import get_db
from app.deps import get_now, require_admin
from app.models import Activity, Edition, Participant
from app.services import activities as activity_service
from app.services import edition as edition_service
from app.timefmt import period_label, status_label

router = APIRouter(
    prefix="/api/admin/activities", tags=["admin"], dependencies=[Depends(require_admin)]
)

Format = Literal["json", "csv"]
Text = Annotated[str, StringConstraints(strip_whitespace=True)]

REFUSALS = {
    "outside_edition": "Il giorno deve essere tra le date dell'edizione",
    "fixed_with_people": "Con persone già iscritte non si cambiano prezzo, giorno e fascia",
    "capacity_below_people": "La capienza non può scendere sotto il numero di iscritti",
    "has_people": "Un'attività con iscritti non si elimina",
}


class ActivityIn(BaseModel):
    title: Annotated[Text, Field(min_length=1, max_length=200)]
    description: Annotated[Text, Field(max_length=5000)] | None = None
    date: date
    period: Literal["morning", "afternoon", "evening"]
    time_label: Annotated[Text, Field(max_length=50)] | None = None
    price_cents: int = Field(default=0, ge=0, le=1_000_000)
    capacity: int | None = Field(default=None, ge=1, le=10000)


class ActivityOut(BaseModel):
    id: int
    title: str
    description: str | None
    date: date
    period: str
    time_label: str | None
    price_cents: int
    capacity: int | None
    joined: int
    free: int | None


class ActivityPerson(BaseModel):
    booking_id: int
    first_name: str
    last_name: str
    email: str
    phone: str | None
    status: str


class ActivityDetailOut(ActivityOut):
    people: list[ActivityPerson]


def _edition(db: Session) -> Edition:
    edition = edition_service.get_active_edition(db)
    if edition is None:
        raise HTTPException(status_code=404, detail="Configura prima l'edizione")
    return edition


def _out(activity: Activity, free: int | None, joined: int) -> ActivityOut:
    return ActivityOut(
        id=activity.id,
        title=activity.title,
        description=activity.description,
        date=activity.date,
        period=activity.period,
        time_label=activity.time_label,
        price_cents=activity.price_cents,
        capacity=activity.capacity,
        joined=joined,
        free=free,
    )


def _people(db: Session, activity: Activity, now: datetime) -> list[ActivityPerson]:
    return [
        ActivityPerson(
            booking_id=booking.id,
            first_name=booking.participant.first_name,
            last_name=booking.participant.last_name,
            email=booking.participant.email,
            phone=booking.participant.phone,
            status=status,
        )
        for booking, status in activity_service.participants(db, activity, now)
    ]


CSV_HEADER = [
    "Giorno",
    "Fascia",
    "Attività",
    "Prezzo",
    "Nome",
    "Cognome",
    "Email",
    "Telefono",
    "Stato",
]


def _csv_rows(activity: Activity, people: list[ActivityPerson]):
    for person in people:
        yield [
            activity.date,
            period_label(activity.period),
            activity.title,
            Amount(activity.price_cents),
            person.first_name,
            person.last_name,
            person.email,
            person.phone,
            status_label(person.status),
        ]


def _data(body: ActivityIn) -> activity_service.ActivityData:
    return activity_service.ActivityData(
        title=body.title,
        description=body.description or None,
        date=body.date,
        period=body.period,
        time_label=body.time_label or None,
        price_cents=body.price_cents,
        capacity=body.capacity,
    )


@router.get("", response_model=None)
def list_activities(
    fmt: Format = Query(default="json", alias="format"),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> list[ActivityOut] | Response:
    edition = edition_service.get_active_edition(db)
    activities = [] if edition is None else activity_service.list_activities(db, edition)
    if fmt == "csv":
        rows = [
            row
            for activity in activities
            for row in _csv_rows(activity, _people(db, activity, now))
        ]
        return csv_response(csv_filename("attivita", now), CSV_HEADER, rows)
    free = activity_service.free_by_activity(db, activities, now)
    occupied = activity_service.occupied_by_activity(db, [a.id for a in activities], now)
    return [_out(a, free[a.id], occupied[a.id]) for a in activities]


@router.post("", status_code=201)
def create_activity(
    body: ActivityIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ActivityOut:
    try:
        activity = activity_service.create(db, admin, _edition(db), _data(body))
    except activity_service.ActivityRefused as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=REFUSALS[exc.reason]) from exc
    return _out(activity, activity.capacity, 0)


@router.get("/{activity_id}", response_model=None)
def get_activity(
    activity_id: int,
    fmt: Format = Query(default="json", alias="format"),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> ActivityDetailOut | Response:
    activity = _get(db, activity_id)
    people = _people(db, activity, now)
    if fmt == "csv":
        name = f"attivita-{activity.id}"
        return csv_response(csv_filename(name, now), CSV_HEADER, _csv_rows(activity, people))
    free = activity_service.free_by_activity(db, [activity], now)[activity.id]
    return ActivityDetailOut(**_out(activity, free, len(people)).model_dump(), people=people)


@router.patch("/{activity_id}")
def update_activity(
    activity_id: int,
    body: ActivityIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> ActivityOut:
    activity = _get(db, activity_id)
    try:
        activity_service.update(db, admin, _edition(db), activity, _data(body), now)
    except activity_service.ActivityRefused as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=REFUSALS[exc.reason]) from exc
    free = activity_service.free_by_activity(db, [activity], now)[activity.id]
    joined = activity_service.occupied_by_activity(db, [activity.id], now)[activity.id]
    return _out(activity, free, joined)


@router.delete("/{activity_id}", status_code=204)
def delete_activity(
    activity_id: int,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    activity = _get(db, activity_id)
    try:
        activity_service.delete(db, admin, activity)
    except activity_service.ActivityRefused as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=REFUSALS[exc.reason]) from exc


def _get(db: Session, activity_id: int) -> Activity:
    try:
        return activity_service.get_activity(db, _edition(db), activity_id)
    except activity_service.ActivityNotFound as exc:
        raise HTTPException(status_code=404, detail="Attività non trovata") from exc
