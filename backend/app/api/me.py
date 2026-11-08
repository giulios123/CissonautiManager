from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.public import _MUNICIPALITIES, ChannelPublic, LegalPublic
from app.api.schemas import ActivityOffer, BookingView, activity_offers, booking_view
from app.config import Settings
from app.db import get_db
from app.deps import (
    current_user,
    get_email_sender,
    get_now,
    get_settings_dep,
    require_privacy_acceptance,
)
from app.domain.profile import InvalidProfileValue, validate_geography, validate_social_profiles
from app.email import EmailSender
from app.i18n import channel_label, t
from app.models import (
    DOC_HEALTH,
    DOC_PRIVACY,
    ConsentEvent,
    LegalDocument,
    STATUS_CONFIRMED,
    Booking,
    Contribution,
    Edition,
    Participant,
    ParticipantEditionProfile,
    WaitlistEntry,
)
from app.services import activities as activity_service
from app.services import booking_changes
from app.services import consents as consent_service
from app.services import contributions as contributions_service
from app.services import edition as edition_service
from app.services import health as health_service
from app.services import meals as meals_service
from app.services import privacy as privacy_service
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
    profile_complete: bool = True
    privacy_associated: bool = False
    privacy_acceptance_required: bool = False


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


class PrivacyDocumentView(BaseModel):
    id: int
    version: int
    body: str
    body_it: str | None
    body_en: str | None
    is_legacy: bool


class PrivacyAcceptanceView(BaseModel):
    id: int
    locale: str | None
    recorded_at: datetime
    source: str
    document: PrivacyDocumentView


class PrivacyStateView(BaseModel):
    edition_id: int | None
    associated: bool
    required: bool
    current_document: PrivacyDocumentView | None
    accepted_document_id: int | None
    history: list[PrivacyAcceptanceView]


class PrivacyAcceptanceIn(BaseModel):
    document_id: int
    version: int
    locale: Literal["it", "en"]
    accepted: Literal[True]


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
    profile = (
        db.scalar(
            select(ParticipantEditionProfile).where(
                ParticipantEditionProfile.participant_id == user.id,
                ParticipantEditionProfile.edition_id == edition.id,
            )
        )
        if edition
        else None
    )
    profile_complete = edition is None or bool(
        user.phone
        and user.telegram
        and user.linkedin
        and profile
        and (
            profile.country.casefold() not in {"italia", "italy"}
            or profile.istat_code
            or profile.province
        )
    )
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
        profile_complete=profile_complete,
        privacy_associated=(
            edition is not None and consent_service.has_edition_association(db, edition, user)
        ),
        privacy_acceptance_required=privacy_service.acceptance_required(db, edition, user),
    )


class ProfileIn(BaseModel):
    phone: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
    telegram: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    linkedin: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
    city: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    province: Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)] | None = None
    region: Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)] | None = None
    country: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    istat_code: Annotated[str, StringConstraints(strip_whitespace=True, max_length=12)] | None = (
        None
    )
    job_title: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
    ]
    company: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    expectations: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)
    ]
    attended_previous: bool


@router.get("/me/profile")
def get_my_profile(user: Participant = Depends(current_user), db: Session = Depends(get_db)):
    edition = edition_service.get_active_edition(db)
    profile = (
        db.scalar(
            select(ParticipantEditionProfile).where(
                ParticipantEditionProfile.participant_id == user.id,
                ParticipantEditionProfile.edition_id == edition.id,
            )
        )
        if edition
        else None
    )
    previous = (
        db.scalar(
            select(Edition)
            .where(
                Edition.end_date < edition.start_date,
            )
            .order_by(Edition.end_date.desc())
        )
        if edition and edition.start_date
        else None
    )
    values = (
        {
            "city": profile.city,
            "province": profile.province,
            "region": profile.region,
            "country": profile.country,
            "istat_code": profile.istat_code,
            "job_title": profile.job_title,
            "company": profile.company,
            "expectations": profile.expectations,
            "attended_previous": profile.attended_previous,
            "attendance_source": profile.attendance_source,
            "previous_edition_id": profile.previous_edition_id,
        }
        if profile
        else {}
    )
    missing = (
        [
            key
            for key, value in {
                "phone": user.phone,
                "telegram": user.telegram,
                "linkedin": user.linkedin,
                "city": values.get("city"),
                "country": values.get("country"),
                "job_title": values.get("job_title"),
                "company": values.get("company"),
                "expectations": values.get("expectations"),
                "attended_previous": values.get("attended_previous"),
                "province": (
                    values.get("province")
                    if values.get("country", "").casefold() in {"italia", "italy"}
                    and not values.get("istat_code")
                    else True
                ),
            }.items()
            if value is None or value == ""
        ]
        if edition
        else []
    )
    return {
        "edition_id": edition.id if edition else None,
        "complete": not missing,
        "missing_fields": missing,
        "profile": values or None,
        "phone": user.phone,
        "telegram": user.telegram,
        "linkedin": user.linkedin,
        "previous_edition_id": previous.id if previous else None,
    }


