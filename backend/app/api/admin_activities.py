from datetime import date, datetime, time
from typing import Annotated, Literal, Self
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field, StringConstraints, model_validator
from sqlalchemy.orm import Session

from app.csv_export import Amount, csv_filename, csv_response
from app.db import get_db
from app.deps import get_email_sender, get_now, require_admin
from app.email import EmailSender
from app.i18n import current_locale, t
from app.models import Activity, ActivityNoteRevision, Edition, Participant
from app.services import activities as activity_service
from app.services import edition as edition_service
from app.services.amounts import activity_terms
from app.timefmt import period_label, status_label

router = APIRouter(
    prefix="/api/admin/activities", tags=["admin"], dependencies=[Depends(require_admin)]
)

Format = Literal["json", "csv"]
Text = Annotated[str, StringConstraints(strip_whitespace=True)]

REFUSALS = {
    "outside_edition": "activity.outside_edition",
    "fixed_with_people": "activity.fixed_with_people",
    "capacity_below_people": "activity.capacity_below_people",
    "has_people": "activity.has_people",
    "invalid_time": "activity.invalid_time",
}


class ActivityIn(BaseModel):
    title: Annotated[Text, Field(min_length=1, max_length=200)]
    description: Annotated[Text, Field(max_length=5000)] | None = None
    title_it: Annotated[Text, Field(min_length=1, max_length=200)] | None = None
    title_en: Annotated[Text, Field(min_length=1, max_length=200)] | None = None
    description_it: Annotated[Text, Field(max_length=5000)] | None = None
    description_en: Annotated[Text, Field(max_length=5000)] | None = None
    date: date
    period: Literal["morning", "afternoon", "evening"]
    start_time: time | None = None
    end_time: time | None = None
    payment_mode: Literal["organizer", "provider"] = "organizer"
    payment_instructions: Annotated[Text, Field(max_length=5000)] | None = None
    price_cents: int = Field(default=0, ge=0, le=1_000_000)
    capacity: int | None = Field(default=None, ge=1, le=10000)

    @model_validator(mode="after")
    def check_terms(self) -> Self:
        if (self.title_it is None) != (self.title_en is None):
            raise ValueError(t("activity.bilingual_required"))
        if (self.description_it is None) != (self.description_en is None):
            raise ValueError(t("activity.bilingual_description"))
        if self.title_it is not None:
            locale = current_locale()
            self.title = self.title_it if locale == "it" else self.title_en or self.title_it
            self.description = self.description_it if locale == "it" else self.description_en
        if self.payment_mode == "provider" and (
            "price_cents" not in self.model_fields_set or not self.payment_instructions
        ):
            raise ValueError(t("collection.terms_required"))
        return self


class ActivityOut(BaseModel):
    id: int
    title: str
    description: str | None
    date: date
    period: str
    time_label: str | None
    start_time: str | None = None
    end_time: str | None = None
    payment_mode: str
    payment_instructions: str | None
    collectable_cents: int
    price_cents: int
    capacity: int | None
    joined: int
    free: int | None
    title_it: str | None = None
    title_en: str | None = None
    description_it: str | None = None
    description_en: str | None = None
    translation_missing: bool = False
    internal_note: str | None = None


class ActivityPerson(BaseModel):
    booking_id: int
    first_name: str
    last_name: str
    email: str
    phone: str | None
    status: str


class ActivityDetailOut(ActivityOut):
    people: list[ActivityPerson]
    internal_note: str | None = None
    note_history: list[dict] = []


class InternalNoteIn(BaseModel):
    note: Annotated[Text, Field(max_length=5000)] | None = None


def _edition(db: Session) -> Edition:
    edition = edition_service.get_active_edition(db)
    if edition is None:
        raise HTTPException(status_code=404, detail=t("edition.not_configured_first"))
    return edition


def _out(activity: Activity, free: int | None, joined: int) -> ActivityOut:
    locale = current_locale()
    return ActivityOut(
        id=activity.id,
        title=(activity.title_it if locale == "it" else activity.title_en) or activity.title,
        description=(activity.description_it if locale == "it" else activity.description_en)
        if activity.title_it
        else activity.description,
        date=activity.date,
        period=activity.period,
        time_label=activity.time_label,
        start_time=activity.starts_at.astimezone(ZoneInfo("Europe/Rome")).strftime("%H:%M")
        if activity.starts_at
        else None,
        end_time=activity.ends_at.astimezone(ZoneInfo("Europe/Rome")).strftime("%H:%M")
        if activity.ends_at
        else None,
        **activity_terms(activity),
        capacity=activity.capacity,
        joined=joined,
        free=free,
        title_it=activity.title_it,
        title_en=activity.title_en,
        description_it=activity.description_it,
        description_en=activity.description_en,
        translation_missing=activity.title_it is None or activity.title_en is None,
        internal_note=activity.internal_note,
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
    "Incasso",
    "Istruzioni di pagamento",
    "Nota interna",
]


