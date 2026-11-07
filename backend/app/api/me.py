from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.public import ChannelPublic, LegalPublic
from app.api.schemas import ActivityOffer, BookingView, activity_offers, booking_view
from app.config import Settings
from app.db import get_db
from app.deps import current_user, get_email_sender, get_now, get_settings_dep
from app.email import EmailSender
from app.i18n import channel_label, t
from app.models import DOC_HEALTH, Booking, Contribution, Edition, Participant, WaitlistEntry
from app.services import activities as activity_service
from app.services import booking_changes
from app.services import consents as consent_service
from app.services import contributions as contributions_service
from app.services import edition as edition_service
from app.services import health as health_service
from app.services import meals as meals_service
from app.services import registration as registration_service
from app.services import waitlist as waitlist_service
from app.services.passwords import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH, hash_password
from app.services.registration import InvalidSlots, SlotsFull
from app.timefmt import format_activity, format_meal, format_slot

router = APIRouter(prefix="/api", tags=["me"])


class WaitlistView(BaseModel):
    id: int
    slot_id: int
    date: date
    period: str
    label: str
    position: int


class ContributionOut(BaseModel):
    id: int
    kind: str
    title: str
    description: str | None


class MeOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    role: str
    personal_code: str
    has_password: bool
    locale: str
    bookings: list[BookingView]
    payment_channels: list[ChannelPublic]
    waitlist: list[WaitlistView] = []
    lunch_price_cents: int | None = None
    dinner_price_cents: int | None = None
    # Text of the consent for allergies; None while the admins have not published it.
    health_consent: LegalPublic | None = None
    # Activities of the current booking: the ones joined and the ones its presence allows.
    activities: list[ActivityOffer] = []
    contributions: list[ContributionOut] = []
    # What the person wrote at registration under "cosa puoi portare al camp?".
    can_bring: str | None = None


class LocaleIn(BaseModel):
    locale: Literal["it", "en"]


class PasswordIn(BaseModel):
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)


class ConsentDocumentView(BaseModel):
    id: int
    version: int
    body: str
    body_it: str | None
    body_en: str | None
    is_legacy: bool


class ConsentEventView(BaseModel):
    id: int
    action: str
    locale: str
    recorded_at: datetime
    source: str
    document: ConsentDocumentView


class OptionalConsentView(BaseModel):
    kind: str
    action: str
    event_id: int | None
    authorized_for_current_document: bool
    needs_renewal: bool
    current_document: ConsentDocumentView | None
    events: list[ConsentEventView]


class ConsentCollectionView(BaseModel):
    edition_id: int | None
    associated: bool
    consents: list[OptionalConsentView]


class ConsentUpdateIn(BaseModel):
    granted: bool
    document_id: int | None = None
    version: int | None = None
    locale: Literal["it", "en"]
    expected_event_id: int | None


@router.put("/me/locale", status_code=204)
def set_my_locale(
    body: LocaleIn,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
) -> None:
    """Language of the emails this person receives; set from the language switch."""
    user.locale = body.locale
    db.commit()


