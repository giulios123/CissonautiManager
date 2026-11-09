# MVP 25b · Design

## Dati e migrazione `0025_external_movements`

Migrazione additiva dopo `0024_external_guests`.

- **`external_movement`**: `id`, `edition_id` (FK, indicizzato), `guest_id` (FK a `external_guest`, indicizzato), `kind` (`payment` | `refund`), `amount_cents` (> 0, vincolo di controllo), `channel` (codice di `PaymentChannel`, come in `Payment.channel`), `paid_on`, `note`, `recorded_by_id`, `created_at`, `voided_at`, `voided_by_id`, `void_reason`, `request_key` (nullable).
- Indice univoco parziale su `request_key` dove non è nullo, come `uq_payment_request_key` della migrazione `0021` (compatibile con SQL Server).

Il registro è separato da `Payment`: nessuna FK a `booking`. Importi sempre in centesimi interi.

## Regole pure (`domain/external.py`)

- `guest_due(items, payer)`: somma di `collectable(price, mode)` (`domain/collection.py`) sulle voci; `non_paying` → 0. Nessuna quota, nessun pasto compreso.
- `guest_paid(movements)`: pagamenti attivi meno restituzioni attive (esclusi gli annullati).
- `guest_balance(due, paid)`: `due - paid`; negativo = credito.
- `can_refund_guest(amount, balance)`: `0 < amount <= -balance`.

I prezzi delle voci arrivano da `meal_terms(edition, day, kind)` e `activity_terms(activity)` di `services/amounts.py`, senza duplicare la logica (D-029). Il dovuto non è salvato: si calcola alla lettura, quindi non servono ricalcoli né un `reprice` per gli esterni.

## Servizi

- `services/guest_payments.py`: `record_movement(db, guest, kind, ...)`, `void_movement(...)`. Blocco su `lock_edition` come ogni scrittura (già garantito da `get_db` per le richieste non GET); controllo del saldo dopo aver riletto i movimenti, per evitare due restituzioni concorrenti oltre il credito. L'idempotenza usa `request_key` come in `payments.record_payment`: stesso invio → stessa risposta, nessun secondo movimento. Ogni azione scrive in `audit.log`.
- `services/guests.py` (25a): l'eliminazione rifiuta con 409 `guests.has_movements` se esiste un movimento.
- `services/views.py`: `collect_rows` aggiunge `externals`; `load_report` aggiunge la sezione esterni.

## API

Estensioni di `api/admin_guests.py` (router già protetto da `require_admin`):

- `GET /{id}` e l'elenco aggiungono `due_cents`, `paid_cents`, `balance_cents`, `movements[]`.
- `POST /{id}/movements`: `{kind, amount_cents, channel, paid_on, note, request_key}`; 422 `guests.refund_too_high` se oltre il credito; 422 per canale non attivo.
- `POST /movements/{mid}/void`: `{reason}` obbligatorio; 409 se già annullato.
- `GET /movements?format=csv`: CSV dei movimenti, intestazioni tradotte via `LABELS_EN`.
- `GET /api/admin/views/to-collect` aggiunge `externals` (solo paganti con `balance_cents > 0`, ricerca per nome).
- `GET /api/admin/views/report` e il CSV del report aggiungono la sezione `external_revenue`.

Sezione del report (`domain/report.py`, `RevenueSection`): `external_due_cents`, `external_paid_cents`, `external_refunded_cents`, `external_to_collect_cents`, `external_credit_cents`, e `event_net_cents` = netto quote + netto esterni. `report_export.py` aggiunge le righe «Incassi esterni» e «Totale evento». Le voci al fornitore restano fuori da entrambi i totali.

## Frontend

- `AdminGuests.tsx`: dettaglio con dovuto, versato, saldo e registro dei movimenti (annullati barrati); modulo per pagamento e restituzione; campo `request_key` generato dal client a ogni apertura del modulo.
- `AdminCollect.tsx`: sezione «Esterni» con finestra di incasso derivata da `QuickPaymentDialog` ma senza ritardo dell'email né annullo a 10 secondi.
- `AdminReport.tsx`: sezione «Incassi esterni» e «Totale evento».
- Chiavi i18n IT/EN; guide `16-guests`, `12-to-collect`, `07-report`.

## Impatti sugli MVP precedenti

- MVP 10 (Da incassare): una sezione in più; la logica per gli iscritti non cambia.
- MVP 7 (report): il totale incassato ora è l'«evento» e va distinto dal netto delle quote; le etichette lo dicono esplicitamente.
- MVP 16: i pagamenti al fornitore restano fuori; stessa funzione `collectable`.

## Verifiche

Test di dominio per dovuto, saldo, credito, tetto della restituzione, voce al fornitore, non pagante, cambio da pagante a non pagante dopo un versamento. Test API: 403, doppio invio con la stessa chiave, restituzione oltre il credito, annullo con motivo, eliminazione bloccata, canale non attivo. Riconciliazione in `test_report.py`: +6 € da un esterno portano il totale evento a +6 €, le quote e i `Payment` dei booking restano identici, il costo al fornitore non compare. Migrazione da zero e da `0024` su SQLite e SQL Server. `test_i18n_admin.py` per il CSV dei movimenti.

## Modifiche a domain.md

Vedere [requirements.md](requirements.md#modifiche-a-domainmd). Applicarla solo dopo approvazione.
