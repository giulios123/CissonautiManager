from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_now, require_admin
from app.models import Participant
from app.services import waitlist as waitlist_service

router = APIRouter(
    prefix="/api/admin/waitlist", tags=["admin"], dependencies=[Depends(require_admin)]
)


@router.delete("/{entry_id}", status_code=204)
def remove_from_waitlist(
    entry_id: int,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> None:
    try:
        waitlist_service.remove(db, admin, entry_id, now)
    except waitlist_service.EntryNotFound as exc:
        raise HTTPException(status_code=404, detail="Voce della lista non trovata") from exc
