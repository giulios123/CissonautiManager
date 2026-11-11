"""Deliveries of the benefits of the edition (MVP 30). Admins only.

Names, category and state only: no email, phone, allergies or amounts.
"""

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy.orm import Session

from app.csv_export import csv_filename, csv_response
from app.db import get_db
from app.deps import get_now, require_admin
from app.i18n import current_locale, t, tr
from app.models import Benefit, BenefitDelivery, Edition, Participant
from app.services import benefit_deliveries as service
from app.services import edition as edition_service

router = APIRouter(
    prefix="/api/admin/deliveries", tags=["admin"], dependencies=[Depends(require_admin)]
)

Format = Literal["json", "csv"]
Text = Annotated[str, StringConstraints(strip_whitespace=True)]
CATEGORY_LABELS = {"ordinary": "Ordinaria", "internal_non_paying": "Interno non pagante"}
STATE_LABELS = {
    "to_deliver": "Da consegnare",
    "delivered": "Consegnato",
    "delivered_without_entitlement": "Consegnato (senza diritto attuale)",
}


class DeliveryIn(BaseModel):
    participant_id: int = Field(ge=1)
    benefit_id: int = Field(ge=1)
    request_key: Annotated[Text, Field(min_length=8, max_length=36)] | None = None


class AnnulIn(BaseModel):
    reason: Annotated[Text, Field(max_length=200)] = ""


class BenefitOut(BaseModel):
    id: int
    name: str
    retired: bool
    delivered: int
    entitled: int


class DeliveryOut(BaseModel):
    id: int
    delivered_at: datetime
    delivered_by: str


class AnnulledOut(BaseModel):
    id: int
    delivered_at: datetime
    annulled_at: datetime
    annulled_by: str
    reason: str


class RowOut(BaseModel):
    participant_id: int
    first_name: str
    last_name: str
    booking_id: int | None
    category: str | None
    entitled: bool
    state: str
    delivery: DeliveryOut | None
    annulled: list[AnnulledOut]


def _edition(db: Session) -> Edition:
    edition = edition_service.get_active_edition(db)
    if edition is None:
        raise HTTPException(status_code=404, detail=t("edition.not_configured_first"))
    return edition


def _name(benefit: Benefit) -> str:
    return benefit.name_it if current_locale() == "it" else benefit.name_en


def _person(person: Participant) -> str:
    return f"{person.first_name} {person.last_name}".strip()


def _row(row: service.Row) -> RowOut:
    active = row.active
    return RowOut(
        participant_id=row.participant_id,
        first_name=row.first_name,
        last_name=row.last_name,
        booking_id=row.booking_id,
        category=row.category,
        entitled=row.entitled,
        state=row.state,
        delivery=DeliveryOut(
            id=active.id,
            delivered_at=active.delivered_at,
            delivered_by=_person(active.delivered_by),
        )
        if active
        else None,
        annulled=[
            AnnulledOut(
                id=a.id,
                delivered_at=a.delivered_at,
                annulled_at=a.annulled_at,
                annulled_by=_person(a.annulled_by) if a.annulled_by else "",
                reason=a.annul_reason or "",
            )
            for a in row.annulled
            if a.annulled_at is not None
        ],
    )


@router.get("/benefits")
def list_benefits(
    db: Session = Depends(get_db), now: datetime = Depends(get_now)
) -> list[BenefitOut]:
    """The benefits that can be delivered, with the counters of delivered and entitled."""
    return [
        BenefitOut(
            id=item["benefit"].id,
            name=_name(item["benefit"]),
            retired=item["benefit"].retired,
            delivered=item["delivered"],
            entitled=item["entitled"],
        )
        for item in service.catalogue(db, _edition(db), now)
    ]


@router.get("", response_model=None)
def list_deliveries(
    benefit_id: int,
    q: Annotated[str, Query(max_length=100)] = "",
    state: Literal["all", "pending", "delivered"] = "all",
    fmt: Format = Query(default="json", alias="format"),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> list[RowOut] | Response:
    edition = _edition(db)
    try:
        benefit = service.get_benefit(db, edition, benefit_id)
    except service.BenefitNotFound as exc:
        raise HTTPException(status_code=404, detail=t("benefit.not_found")) from exc
    rows = service.rows_for(db, edition, benefit, now, q, state)
    if fmt == "csv":
        header = [
            "Nome",
            "Cognome",
            "Categoria",
            "Stato",
            "Consegnato il",
            "Consegnato da",
            "Consegne annullate",
        ]
        csv_rows = [
            [
                r.first_name,
                r.last_name,
                tr(CATEGORY_LABELS.get(r.category or "", "")) if r.category else "",
                tr(STATE_LABELS[r.state]),
                r.active.delivered_at if r.active else "",
                _person(r.active.delivered_by) if r.active else "",
                len(r.annulled),
            ]
            for r in rows
        ]
        return csv_response(
            csv_filename(f"{tr('Consegne')}-{_name(benefit)}", now), header, csv_rows
        )
    return [_row(r) for r in rows]


@router.post("", response_model=None)
def deliver(
    body: DeliveryIn,
    response: Response,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> dict:
    edition = _edition(db)
    try:
        delivery, created = service.deliver(
            db, admin, edition, body.participant_id, body.benefit_id, body.request_key, now
        )
    except service.BenefitNotFound as exc:
        raise HTTPException(status_code=404, detail=t("benefit.not_found")) from exc
    except service.PersonNotFound as exc:
        raise HTTPException(status_code=404, detail=t("delivery.person_not_found")) from exc
    except service.BenefitRetired as exc:
        raise HTTPException(status_code=422, detail=t("benefit.retired")) from exc
    except service.NotEntitled as exc:
        raise HTTPException(status_code=422, detail=t("delivery.not_entitled")) from exc
    response.status_code = 201 if created else 200
    return _ids(delivery, created)


@router.post("/{delivery_id}/annul", response_model=None)
def annul(
    delivery_id: int,
    body: AnnulIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> dict:
    try:
        delivery, changed = service.annul(db, admin, _edition(db), delivery_id, body.reason, now)
    except service.DeliveryNotFound as exc:
        raise HTTPException(status_code=404, detail=t("delivery.not_found")) from exc
    except service.ReasonRequired as exc:
        raise HTTPException(status_code=422, detail=t("delivery.reason_required")) from exc
    return _ids(delivery, changed)


def _ids(delivery: BenefitDelivery, changed: bool) -> dict:
    return {
        "id": delivery.id,
        "participant_id": delivery.participant_id,
        "benefit_id": delivery.benefit_id,
        "changed": changed,
    }
