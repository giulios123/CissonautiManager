from datetime import date, datetime, time
from typing import Annotated, Literal, Self
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field, StringConstraints, model_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.csv_export import Amount, csv_filename, csv_response
from app.db import get_db
from app.deps import get_email_sender, get_now, require_admin
from app.email import EmailSender
from app.i18n import current_locale, t, tr
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
    title: Annotated[Text, Field(min_length=1, max_length=200)] | None = None
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
    # MVP 29: only read when creating. `request_key` makes a repeated save return the same activity.
    source_contribution_id: int | None = Field(default=None, ge=1)
    request_key: Annotated[Text, Field(min_length=8, max_length=36)] | None = None

    @model_validator(mode="after")
    def check_terms(self) -> Self:
        localized_content = any(
            value is not None
            for value in (
                self.title_it,
                self.title_en,
                self.description_it,
                self.description_en,
            )
        )
        if localized_content and (
            not self.title_it
            or not self.title_en
            or not self.description_it
            or not self.description_en
        ):
            raise ValueError(t("activity.bilingual_required"))
        if localized_content:
            locale = current_locale()
            self.title = self.title_it
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
    # The proposal it came from; `contribution_id` is empty once the proposal is gone.
    source: dict | None = None


class ActivityPerson(BaseModel):
    booking_id: int
    first_name: str
    last_name: str
    email: str
    phone: str | None
    status: str


class ActivityGuest(BaseModel):
    guest_id: int
    first_name: str
    last_name: str
    phone: str | None
    payer: str


class ActivityDetailOut(ActivityOut):
    people: list[ActivityPerson]
    guests: list[ActivityGuest] = []
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
        or activity.description,
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
        translation_missing=any(
            not value
            for value in (
                activity.title_it,
                activity.title_en,
                activity.description_it,
                activity.description_en,
            )
        ),
        internal_note=activity.internal_note,
        source=(
            {"contribution_id": activity.source_contribution_id, "title": activity.source_title}
            if activity.source_title is not None
            else None
        ),
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
    "Tipo",
    "Nota interna",
]


def _guests(db: Session, activity: Activity) -> list[ActivityGuest]:
    return [
        ActivityGuest(
            guest_id=g.id,
            first_name=g.first_name,
            last_name=g.last_name,
            phone=g.phone,
            payer=g.payer,
        )
        for g in activity_service.guests_of(db, activity)
    ]


def _csv_rows(activity: Activity, people: list[ActivityPerson], guests: list[ActivityGuest]):
    title = (activity.title_it if current_locale() == "it" else activity.title_en) or activity.title
    head = [activity.date, period_label(activity.period), title, Amount(activity.price_cents)]
    terms = [t(f"collection.{activity.payment_mode}"), activity.payment_instructions]
    if not people and not guests:
        yield [*head, None, None, None, None, None, *terms, None, activity.internal_note]
    first = True
    for person in people:
        yield [
            *head,
            person.first_name,
            person.last_name,
            person.email,
            person.phone,
            status_label(person.status),
            *terms,
            tr("Iscritto"),
            activity.internal_note if first else None,
        ]
        first = False
    for guest in guests:
        yield [
            *head,
            guest.first_name,
            guest.last_name,
            None,
            guest.phone,
            None,
            *terms,
            tr("Esterno"),
            activity.internal_note if first else None,
        ]
        first = False


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
        title=(body.title_it or body.title or "")
        if existing is None
        else (body.title_it or existing.title),
        description=(body.description_it or body.description)
        if existing is None
        else (body.description_it if body.title_it is not None else existing.description),
        title_it=(body.title_it if body.title_it is not None else existing.title_it)
        if existing is not None
        else body.title_it,
        title_en=(body.title_en if body.title_en is not None else existing.title_en)
        if existing is not None
        else body.title_en,
        description_it=(
            body.description_it if body.title_it is not None else existing.description_it
        )
        if existing is not None
        else body.description_it,
        description_en=(
            body.description_en if body.title_it is not None else existing.description_en
        )
        if existing is not None
        else body.description_en,
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
            for row in _csv_rows(activity, _people(db, activity, now), _guests(db, activity))
        ]
        return csv_response(csv_filename("attivita", now), CSV_HEADER, rows)
    free = activity_service.free_by_activity(db, activities, now)
    occupied = activity_service.occupied_by_activity(db, [a.id for a in activities], now)
    return [_out(a, free[a.id], occupied[a.id]) for a in activities]


@router.post("", status_code=201)
def create_activity(
    body: ActivityIn,
    response: Response,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> ActivityOut:
    edition = _edition(db)
    if body.request_key is not None:
        existing = activity_service.find_by_request_key(db, edition, body.request_key)
        if existing is not None:
            return _existing(db, existing, now, response)
    if not all((body.title_it, body.title_en, body.description_it, body.description_en)):
        raise HTTPException(status_code=422, detail=t("activity.bilingual_required"))
    try:
        source = None
        if body.source_contribution_id is not None:
            source = activity_service.source_contribution(db, edition, body.source_contribution_id)
        if (
            not edition.start_date
            or not edition.end_date
            or not edition.start_date <= body.date <= edition.end_date
        ):
            raise activity_service.ActivityRefused("outside_edition")
        activity = activity_service.create(
            db, admin, edition, _data(body, edition), source=source, request_key=body.request_key
        )
    except activity_service.SourceNotFound as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=t("activity.source_not_found")) from exc
    except activity_service.ActivityRefused as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=t(REFUSALS[exc.reason])) from exc
    except IntegrityError:
        # Two saves of the same form in a race: the other one won, return its activity.
        db.rollback()
        existing = (
            activity_service.find_by_request_key(db, edition, body.request_key)
            if body.request_key is not None
            else None
        )
        if existing is None:
            raise
        return _existing(db, existing, now, response)
    return _out(activity, activity.capacity, 0)


def _existing(db: Session, activity: Activity, now: datetime, response: Response) -> ActivityOut:
    """The activity a repeated save already created (200 instead of 201)."""
    response.status_code = 200
    free = activity_service.free_by_activity(db, [activity], now)[activity.id]
    joined = len(_people(db, activity, now)) + len(_guests(db, activity))
    return _out(activity, free, joined)


@router.get("/{activity_id}", response_model=None)
def get_activity(
    activity_id: int,
    fmt: Format = Query(default="json", alias="format"),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> ActivityDetailOut | Response:
    activity = _get(db, activity_id)
    people = _people(db, activity, now)
    guests = _guests(db, activity)
    if fmt == "csv":
        name = f"attivita-{activity.id}"
        return csv_response(
            csv_filename(name, now), CSV_HEADER, _csv_rows(activity, people, guests)
        )
    free = activity_service.free_by_activity(db, [activity], now)[activity.id]
    history = (
        db.query(ActivityNoteRevision)
        .filter_by(activity_id=activity.id)
        .order_by(ActivityNoteRevision.id.desc())
        .all()
    )
    return ActivityDetailOut(
        **_out(activity, free, len(people) + len(guests)).model_dump(),
        people=people,
        guests=guests,
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
    if body.title_it is None and body.title is not None and body.title != activity.title:
        raise HTTPException(status_code=422, detail=t("activity.bilingual_required"))
    if (
        body.title_it is None
        and body.description is not None
        and body.description != activity.description
    ):
        raise HTTPException(status_code=422, detail=t("activity.bilingual_required"))
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
