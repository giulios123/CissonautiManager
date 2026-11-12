"""Hide a participant's proposal from the others, or show it again (MVP 27). Admins only."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, StringConstraints
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_now, require_admin
from app.i18n import t
from app.models import Participant
from app.services import contributions as contributions_service

router = APIRouter(prefix="/api/admin/contributions", tags=["admin"])


class HideIn(BaseModel):
    reason: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None = None


class HiddenOut(BaseModel):
    id: int
    hidden: bool


def _set(
    contribution_id: int,
    hidden: bool,
    reason: str | None,
    admin: Participant,
    db: Session,
    now: datetime,
) -> HiddenOut:
    try:
        contributions_service.set_hidden(db, admin, contribution_id, hidden, reason, now)
    except contributions_service.ContributionNotFound as exc:
        raise HTTPException(status_code=404, detail=t("contribution.not_found")) from exc
    return HiddenOut(id=contribution_id, hidden=hidden)


@router.post("/{contribution_id}/hide")
def hide(
    contribution_id: int,
    body: HideIn | None = None,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> HiddenOut:
    return _set(contribution_id, True, body.reason if body else None, admin, db, now)


@router.post("/{contribution_id}/unhide")
def unhide(
    contribution_id: int,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> HiddenOut:
    return _set(contribution_id, False, None, admin, db, now)