@router.get("/me")
def get_me(
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> MeOut:
    edition = edition_service.get_active_edition(db)
    bookings: list[Booking] = []
    channels = []
    waitlist: list[WaitlistView] = []
    if edition is not None:
        waitlist = [
            _waitlist_view(db, entry) for entry in waitlist_service.entries_of(db, user, edition)
        ]
        bookings = list(
            db.scalars(
                select(Booking)
                .where(Booking.participant_id == user.id, Booking.edition_id == edition.id)
                .order_by(Booking.id.desc())
            )
        )
        channels = [
            ChannelPublic(
                code=c.code, label=channel_label(c.code, c.label), instructions=c.instructions
            )
            for c in registration_service.enabled_channels(db, edition)
        ]
    return MeOut(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        role=user.role,
        personal_code=user.personal_code,
        has_password=user.password_hash is not None,
        locale=user.locale,
        bookings=[booking_view(b, now) for b in bookings],
        payment_channels=channels,
        waitlist=waitlist,
        health_consent=_health_consent(db, edition),
        activities=_offers(db, user, now),
        contributions=_contributions(db, user),
        can_bring=user.can_bring,
        lunch_price_cents=edition.lunch_price_cents if edition else None,
        dinner_price_cents=edition.dinner_price_cents if edition else None,
    )


@router.get("/me/consents", response_model=ConsentCollectionView)
def get_my_consents(
    response: Response,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
) -> ConsentCollectionView:
    response.headers["Cache-Control"] = "private, no-store"
    edition = edition_service.get_active_edition(db)
    if edition is None:
        return ConsentCollectionView(edition_id=None, associated=False, consents=[])
    snapshot = consent_service.collection_snapshot(db, edition, user)
    return ConsentCollectionView.model_validate(snapshot)


@router.put("/me/consents/{kind}", response_model=ConsentCollectionView)
def update_my_consent(
    kind: str,
    body: ConsentUpdateIn,
    response: Response,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> ConsentCollectionView:
    response.headers["Cache-Control"] = "private, no-store"
    edition = edition_service.get_active_edition(db)
    if edition is None or not consent_service.has_edition_association(db, edition, user):
        raise HTTPException(status_code=404, detail=t("consent.association_not_found"))
    try:
        consent_service.record_choice(
            db,
            edition,
            user,
            kind=kind,
            granted=body.granted,
            document_id=body.document_id,
            version=body.version,
            locale=body.locale,
            expected_event_id=body.expected_event_id,
            source="self_service",
            now=now,
        )
    except consent_service.InvalidConsentKind as exc:
        raise HTTPException(status_code=404, detail=t("consent.kind_not_found")) from exc
    except consent_service.ConsentConflict as exc:
        raise HTTPException(status_code=409, detail=t("consent.changed")) from exc
    except consent_service.ConsentDocumentUnavailable as exc:
        raise HTTPException(status_code=422, detail=t("consent.text_unavailable")) from exc
    db.commit()
    return ConsentCollectionView.model_validate(
        consent_service.collection_snapshot(db, edition, user)
    )


def _offers(db: Session, user: Participant, now: datetime) -> list[ActivityOffer]:
    booking = booking_changes.get_current_booking(db, user)
    return [] if booking is None else activity_offers(db, booking, now)


def _contributions(db: Session, user: Participant) -> list[ContributionOut]:
    booking = booking_changes.get_current_booking(db, user)
    if booking is None:
        return []
    return [_contribution_out(c) for c in booking.contributions]


def _contribution_out(contribution: Contribution) -> ContributionOut:
    return ContributionOut(
        id=contribution.id,
        kind=contribution.kind,
        title=contribution.title,
        description=contribution.description,
    )


def _health_consent(db: Session, edition: Edition | None) -> LegalPublic | None:
    if edition is None:
        return None
    document = edition_service.latest_legal_document(db, edition, DOC_HEALTH)
    return (
        LegalPublic(
            id=document.id,
            version=document.version,
            body=document.body,
            body_it=document.body_it,
            body_en=document.body_en,
            is_legacy=document.body_it is None or document.body_en is None,
        )
        if document
        else None
    )


def _waitlist_view(db: Session, entry: WaitlistEntry) -> WaitlistView:
    slot = entry.slot
    return WaitlistView(
        id=entry.id,
        slot_id=slot.id,
        date=slot.date,
        period=slot.period,
        label=format_slot(slot.date, slot.period, slot.start_time, slot.end_time),
        position=waitlist_service.position_of(db, entry),
    )


class WaitlistIn(BaseModel):
    slot_id: int


@router.post("/me/waitlist", status_code=201)
def join_waitlist(
    body: WaitlistIn,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> WaitlistView:
    try:
        entry = waitlist_service.join(db, user, body.slot_id, now)
    except waitlist_service.EntryNotFound as exc:
        raise HTTPException(status_code=404, detail=t("slot.not_found")) from exc
    except waitlist_service.NoLegalAcceptance as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=t("waitlist.register_first")) from exc
    except waitlist_service.WaitlistRefused as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail=t(waitlist_service.REFUSAL_MESSAGES[exc.reason])
        ) from exc
    db.commit()
    return _waitlist_view(db, entry)


@router.delete("/me/waitlist/{entry_id}", status_code=204)
def leave_waitlist(
    entry_id: int,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> None:
    try:
        waitlist_service.leave(db, user, entry_id, now)
    except waitlist_service.EntryNotFound as exc:
        raise HTTPException(status_code=404, detail=t("waitlist.not_listed")) from exc


@router.put("/me/password", status_code=204)
def set_password(
    body: PasswordIn, user: Participant = Depends(current_user), db: Session = Depends(get_db)
) -> None:
    user = db.merge(user)
    user.password_hash = hash_password(body.password)
    db.commit()


class SlotsIn(BaseModel):
    slot_ids: list[int] = Field(max_length=60)


@router.put("/me/booking/slots", response_model=None)
def change_my_slots(
    body: SlotsIn,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
    settings: Settings = Depends(get_settings_dep),
    now: datetime = Depends(get_now),
) -> BookingView | JSONResponse:
    booking = booking_changes.get_current_booking(db, user)
    if booking is None:
        raise HTTPException(status_code=404, detail=t("booking.none"))
    try:
        result = booking_changes.change_slots(db, sender, booking, body.slot_ids, now)
    except booking_changes.NotEditable as exc:
        raise HTTPException(status_code=409, detail=t("booking.not_editable")) from exc
    except booking_changes.EmptySelection as exc:
        raise HTTPException(status_code=422, detail=t("slots.at_least_one")) from exc
    except booking_changes.PastDay as exc:
        raise HTTPException(
            status_code=422,
            detail=t("slots.past_day"),
        ) from exc
    except InvalidSlots as exc:
        raise HTTPException(status_code=422, detail=t("slots.invalid")) from exc
    except SlotsFull as exc:
        db.rollback()
        labels = ", ".join(
            format_slot(s.date, s.period, s.start_time, s.end_time) for s in exc.slots
        )
        return JSONResponse(
            status_code=409,
            content={
                "detail": t("slots.full_choose_others", labels=labels),
                "full_slot_ids": [s.id for s in exc.slots],
            },
        )
    waitlist_service.promote_freed(db, sender, settings, result.removed_slot_ids, now)
    db.refresh(result.booking)
    view = booking_view(result.booking, now)
    view.dropped_meals = [format_meal(day, kind) for day, kind in result.dropped_meals]
    view.dropped_activities = [
        format_activity(a.title, a.date, a.period) for a in result.dropped_activities
    ]
    return view


class MealIn(BaseModel):
    date: date
    kind: Literal["lunch", "dinner"]


class MealsIn(BaseModel):
    meals: list[MealIn] = Field(max_length=200)


MEAL_REFUSALS = {
    "not_allowed": "meals.not_allowed",
    "past_day": "meals.past_day",
}


@router.put("/me/booking/meals")
def change_my_meals(
    body: MealsIn,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
    now: datetime = Depends(get_now),
) -> BookingView:
    booking = booking_changes.get_current_booking(db, user)
    if booking is None:
        raise HTTPException(status_code=404, detail=t("booking.none"))
    try:
        result = meals_service.change_meals(
            db, sender, booking, [(m.date, m.kind) for m in body.meals], now
        )
    except booking_changes.NotEditable as exc:
        raise HTTPException(status_code=409, detail=t("booking.not_editable")) from exc
    except meals_service.MealsRefused as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=t(MEAL_REFUSALS[exc.reason])) from exc
    return booking_view(result.booking, now)


class DietaryIn(BaseModel):
    diet: Literal["omnivore", "vegetarian", "vegan"] | None = None
    allergies: str | None = Field(default=None, max_length=2000)
    consent: bool = False
    # Version of the consent text shown to the person; required with consent.
    consent_version: int | None = None


@router.put("/me/booking/dietary")
def save_my_dietary(
    body: DietaryIn,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> BookingView:
    booking = booking_changes.get_current_booking(db, user)
    if booking is None:
        raise HTTPException(status_code=404, detail=t("booking.none"))
    try:
        health_service.save_dietary(
            db, booking, body.diet, body.allergies, body.consent, now, body.consent_version
        )
    except booking_changes.NotEditable as exc:
        raise HTTPException(status_code=409, detail=t("booking.not_editable")) from exc
    except health_service.ConsentRequired as exc:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail=t("health.consent_required"),
        ) from exc
    except health_service.ConsentTextChanged as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=t("health.consent_outdated"),
        ) from exc
    except health_service.NoConsentText as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=t("health.not_available"),
        ) from exc
    return booking_view(booking, now)


