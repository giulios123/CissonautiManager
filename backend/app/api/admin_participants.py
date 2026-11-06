from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_now, require_admin
from app.i18n import t
from app.models import Participant
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