def _csv_rows(activity: Activity, people: list[ActivityPerson]):
    title = (activity.title_it if current_locale() == "it" else activity.title_en) or activity.title
    if not people:
        yield [
            activity.date,
            period_label(activity.period),
            title,
            Amount(activity.price_cents),
            None,
            None,
            None,
            None,
            None,
            t(f"collection.{activity.payment_mode}"),
            activity.payment_instructions,
            activity.internal_note,
        ]
    for person in people:
        yield [
            activity.date,
            period_label(activity.period),
            title,
            Amount(activity.price_cents),
            person.first_name,
            person.last_name,
            person.email,
            person.phone,
            status_label(person.status),
            t(f"collection.{activity.payment_mode}"),
            activity.payment_instructions,
            activity.internal_note,
        ]


def _data(
    body: ActivityIn, edition: Edition, existing: Activity | None = None
) -> activity_service.ActivityData:
    if existing is not None and body.start_time is None and body.end_time is None:
        if existing.starts_at is not None and existing.ends_at is not None:
            zone = ZoneInfo("Europe/Rome")
            times = activity_service.activity_times(
                edition,
                body.date,
                body.period,
                existing.starts_at.astimezone(zone).time(),
                existing.ends_at.astimezone(zone).time(),
            )
        else:
            times = dict(starts_at=None, ends_at=None, time_label=existing.time_label)
    else:
        times = activity_service.activity_times(
            edition, body.date, body.period, body.start_time, body.end_time
        )
    return activity_service.ActivityData(
        title=body.title,
        description=body.description or None,
        title_it=body.title_it or body.title,
        title_en=body.title_en or body.title,
        description_it=body.description_it if body.description_it is not None else body.description,
        description_en=body.description_en if body.description_en is not None else body.description,
        internal_note=existing.internal_note if existing is not None else None,
        date=body.date,
        period=body.period,
        **times,
        payment_mode=body.payment_mode,
        payment_instructions=body.payment_instructions if body.payment_mode == "provider" else None,
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
        edition = _edition(db)
        if (
            not edition.start_date
            or not edition.end_date
            or not edition.start_date <= body.date <= edition.end_date
        ):
            raise activity_service.ActivityRefused("outside_edition")
        activity = activity_service.create(db, admin, edition, _data(body, edition))
    except activity_service.ActivityRefused as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=t(REFUSALS[exc.reason])) from exc
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
    history = (
        db.query(ActivityNoteRevision)
        .filter_by(activity_id=activity.id)
        .order_by(ActivityNoteRevision.id.desc())
        .all()
    )
    return ActivityDetailOut(
        **_out(activity, free, len(people)).model_dump(),
        people=people,
        note_history=[
            {
                "note": row.note,
                "author": db.get(Participant, row.actor_id).email,
                "created_at": row.created_at,
            }
            for row in history
        ],
    )


@router.put("/{activity_id}/note")
def update_internal_note(
    activity_id: int,
    body: InternalNoteIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    activity = _get(db, activity_id)
    note = body.note.strip() if body.note else None
    activity.internal_note = note
    revision = ActivityNoteRevision(activity_id=activity.id, actor_id=admin.id, note=note)
    db.add(revision)
    db.commit()
    db.refresh(revision)
    return {"note": note, "created_at": revision.created_at}


@router.patch("/{activity_id}")
def update_activity(
    activity_id: int,
    body: ActivityIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
    sender: EmailSender = Depends(get_email_sender),
) -> ActivityOut:
    activity = _get(db, activity_id)
    try:
        edition = _edition(db)
        activity_service.update(
            db, admin, edition, activity, _data(body, edition, activity), now, sender
        )
    except activity_service.ActivityRefused as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=t(REFUSALS[exc.reason])) from exc
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
        raise HTTPException(status_code=409, detail=t(REFUSALS[exc.reason])) from exc


def _get(db: Session, activity_id: int) -> Activity:
    try:
        return activity_service.get_activity(db, _edition(db), activity_id)
    except activity_service.ActivityNotFound as exc:
        raise HTTPException(status_code=404, detail=t("activity.not_found")) from exc