class ActivitiesIn(BaseModel):
    activity_ids: list[int] = Field(max_length=200)


def activity_refusal(exc: activity_service.ActivitiesRefused) -> str:
    names = activity_service.labels(exc.activities)
    if exc.reason == "full":
        return t("activities.full", names=names)
    if exc.reason == "past_day":
        return t("activities.past_day")
    return t("activities.not_present", names=names)


@router.put("/me/booking/activities")
def change_my_activities(
    body: ActivitiesIn,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
    now: datetime = Depends(get_now),
) -> BookingView:
    booking = booking_changes.get_current_booking(db, user)
    if booking is None:
        raise HTTPException(status_code=404, detail=t("booking.none"))
    try:
        result = activity_service.change_activities(db, sender, booking, body.activity_ids, now)
    except booking_changes.NotEditable as exc:
        raise HTTPException(status_code=409, detail=t("booking.not_editable")) from exc
    except activity_service.InvalidActivities as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=t("activities.invalid")) from exc
    except activity_service.ActivitiesRefused as exc:
        db.rollback()
        status = 409 if exc.reason == "full" else 422
        raise HTTPException(status_code=status, detail=activity_refusal(exc)) from exc
    return booking_view(result.booking, now)


class ContributionIn(BaseModel):
    kind: Literal["talk", "topic", "skill"]
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


