"""External guests (MVP 25a): people without an account who join meals and activities.

Admins only. Guests never appear in any participant-facing response.
"""

from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy.orm import Session

from app.api.admin_views import DIET_LABELS
from app.csv_export import csv_filename, csv_response
from app.db import get_db
from app.deps import get_now, require_admin
from app.i18n import current_locale, t, tr
from app.models import PAYERS, Activity, Edition, ExternalGuest, Participant
from app.services import edition as edition_service
from app.services import guests as guest_service
from app.services.activities import activity_sort_key
from app.timefmt import format_day_short, meal_label, period_label

router = APIRouter(
    prefix="/api/admin/guests", tags=["admin"], dependencies=[Depends(require_admin)]
)

Format = Literal["json", "csv"]
Text = Annotated[str, StringConstraints(strip_whitespace=True)]
Diet = Literal["omnivore", "vegetarian", "vegan"]
MealKind = Literal["lunch", "dinner"]


class GuestIn(BaseModel):
    first_name: Annotated[Text, Field(min_length=1, max_length=100)]
    last_name: Annotated[Text, Field(min_length=1, max_length=100)]
    payer: Literal["paying", "non_paying"] = "paying"
    phone: Annotated[Text, Field(max_length=50)] | None = None
    reference: Annotated[Text, Field(max_length=200)] | None = None
    internal_note: Annotated[Text, Field(max_length=5000)] | None = None
    diet: Diet | None = None
    allergies: Annotated[Text, Field(max_length=2000)] | None = None
    # The admin collected the person's consent to keep the allergies.
    allergies_consent: bool = False
    # Save even if someone with the same name is already in the edition.
    confirm_duplicate: bool = False


class MealRef(BaseModel):
    date: date
    kind: MealKind


class MealsIn(BaseModel):
    meals: list[MealRef] = Field(max_length=200)


class ActivitiesIn(BaseModel):
    activity_ids: list[int] = Field(max_length=200)
    # Accept an activity that is already full.
    force: bool = False


class ActivityRef(BaseModel):
    id: int
    title: str
    date: date
    period: str


class GuestOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    payer: str
    phone: str | None
    reference: str | None
    internal_note: str | None
    diet: str | None
    allergies: str | None
    allergies_consent_at: datetime | None
    meals: list[MealRef]
    activities: list[ActivityRef]
    warning: str | None = None


def _title(activity: Activity) -> str:
    title = activity.title_it if current_locale() == "it" else activity.title_en
    return title or activity.title


def _out(guest: ExternalGuest, warning: str | None = None) -> GuestOut:
    return GuestOut(
        id=guest.id,
        first_name=guest.first_name,
        last_name=guest.last_name,
        payer=guest.payer,
        phone=guest.phone,
        reference=guest.reference,
        internal_note=guest.internal_note,
        diet=guest.diet,
        allergies=guest.allergies,
        allergies_consent_at=guest.allergies_consent_at,
        meals=[MealRef(date=m.date, kind=m.kind) for m in guest.meals],  # type: ignore[arg-type]
        activities=[
            ActivityRef(id=a.id, title=_title(a), date=a.date, period=a.period)
            for a in sorted(guest.activities, key=activity_sort_key)
        ],
        warning=warning,
    )


def _edition(db: Session) -> Edition:
    edition = edition_service.get_active_edition(db)
    if edition is None:
        raise HTTPException(status_code=404, detail=t("edition.not_configured_first"))
    return edition


def _guest(db: Session, edition: Edition, guest_id: int) -> ExternalGuest:
    try:
        return guest_service.get_guest(db, edition, guest_id)
    except guest_service.GuestNotFound as exc:
        raise HTTPException(status_code=404, detail=t("guests.not_found")) from exc


def _data(body: GuestIn) -> guest_service.GuestData:
    assert body.payer in PAYERS
    return guest_service.GuestData(
        first_name=body.first_name,
        last_name=body.last_name,
        payer=body.payer,
        phone=body.phone or None,
        reference=body.reference or None,
        internal_note=body.internal_note or None,
        diet=body.diet,
        allergies=body.allergies or None,
        allergies_consent=body.allergies_consent,
    )


