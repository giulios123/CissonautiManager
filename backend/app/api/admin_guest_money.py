"""Payments and refunds of external guests (MVP 25b). Admins only; no email is sent.

Included before the guests router so that `/movements` and `/to-collect` are not read as a
guest id.
"""

from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.admin_guests import GuestOut, _guest, _out
from app.csv_export import Amount, csv_filename, csv_response
from app.db import get_db
from app.deps import get_now, require_admin
from app.domain.external import MOVEMENT_KINDS, MOVEMENT_REFUND, PAYER_PAYING
from app.i18n import channel_label, t, tr
from app.models import Edition, ExternalGuest, ExternalMovement, Participant
from app.services import edition as edition_service
from app.services import guest_payments
from app.services import guests as guest_service
from app.services.edition import PAYMENT_CHANNELS
from app.timefmt import to_rome

router = APIRouter(
    prefix="/api/admin/guests", tags=["admin"], dependencies=[Depends(require_admin)]
)

Format = Literal["json", "csv"]
Text = Annotated[str, StringConstraints(strip_whitespace=True)]


class MovementIn(BaseModel):
    kind: Literal["payment", "refund"]
    amount_cents: int = Field(gt=0, le=1_000_000)
    channel: Literal["revolut", "satispay", "paypal", "iban"]
    paid_on: date | None = None
    note: Annotated[Text, Field(max_length=1000)] | None = None
    # The same request sent twice (double click, retry) is recorded once.
    request_key: UUID | None = None


class VoidIn(BaseModel):
    reason: Annotated[Text, Field(min_length=1, max_length=1000)]


def _edition(db: Session) -> Edition:
    edition = edition_service.get_active_edition(db)
    if edition is None:
        raise HTTPException(status_code=404, detail=t("edition.not_configured_first"))
    return edition


@router.post("/{guest_id}/movements", status_code=201)
def add_movement(
    guest_id: int,
    body: MovementIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> GuestOut:
    edition = _edition(db)
    guest = _guest(db, edition, guest_id)
    assert body.kind in MOVEMENT_KINDS
    try:
        guest_payments.record_movement(
            db,
            admin,
            edition,
            guest,
            body.kind,
            body.amount_cents,
            body.channel,
            body.paid_on or to_rome(now).date(),
            body.note,
            now,
            request_key=str(body.request_key) if body.request_key else None,
        )
    except guest_payments.MovementRequestConflict as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"code": "payment_request_conflict", "message": t("payment.retry_conflict")},
        ) from exc
    except guest_payments.MovementRefused as exc:
        db.rollback()
        key = (
            "guests.refund_too_high" if exc.reason == "refund_too_high" else "guests.invalid_amount"
        )
        raise HTTPException(status_code=422, detail=t(key)) from exc
    db.refresh(guest)
    return _out(db, edition, guest)


@router.post("/movements/{movement_id}/void")
def void_movement(
    movement_id: int,
    body: VoidIn,
    admin: Participant = Depends(require_admin),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> GuestOut:
    edition = _edition(db)
    try:
        guest = guest_payments.void_movement(db, admin, edition, movement_id, body.reason, now)
    except guest_payments.MovementNotFound as exc:
        raise HTTPException(status_code=404, detail=t("guests.movement_not_found")) from exc
    except guest_payments.AlreadyVoided as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=t("guests.movement_voided")) from exc
    except guest_payments.VoidBlocked as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=t("guests.void_blocked")) from exc
    db.refresh(guest)
    return _out(db, edition, guest)


MOVEMENTS_HEADER = [
    "Data",
    "Cognome",
    "Nome",
    "Tipo di movimento",
    "Importo",
    "Canale",
    "Stato",
    "Motivo dell'annullo",
    "Nota",
]


@router.get("/movements", response_model=None)
def list_movements(
    fmt: Format = Query(default="json", alias="format"),
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
) -> list[dict] | Response:
    edition = edition_service.get_active_edition(db)
    rows: list[tuple[ExternalMovement, ExternalGuest]] = []
    if edition is not None:
        for movement in db.scalars(
            select(ExternalMovement)
            .where(ExternalMovement.edition_id == edition.id)
            .order_by(ExternalMovement.paid_on, ExternalMovement.id)
        ):
            guest = db.get(ExternalGuest, movement.guest_id)
            assert guest is not None
            rows.append((movement, guest))
    if fmt == "csv":
        return csv_response(
            csv_filename("movimenti-esterni", now),
            MOVEMENTS_HEADER,
            [
                [
                    m.paid_on,
                    g.last_name,
                    g.first_name,
                    tr("Restituzione" if m.kind == MOVEMENT_REFUND else "Pagamento"),
                    Amount(m.amount_cents),
                    channel_label(m.channel, PAYMENT_CHANNELS.get(m.channel, m.channel)),
                    tr("Annullato" if m.voided_at else "Valido"),
                    m.void_reason,
                    m.note,
                ]
                for m, g in rows
            ],
        )
    return [
        {
            "id": m.id,
            "guest_id": g.id,
            "first_name": g.first_name,
            "last_name": g.last_name,
            "kind": m.kind,
            "amount_cents": m.amount_cents,
            "channel": m.channel,
            "paid_on": m.paid_on,
            "voided": m.voided_at is not None,
        }
        for m, g in rows
    ]


class CollectGuestOut(BaseModel):
    guest_id: int
    first_name: str
    last_name: str
    reference: str | None
    items: list[guest_payments.Item]
    due_cents: int
    paid_cents: int
    balance_cents: int


@router.get("/to-collect")
def guests_to_collect(
    q: str = Query(default="", max_length=100),
    db: Session = Depends(get_db),
) -> list[CollectGuestOut]:
    """Paying guests with something still to pay, by surname. Never mixed with the bookings."""
    edition = edition_service.get_active_edition(db)
    if edition is None:
        return []
    needle = " ".join(q.split()).casefold()
    rows: list[CollectGuestOut] = []
    by_guest = guest_payments.movements_by_guest(db, edition)
    for guest in guest_service.list_guests(db, edition):
        if guest.payer != PAYER_PAYING:
            continue
        if needle and needle not in f"{guest.first_name} {guest.last_name}".casefold():
            continue
        account = guest_payments.account_of(edition, guest, by_guest.get(guest.id, []))
        if account.to_collect_cents <= 0:
            continue
        rows.append(
            CollectGuestOut(
                guest_id=guest.id,
                first_name=guest.first_name,
                last_name=guest.last_name,
                reference=guest.reference,
                items=[i for i in guest_payments.items_of(edition, guest) if i.collectable_cents],
                due_cents=account.due_cents,
                paid_cents=account.net_cents,
                balance_cents=account.balance_cents,
            )
        )
    return rows
