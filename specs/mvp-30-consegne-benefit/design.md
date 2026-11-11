# MVP 30 · Design

## Regola di diritto (dominio puro)

Nuovo `backend/app/domain/benefits.py`, senza database:

```python
def is_entitled(*, active: bool, category: str, fee_exempt: bool,
                net_paid_cents: int, base_fee_cents: int) -> bool
```

`active` è `occupies_seats(effective_status(...))` (`domain/booking.py`). Vale `active and (category == CATEGORY_INTERNAL_NON_PAYING or fee_exempt or (base_fee_cents > 0 and net_paid_cents >= base_fee_cents))`. Il valore `net_paid_cents` viene da `models.net_paid_cents(booking)` (pagamenti validi meno rimborsi attivi). Non si usa `registration_fee_cents` né `domain/confirmation.py`: sono la soglia base+giorni.

## Dati e migrazione `0029_benefit_delivery`

Migrazione additiva, tabella `benefit_delivery`:

| Colonna | Tipo | Note |
|---|---|---|
| `id` | int PK | |
| `edition_id` | FK `edition` | indice |
| `participant_id` | FK `participant` | **non** la prenotazione, che può sparire |
| `benefit_id` | FK `benefit` | |
| `delivered_at`, `delivered_by_id` | UTC, FK `participant` | |
| `annulled_at`, `annulled_by_id`, `annul_reason` | null finché attiva | motivo ≤ 200 |
| `request_key` | `Unicode(36)` null | |

- Indice univoco filtrato `uq_benefit_delivery_active` su `(participant_id, benefit_id)` `WHERE annulled_at IS NULL` (`mssql_where` e `sqlite_where`, come `uq_payment_request_key`): garantisce **una sola consegna attiva** anche con due admin in corsa.
- Indice univoco filtrato `uq_benefit_delivery_request_key` su `request_key` `WHERE request_key IS NOT NULL`.
- Nessuna colonna sul catalogo `benefit` e nessuna modifica a `booking`. I benefit ritirati restano (`retired`), quindi le FK non si rompono.
- Downgrade: elimina la tabella.

## Servizio

`backend/app/services/benefit_deliveries.py`:

- `entitled_people(db, edition, now)`: una query sulle prenotazioni dell'edizione con pagamenti e rimborsi caricati (stesso schema di `services/views.py`; nessun N+1), applica `is_entitled`; restituisce persona, booking, categoria, flag di diritto.
- `rows_for(db, edition, benefit, now, q, state)`: unione tra aventi diritto e persone con **almeno una consegna** per quel benefit (anche annullata, anche senza prenotazione). Per ognuna: consegna attiva (se c'è), consegne annullate, `entitled` e quindi «Senza diritto attuale» quando c'è una consegna attiva ma `entitled` è falso. Le persone senza diritto con sole consegne annullate escono dall'elenco principale.
- `deliver(db, admin, edition, participant_id, benefit_id, request_key, now)`: controlla che benefit ed edizione coincidano, che il benefit non sia ritirato (422 `benefit.retired`), che la persona abbia diritto (422 `delivery.not_entitled`); se `request_key` esiste già restituisce quella consegna; se esiste una consegna attiva restituisce quella (nessun errore, idempotente); un `IntegrityError` sugli indici si traduce nella lettura della consegna vincente.
- `annul(db, admin, delivery_id, reason, now)`: motivo obbligatorio; già annullata = nessuna modifica e nessuna nuova voce di cronologia.
- `AuditLog` (`services/audit.py`) con azioni `benefit_delivered` / `benefit_annulled`, `participant_id` e `edition_id`; il dettaglio contiene benefit e (per l'annullo) il motivo.

## API admin (`backend/app/api/admin_deliveries.py`, tutte `require_admin`)

- `GET /api/admin/deliveries/benefits`: benefit del catalogo (attivi e, se hanno consegne, ritirati) con contatori «consegnati / aventi diritto».
- `GET /api/admin/deliveries?benefit_id=&q=&state=&format=json|csv`: righe come sopra; il CSV ha le stesse righe e intestazioni per lingua (BOM e `;` come gli altri CSV, `csv_export.py`).
- `POST /api/admin/deliveries` `{ participant_id, benefit_id, request_key }` → 201 (nuova) o 200 (esistente).
- `POST /api/admin/deliveries/{id}/annul` `{ reason }`.

Le risposte contengono: id persona, nome, categoria, link alla scheda (id prenotazione se esiste), stato. **Mai** email, telefono, allergie, importi o note. Le consegne dell'edizione corrente soltanto; una consegna di un'altra edizione dà 404.

## Frontend

- Nuova pagina `frontend/src/pages/AdminDeliveries.tsx`, rotta `adminDeliveries: "/admin/deliveries"` in `routes.ts`, voce «Consegne / Deliveries» in `AdminLayout.tsx` accanto a «Esterni».
- Selettore del benefit (con contatori), ricerca, filtro di stato, elenco mobile-first con pulsante «Consegna» (≥44 px) e «Annulla…» che apre un dialogo (`ConfirmDialog` con campo motivo). La `request_key` si genera per tentativo; il pulsante si disabilita durante l'invio.
- Stato con testo (e icona), non solo colore; `StatusBadge` esistente per i valori. «Senza diritto attuale» ha una spiegazione visibile.
- Testi in `i18n/{it,en}.ts` (`deliveries.*`), messaggi server `delivery.not_entitled`, `benefit.retired`, `delivery.reason_required`, `delivery.not_found` in `backend/app/i18n.py`.
- Guida: nuova sezione `frontend/src/guide/{it,en}/admin/17-deliveries.md` (stesso nome nelle due lingue) e un rimando in `10-settings.md` sul catalogo.

## Impatti sugli MVP precedenti

- MVP 23: nessuna modifica al catalogo né al ritiro soft; i benefit continuano a essere gestiti in Impostazioni.
- MVP 25c: si leggono categoria, `fee_exempt` e versato netto così come sono.
- MVP 25a/b: gli esterni restano fuori (nessun `Participant` né prenotazione).
- Report, CSV dei partecipanti, email e pagina personale non cambiano.

## Test previsti

Vedi [tasks.md](tasks.md).