def _duplicate_error(exc: guest_service.DuplicateGuest) -> HTTPException:
    names = ", ".join(f"{d.first_name} {d.last_name}" for d in exc.duplicates)
    return HTTPException(status_code=409, detail=t("guests.duplicate", names=names))


CSV_HEADER = [
    "Cognome",
    "Nome",
    "Pagante",
    "Telefono",
    "Riferimento",
    "Regime",
    "Pasti",
    "Attività",
    "Nota interna",
]


def _csv_row(guest: ExternalGuest) -> list:
    return [
        guest.last_name,
        guest.first_name,
        guest.payer == "paying",
        guest.phone,
        guest.reference,
        tr(DIET_LABELS[guest.diet]) if guest.diet else None,
        "; ".join(f"{meal_label(m.kind)} {format_day_short(m.date)}" for m in guest.meals),
        "; ".join(
            f"{_title(a)} ({format_day_short(a.date)} {period_label(a.period)})"
            for a in sorted(guest.activities, key=activity_sort_key)
        ),
        guest.internal_note,
    ]


@router.get("", response_model=None)
def list_guests(
    fmt: Format = Query(default="json", alias="format"),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> list[GuestOut] | Response:
    edition = edition_service.get_active_edition(db)
    guests = [] if edition is None else guest_service.list_guests(db, edition)
    if fmt == "csv":
        return csv_response(csv_filename("esterni", now), CSV_HEADER, [_csv_row(g) for g in guests])
    return [_out(g) for g in guests]


@router.post("", status_code=201)
def create_guest(
    body: GuestIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> GuestOut:
    edition = _edition(db)
    try:
        guest = guest_service.create(
            db, admin, edition, _data(body), now, confirm_duplicate=body.confirm_duplicate
        )
    except guest_service.DuplicateGuest as exc:
        db.rollback()
        raise _duplicate_error(exc) from exc
    except guest_service.ConsentRequired as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=t("guests.consent_required")) from exc
    return _out(guest)


@router.get("/{guest_id}")
def get_guest(guest_id: int, db: Session = Depends(get_db)) -> GuestOut:
    return _out(_guest(db, _edition(db), guest_id))


@router.patch("/{guest_id}")
def update_guest(
    guest_id: int,
    body: GuestIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> GuestOut:
    edition = _edition(db)
    guest = _guest(db, edition, guest_id)
    try:
        guest_service.update(
            db, admin, edition, guest, _data(body), now, confirm_duplicate=body.confirm_duplicate
        )
    except guest_service.DuplicateGuest as exc:
        db.rollback()
        raise _duplicate_error(exc) from exc
    except guest_service.ConsentRequired as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=t("guests.consent_required")) from exc
    return _out(guest)


@router.delete("/{guest_id}", status_code=204)
def delete_guest(
    guest_id: int,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    guest_service.delete(db, admin, _guest(db, _edition(db), guest_id))


@router.put("/{guest_id}/meals")
def set_guest_meals(
    guest_id: int,
    body: MealsIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
) -> GuestOut:
    edition = _edition(db)
    guest = _guest(db, edition, guest_id)
    try:
        guest_service.set_meals(db, admin, edition, guest, [(m.date, m.kind) for m in body.meals])
    except guest_service.InvalidMeals as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=t("guests.meals_invalid")) from exc
    db.refresh(guest)
    return _out(guest)


@router.put("/{guest_id}/activities")
def set_guest_activities(
    guest_id: int,
    body: ActivitiesIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> GuestOut:
    edition = _edition(db)
    guest = _guest(db, edition, guest_id)
    try:
        over = guest_service.set_activities(
            db, admin, edition, guest, body.activity_ids, now, force=body.force
        )
    except guest_service.InvalidActivities as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=t("activities.invalid")) from exc
    except guest_service.ActivitiesFull as exc:
        db.rollback()
        names = ", ".join(
            f"{_title(a)} ({format_day_short(a.date)} {period_label(a.period)})"
            for a in sorted(exc.activities, key=activity_sort_key)
        )
        raise HTTPException(
            status_code=409, detail=t("activities.full_force", names=names)
        ) from exc
    db.refresh(guest)
    warning = None
    if over:
        labels = ", ".join(_title(a) for a in sorted(over, key=activity_sort_key))
        warning = t("warn.over_capacity", labels=labels)
    return _out(guest, warning)
