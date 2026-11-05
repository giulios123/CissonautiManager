# MVP 3 · Pannello admin completo · Design

## Modello dati (migrazione 0004)

Su `booking`:

| Campo | Scopo |
|-------|-------|
| `refund_cents` (nullable int) | importo rimborsato |
| `refunded_at` | quando |
| `refund_note` | nota |
| `refunded_by_id` | admin che l'ha registrato |

Su `payment`: `voided_at`, `voided_by_id`, `void_reason`. Un pagamento annullato non conta nel pagato ma resta in elenco.

Nuova tabella `audit_log`: `id`, `at`, `actor_id`, `booking_id` (nullable), `action` (stringa breve), `detail` (testo con prima e dopo). Alimentata da ogni azione manuale dell'admin: modifica anagrafica, modifica slot, proroga, disdetta, riattivazione, rimborso, annullamento pagamento, aggiunta e rimozione admin. La scheda mostra la cronologia.

`paid_total` (in `services/payments.py`) e `booking_view` (in `api/schemas.py`) escludono i pagamenti annullati; `PaymentView` espone `voided` e `void_reason`.

## Regole di dominio (funzioni pure)

In `app/domain/presence.py`:

- `has_evening(periods: set[str]) -> bool`: sera esplicita oppure mattina e pomeriggio (D-009).
- `presence_by_slot(...)`: per slot, elenco dei presenti con flag `derived` per la sera derivata.
- `week_summary(...)`: conteggi per giorno e totale di persone distinte.

In `app/domain/payments_review.py`:

- `review_reason(status, due, paid, refund_cents) -> str | None`: uno tra `scaduta_con_pagamenti`, `saldo_positivo`, `credito`, `disdetta_da_rimborsare`, `pagamento_parziale`, oppure `None`.

In `app/domain/admins.py`:

- `can_remove_admin(target_id, actor_id, admin_count, target_email, seed_email) -> RemoveCheck` con motivo del rifiuto.

In `app/domain/booking.py`: `can_refund(status, paid_cents, refund_cents)`; `status_after_void(status, due, paid)` (confermata che scende sotto il dovuto torna in attesa).

Le presenze contano solo prenotazioni che occupano posti (`occupies_seats`, valutata con `effective_status`).

## Export CSV

`app/csv_export.py`: separatore `;`, UTF-8 con BOM (si apre in Excel italiano senza passaggi), date e ore in Europe/Rome, importi con la virgola, protezione dalle formule (celle che iniziano con `=`, `+`, `-`, `@` ricevono un apice davanti). Ogni vista ha `?format=csv` sullo stesso endpoint, che risponde con `Content-Disposition: attachment` e un nome file con data.

## Servizi

- `app/services/views.py`: query delle viste (persone, slot, settimana, da verificare) con lettura su `expire_overdue` come oggi.
- `app/services/admins.py`: elenco, aggiunta (promuove o crea) e rimozione degli admin.
- `app/services/booking_changes.py` (da MVP 2): `change_slots(..., force=True)` per l'admin, `reactivate_manually`.
- `app/services/refunds.py`: `record_refund`.
- `app/services/payments.py`: `void_payment`.
- `app/services/audit.py`: `log(db, actor, action, booking, detail)`, chiamato da ogni servizio sopra quando l'attore è un admin.

## Endpoint (tutti `require_admin`)

| Metodo e path | Scopo |
|---------------|-------|
| `GET /api/admin/views/people` | vista per persona (`?status=&q=&format=csv`) |
| `GET /api/admin/views/slots` | giorno e slot (`?format=csv`) |
| `GET /api/admin/views/week` | settimana aggregata (`?format=csv`) |
| `GET /api/admin/views/payments-review` | pagamenti da verificare (`?format=csv`) |
| `GET /api/admin/admins` | elenco admin |
| `POST /api/admin/admins` | `{email, first_name?, last_name?}`: promuove o crea |
| `DELETE /api/admin/admins/{id}` | rimuove il ruolo |
| `PATCH /api/admin/registrations/{id}` | anagrafica e proroga (`hold_expires_at`) |
| `PUT /api/admin/registrations/{id}/slots` | `{slot_ids, force}` |
| `POST /api/admin/registrations/{id}/cancel` | disdetta per conto del partecipante |
| `POST /api/admin/registrations/{id}/reactivate` | riattivazione manuale |
| `POST /api/admin/registrations/{id}/refund` | `{amount_cents, refunded_on, note}` |
| `POST /api/admin/registrations/{id}/payments/{pid}/void` | `{reason}` |
| `GET /api/admin/registrations/{id}` | esteso con cronologia |

`GET /api/admin/registrations` (MVP 1) resta; la vista «Persone» lo estende con telefono e presenza serale invece di duplicarlo.

## Pagine

`AdminLayout` con le voci Persone, Giorni e slot, Settimana, Pagamenti da verificare, Admin, Impostazioni. Pagine nuove: `AdminPeople` (evoluzione di `AdminRegistrations`), `AdminSlots`, `AdminWeek`, `AdminReview`, `AdminAdmins`. `AdminRegistrationDetail` guadagna le azioni: modifica dati, modifica slot (con «Forza oltre la capienza»), proroga, disdetta, riattivazione, rimborso, annulla pagamento, cronologia. Pulsante «Scarica CSV» comune (componente riusabile). Tabelle con `<caption>`, intestazioni `scope`, contenitore scorrevole su telefono.

## Impatti sugli MVP precedenti

- **MVP 1**: `paid_total` e `booking_view` cambiano per escludere i pagamenti annullati; i test esistenti sui saldi restano validi (nessun pagamento annullato).
- **MVP 2**: riuso di `change_slots`; `request_cancellation` accetta l'attore admin; la riattivazione manuale riusa `hold_started_at` e azzera i promemoria.
- **MVP 4 e successivi**: la vista «Giorni e slot» e la settimana aggregata saranno estese (lista d'attesa, pasti, attività). Le funzioni di presenza restano pure per facilitarlo.

## Scelte tecniche da registrare in `decisions.md`

- CSV con `;` e BOM per Excel italiano, con protezione dalle formule.
- Pagamenti annullati e non cancellati.
- `audit_log` generico invece di campi sparsi.
- Presenza serale derivata calcolata a lettura, mai salvata (D-009).
