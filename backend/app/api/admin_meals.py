"""Configure who collects the price of a specific lunch or dinner."""

from datetime import date, datetime
from typing import Annotated, Literal, Self

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, StringConstraints, model_validator
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_email_sender, get_now, require_admin
from app.email import EmailSender
from app.i18n import t
from app.models import MealSetting, Participant
from app.services import audit
from app.services import edition as edition_service
from app.services.amounts import meal_terms
from app.services.payments import paid_total, send_transition_confirmation
from app.services.pricing import reprice

router = APIRouter(prefix="/api/admin/meals", tags=["admin"], dependencies=[Depends(require_admin)])


class MealSettingIn(BaseModel):
    payment_mode: Literal["organizer", "provider"] = "organizer"
    price_cents: int | None = Field(default=None, ge=0, le=1_000_000)
    payment_instructions: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=5000)] | None
    ) = None

    @model_validator(mode="after")
    def provider_terms(self) -> Self:
        if self.payment_mode == "provider" and (
            self.price_cents is None or not self.payment_instructions
        ):
            raise ValueError(t("collection.terms_required"))
        return self


@router.put("/{day}/{kind}")
def set_meal_terms(
    day: date,
    kind: Literal["lunch", "dinner"],
    body: MealSettingIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
    sender: EmailSender = Depends(get_email_sender),
) -> dict:
    edition = edition_service.get_active_edition(db)
    if (
        edition is None
        or not edition.start_date
        or not edition.end_date
        or not edition.start_date <= day <= edition.end_date
    ):
        raise HTTPException(status_code=422, detail=t("activity.outside_edition"))
    before = meal_terms(edition, day, kind)
    setting = db.get(MealSetting, (edition.id, day, kind))
    if setting is None:
        setting = MealSetting(date=day, kind=kind)
        edition.meal_settings.append(setting)
    setting.payment_mode = body.payment_mode
    setting.price_cents = body.price_cents if body.payment_mode == "provider" else None
    setting.payment_instructions = (
        body.payment_instructions if body.payment_mode == "provider" else None
    )
    db.flush()
    after = meal_terms(edition, day, kind)
    audit.log(db, admin, "meal_setting_changed", f"Pasto {day} {kind}: {before} → {after}")
    financial_change = (before["price_cents"], before["payment_mode"]) != (
        after["price_cents"],
        after["payment_mode"],
    )
    confirmed = reprice(db, edition, admin, now, meal=(day, kind)) if financial_change else []
    db.commit()
    for booking in confirmed:
        send_transition_confirmation(db, sender, booking, paid_total(booking), now)
    return after