@router.put("/me/profile", status_code=204)
def update_my_profile(
    body: ProfileIn, user: Participant = Depends(current_user), db: Session = Depends(get_db)
) -> None:
    edition = edition_service.get_active_edition(db)
    if edition is None:
        raise HTTPException(status_code=409, detail=t("profile.no_active_edition"))
    try:
        validate_social_profiles(body.telegram, body.linkedin)
        validate_geography(
            body.city,
            body.country,
            body.province,
            body.istat_code,
            _MUNICIPALITIES,
        )
    except InvalidProfileValue as exc:
        raise HTTPException(status_code=422, detail=t(exc.message_key)) from exc
    values = body.model_dump()
    user.phone = values.pop("phone").strip()
    user.telegram = values.pop("telegram").strip()
    user.linkedin = values.pop("linkedin").strip()
    previous = (
        db.scalar(
            select(Edition)
            .where(Edition.end_date < edition.start_date)
            .order_by(Edition.end_date.desc())
        )
        if edition.start_date
        else None
    )
    confirmed_previous = bool(
        previous
        and db.scalar(
            select(Booking.id)
            .where(
                Booking.participant_id == user.id,
                Booking.edition_id == previous.id,
                Booking.status == STATUS_CONFIRMED,
            )
            .limit(1)
        )
    )
    if confirmed_previous:
        values["attended_previous"] = True
    existing = db.scalar(
        select(ParticipantEditionProfile).where(
            ParticipantEditionProfile.participant_id == user.id,
            ParticipantEditionProfile.edition_id == edition.id,
        )
    )
    if existing is None:
        existing = ParticipantEditionProfile(
            participant_id=user.id,
            edition_id=edition.id,
            attendance_source="derived" if confirmed_previous else "declared",
            previous_edition_id=previous.id if previous else None,
            **values,
        )
        db.add(existing)
    else:
        for key, value in values.items():
            setattr(existing, key, value)
        existing.attendance_source = "derived" if confirmed_previous else "declared"
        existing.previous_edition_id = previous.id if previous else None
    db.commit()


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


def _privacy_document(document: LegalDocument | None) -> PrivacyDocumentView | None:
    if document is None:
        return None
    return PrivacyDocumentView(
        id=document.id,
        version=document.version,
        body=document.body,
        body_it=document.body_it,
        body_en=document.body_en,
        is_legacy=document.body_it is None or document.body_en is None,
    )


def _privacy_state(db: Session, edition: Edition | None, user: Participant) -> PrivacyStateView:
    if edition is None:
        return PrivacyStateView(
            edition_id=None,
            associated=False,
            required=False,
            current_document=None,
            accepted_document_id=None,
            history=[],
        )
    associated = consent_service.has_edition_association(db, edition, user)
    current = edition_service.latest_legal_document(db, edition, DOC_PRIVACY)
    history = list(
        db.scalars(
            select(ConsentEvent)
            .options(joinedload(ConsentEvent.document))
            .where(
                ConsentEvent.edition_id == edition.id,
                ConsentEvent.participant_id == user.id,
                ConsentEvent.kind == DOC_PRIVACY,
                ConsentEvent.action == "accepted",
            )
            .order_by(ConsentEvent.recorded_at, ConsentEvent.id)
        )
    )
    latest = privacy_service.latest_acceptance(db, edition, user)
    return PrivacyStateView(
        edition_id=edition.id,
        associated=associated,
        required=privacy_service.acceptance_required(db, edition, user),
        current_document=_privacy_document(current),
        accepted_document_id=latest.document_id if latest is not None else None,
        history=[
            PrivacyAcceptanceView(
                id=event.id,
                locale=event.locale,
                recorded_at=event.recorded_at,
                source=event.source,
                document=_privacy_document(event.document),
            )
            for event in history
        ],
    )


@router.get("/me/privacy", response_model=PrivacyStateView)
def get_my_privacy(
    response: Response,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
) -> PrivacyStateView:
    response.headers["Cache-Control"] = "private, no-store"
    return _privacy_state(db, edition_service.get_active_edition(db), user)


@router.post("/me/privacy/accept", response_model=PrivacyStateView)
def accept_my_privacy(
    body: PrivacyAcceptanceIn,
    response: Response,
    user: Participant = Depends(current_user),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> PrivacyStateView:
    response.headers["Cache-Control"] = "private, no-store"
    edition = edition_service.get_active_edition(db)
    if edition is None or not consent_service.has_edition_association(db, edition, user):
        raise HTTPException(status_code=404, detail=t("consent.association_not_found"))
    try:
        privacy_service.accept_current(
            db,
            edition,
            user,
            document_id=body.document_id,
            version=body.version,
            locale=body.locale,
            now=now,
            allow_legacy=False,
        )
    except privacy_service.PrivacyDocumentConflict as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=t("privacy.version_changed")) from exc
    db.commit()
    return _privacy_state(db, edition, user)


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


@router.post("/me/waitlist", status_code=201, dependencies=[Depends(require_privacy_acceptance)])
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


@router.put(
    "/me/booking/slots",
    response_model=None,
    dependencies=[Depends(require_privacy_acceptance)],
)
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


@router.put("/me/booking/meals", dependencies=[Depends(require_privacy_acceptance)])
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


@router.put("/me/booking/activities", dependencies=[Depends(require_privacy_acceptance)])
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


@router.post(
    "/me/contributions", status_code=201, dependencies=[Depends(require_privacy_acceptance)]
)
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


@router.patch(
    "/me/contributions/{contribution_id}",
    dependencies=[Depends(require_privacy_acceptance)],
)
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


@router.delete(
    "/me/contributions/{contribution_id}",
    status_code=204,
    dependencies=[Depends(require_privacy_acceptance)],
)
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