CONTRIBUTION_REFUSALS = {
    "title_required": "contribution.title_required",
    "invalid_kind": "contribution.invalid_kind",
}


@router.post("/me/contributions", status_code=201)
def add_contribution(
    body: ContributionIn,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> ContributionOut:
    booking = booking_changes.get_current_booking(db, user)
    if booking is None:
        raise HTTPException(status_code=404, detail=t("booking.none"))
    try:
        contribution = contributions_service.add(
            db, booking, body.kind, body.title, body.description, now
        )
    except booking_changes.NotEditable as exc:
        raise HTTPException(status_code=409, detail=t("booking.not_editable")) from exc
    except contributions_service.InvalidContribution as exc:
        raise HTTPException(status_code=422, detail=t(CONTRIBUTION_REFUSALS[exc.reason])) from exc
    return _contribution_out(contribution)


@router.patch("/me/contributions/{contribution_id}")
def update_contribution(
    contribution_id: int,
    body: ContributionIn,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> ContributionOut:
    try:
        contribution = contributions_service.update(
            db, user, contribution_id, body.kind, body.title, body.description, now
        )
    except contributions_service.ContributionNotFound as exc:
        raise HTTPException(status_code=404, detail=t("contribution.not_found")) from exc
    except contributions_service.InvalidContribution as exc:
        raise HTTPException(status_code=422, detail=t(CONTRIBUTION_REFUSALS[exc.reason])) from exc
    return _contribution_out(contribution)


@router.delete("/me/contributions/{contribution_id}", status_code=204)
def delete_contribution(
    contribution_id: int,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        contributions_service.remove(db, user, contribution_id)
    except contributions_service.ContributionNotFound as exc:
        raise HTTPException(status_code=404, detail=t("contribution.not_found")) from exc


class CancelOut(BaseModel):
    outcome: str


@router.post("/me/booking/cancel")
def cancel_my_booking(
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    sender: EmailSender = Depends(get_email_sender),
    settings: Settings = Depends(get_settings_dep),
    now: datetime = Depends(get_now),
) -> CancelOut:
    booking = booking_changes.get_current_booking(db, user)
    if booking is None:
        raise HTTPException(status_code=404, detail=t("booking.none"))
    freed = [s.id for s in booking.slots]
    try:
        outcome = booking_changes.request_cancellation(db, sender, booking, now)
    except booking_changes.NotEditable as exc:
        raise HTTPException(status_code=409, detail=t("booking.not_cancellable")) from exc
    waitlist_service.promote_freed(db, sender, settings, freed, now)
    return CancelOut(outcome=outcome)
