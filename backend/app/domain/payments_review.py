from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
)

EXPIRED_WITH_PAYMENTS = "scaduta_con_pagamenti"
BALANCE_DUE = "saldo_positivo"
CREDIT = "credito"
CANCELLATION_TO_REFUND = "disdetta_da_rimborsare"
CANCELLATION_TO_CLOSE = "disdetta_da_chiudere"
PARTIAL_PAYMENT = "pagamento_parziale"

REASON_LABELS = {
    EXPIRED_WITH_PAYMENTS: "Scaduta con pagamenti registrati",
    BALANCE_DUE: "Confermata con una differenza da versare",
    CREDIT: "Confermata con un credito (ha versato in più)",
    CANCELLATION_TO_REFUND: "Disdetta richiesta: da rimborsare",
    CANCELLATION_TO_CLOSE: "Disdetta richiesta senza pagamenti: da chiudere",
    PARTIAL_PAYMENT: "In attesa con un pagamento parziale",
}


def review_reason(status: str, due_cents: int, paid_cents: int) -> str | None:
    """Why an admin should look at this booking, or None when it is all in order."""
    if status == STATUS_EXPIRED and paid_cents > 0:
        return EXPIRED_WITH_PAYMENTS
    if status == STATUS_CONFIRMED:
        if paid_cents < due_cents:
            return BALANCE_DUE
        if paid_cents > due_cents:
            return CREDIT
    if status == STATUS_CANCEL_REQUESTED:
        # Still open until an admin marks it refunded, even when nothing was ever paid.
        return CANCELLATION_TO_REFUND if paid_cents > 0 else CANCELLATION_TO_CLOSE
    if status == STATUS_PENDING and paid_cents > 0 and paid_cents < due_cents:
        return PARTIAL_PAYMENT
    return None
