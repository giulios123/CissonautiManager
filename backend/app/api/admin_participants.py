from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, StringConstraints
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.public import _MUNICIPALITIES, _fold
from app.db import get_db
from app.deps import get_now, require_admin
from app.i18n import t
from app.models import Edition, Participant, ParticipantEditionProfile
from app.services import audit as audit_service
from app.services import consents as consent_service
from app.services import edition as edition_service
from app.services import plus_one as plus_one_service

router = APIRouter(
    prefix="/api/admin/participants", tags=["admin"], dependencies=[Depends(require_admin)]
)


class PlusOneIn(BaseModel):
    verified: bool


class PlusOneOut(BaseModel):
    participant_id: int
    verified: bool
    verified_at: datetime | None
    verified_by: str | None


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
    edition_id: int
    associated: bool
    consents: list[OptionalConsentView]


class ParticipantProfileIn(BaseModel):
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


@router.get("/{participant_id}/profile")
def get_participant_profile(participant_id: int, db: Session = Depends(get_db)):
    participant = db.get(Participant, participant_id)
    if participant is None:
        raise HTTPException(status_code=404, detail=t("person.not_found"))
    edition = edition_service.get_active_edition(db)
    profile = (
        db.scalar(
            select(ParticipantEditionProfile).where(
                ParticipantEditionProfile.participant_id == participant_id,
                ParticipantEditionProfile.edition_id == edition.id,
            )
        )
        if edition
        else None
    )
    fields = (
        "city",
        "province",
        "region",
        "country",
        "istat_code",
        "job_title",
        "company",
        "expectations",
        "attended_previous",
        "attendance_source",
        "previous_edition_id",
    )
    return {
        "phone": participant.phone,
        "telegram": participant.telegram,
        "linkedin": participant.linkedin,
        "profile": {key: getattr(profile, key) for key in fields} if profile else None,
    }


@router.put("/{participant_id}/profile", status_code=204)
def put_participant_profile(
    participant_id: int,
    body: ParticipantProfileIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    participant = db.get(Participant, participant_id)
    edition = edition_service.get_active_edition(db)
    if participant is None:
        raise HTTPException(status_code=404, detail=t("person.not_found"))
    if edition is None:
        raise HTTPException(status_code=404, detail=t("edition.none"))
    values = body.model_dump()
    if values["telegram"].strip().casefold() not in {
        "none",
        "non possiedo",
        "i don't have it",
    } and not values["telegram"].strip().startswith("@"):
        raise HTTPException(status_code=422, detail=t("profile.invalid_telegram"))
    if values["linkedin"].strip().casefold() not in {
        "none",
        "non possiedo",
        "i don't have it",
    } and not values["linkedin"].startswith("https://www.linkedin.com/"):
        raise HTTPException(status_code=422, detail=t("profile.invalid_linkedin"))
    if values["istat_code"]:
        municipality = next(
            (item for item in _MUNICIPALITIES if item["istat_code"] == values["istat_code"]), None
        )
        if (
            municipality is None
            or values["country"].casefold() not in {"italia", "italy"}
            or _fold(municipality["name"]) != _fold(values["city"])
            or municipality["province"] != (values["province"] or "")
        ):
            raise HTTPException(status_code=422, detail=t("profile.invalid_municipality"))
    elif values["country"].casefold() in {"italia", "italy"} and not values["province"]:
        raise HTTPException(status_code=422, detail=t("profile.province_required"))
    participant.phone = values.pop("phone").strip()
    participant.telegram = values.pop("telegram").strip()
    participant.linkedin = values.pop("linkedin").strip()
    profile = db.scalar(
        select(ParticipantEditionProfile).where(
            ParticipantEditionProfile.participant_id == participant_id,
            ParticipantEditionProfile.edition_id == edition.id,
        )
    )
    if profile is None:
        db.add(
            ParticipantEditionProfile(
                participant_id=participant_id,
                edition_id=edition.id,
                attendance_source="admin",
                **values,
            )
        )
    else:
        for key, value in values.items():
            setattr(profile, key, value)
        profile.attendance_source = "admin"
    audit_service.log(
        db, admin, "participant_profile_updated", f"Profile updated for {participant.email}"
    )
    db.commit()


@router.put("/{participant_id}/plus-one")
def put_plus_one(
    participant_id: int,
    body: PlusOneIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> PlusOneOut:
    """Confirm (or take back) that the person was invited by who they say. Works for people who
    are only on a waitlist too, so it is keyed by the person and not by a booking."""
    participant = db.get(Participant, participant_id)
    if participant is None:
        raise HTTPException(status_code=404, detail=t("person.not_found"))
    try:
        plus_one_service.set_verified(db, admin, participant, body.verified, now)
    except plus_one_service.NothingToVerify as exc:
        raise HTTPException(
            status_code=422,
            detail=t("plus_one.needs_inviter"),
        ) from exc
    return PlusOneOut(
        participant_id=participant.id,
        verified=plus_one_service.is_verified(participant),
        verified_at=participant.plus_one_verified_at,
        verified_by=plus_one_service.verified_by_name(db, participant),
    )


@router.get("/{participant_id}/consents", response_model=ConsentCollectionView)
def get_participant_consents(
    participant_id: int,
    response: Response,
    db: Session = Depends(get_db),
) -> ConsentCollectionView:
    response.headers["Cache-Control"] = "private, no-store"
    participant = db.get(Participant, participant_id)
    if participant is None:
        raise HTTPException(status_code=404, detail=t("person.not_found"))
    edition: Edition | None = edition_service.get_active_edition(db)
    if edition is None:
        raise HTTPException(status_code=404, detail=t("edition.none"))
    snapshot = consent_service.collection_snapshot(db, edition, participant)
    if not snapshot["associated"]:
        raise HTTPException(status_code=404, detail=t("consent.association_not_found"))
    return ConsentCollectionView.model_validate(snapshot)
