# MVP 7 · Inviti e report · Design

Basato sul codice di `main` dopo gli MVP 4-6. Punti verificati: `queue` e `position` in `backend/app/domain/waitlist.py` (il commento di `queue` indica già «This is where a priority (the +1 of MVP 7) will plug in»), `active_entries` in `backend/app/services/waitlist.py`, `WaitingPerson` in `backend/app/api/admin_views.py`, `recompute_amount` e `compute_amount_due` per le voci di costo.

## Modello dati (migrazione 0008)

Su `participant`, accanto a `invited_by`:

| Campo | Scopo |
|-------|-------|
| `plus_one_verified_at` (UtcDateTime, nullable) | quando l'admin ha verificato il legame; `NULL` = non verificato |
| `plus_one_verified_by_id` (FK `participant`, nullable) | admin che l'ha verificato |

Sul partecipante e non sulla prenotazione perché «chi ti ha invitato?» è del partecipante e chi è solo in lista non ha una prenotazione (D-026, D-028). Il modello prevede un'edizione alla volta: con più edizioni la verifica andrà spostata (annotato nel Backlog).

Il report non ha tabelle: si calcola a lettura.

## Regole di dominio (funzioni pure)

In `app/domain/waitlist.py`:

- `queue(entries, priority_ids=frozenset())`: ordina per `(participant_id not in priority_ids, created_at, id)`. Oggi chiede solo `id` e `created_at` (`QueuedEntry`): il protocollo guadagna `participant_id`. Con `priority_ids` vuoto il comportamento è identico a oggi, quindi i test esistenti restano validi.
- `position(entries, entry_id, priority_ids=frozenset())`: inoltra `priority_ids` a `queue`.
- `can_verify_plus_one(invited_by: str | None) -> bool`: vero solo se il testo, ripulito dagli spazi, non è vuoto.

In `app/domain/report.py` (nuovo):

- `edition_report(...) -> EditionReport`: riceve righe già lette e restituisce dataclass per sezione. Riusa `presences` e `week_summary` di `app/domain/presence.py`, `diet_counts` di `app/domain/meals.py` e il calcolo del pagato senza annullati (D-021).
- Picco = massimo dei presenti su tutti gli slot; media = media sugli slot di mattina e pomeriggio; giorni-persona = somma per persona dei giorni con almeno uno slot.
- Dovuto totale = somma di `booking.amount_due_cents`. La scomposizione in quota, pasti e attività usa i prezzi correnti dell'edizione (come `recompute_amount`, D-017) e una riga «scarto» assorbe la differenza se un prezzo è cambiato dopo le iscrizioni: la somma delle voci torna sempre al totale.
- Netto = versato meno rimborsato. Da incassare = somma dei saldi positivi delle prenotazioni che occupano posti. Crediti = somma dei saldi negativi.
- «Confermate» e «in attesa» sono gli stati effettivi `confermata` e `in_attesa_pagamento`.

## Servizi

- `app/services/waitlist.py`: `active_entries` carica in una sola query l'insieme dei partecipanti con `plus_one_verified_at` non nullo tra quelli in lista e lo passa a `queue`. Da lì seguono da sole la promozione (`_promote_slot`, che prende `entries.pop(0)`), `position_of` (la posizione mostrata in `Waitlist.tsx`) e la vista admin.
- `app/services/participants.py` (o nuovo `plus_one.py`): `set_plus_one_verified(db, actor, participant, verified)`; rifiuta se `can_verify_plus_one` è falso; scrive `audit_log` con `app/services/audit.py` (`booking_id` vuoto se non c'è una prenotazione; il testo riporta nome, email e «invitato da», D-022).
- Modifica dati dell'admin (`PATCH /api/admin/registrations/{id}`): se «invitato da» diventa vuoto, la verifica cade e finisce nella cronologia.
- `app/services/views.py`: `load_report(db, now)` con `expire_overdue` come le altre viste; legge prenotazioni, presenze (`load_presence`), pasti (`load_meals`, esteso con lo stato della prenotazione), attività e adesioni, contributi, voci della lista (`WaitlistEntry.close_reason`) e pagamenti.

## Endpoint (tutti `require_admin`)

| Metodo e path | Scopo |
|---------------|-------|
| `PUT /api/admin/participants/{id}/plus-one` | `{verified: bool}`; 422 se «invitato da» è vuoto, 404 se la persona non esiste |
| `GET /api/admin/registrations/{id}` | esteso con `participant_id`, `plus_one_verified_at` e `plus_one_verified_by` |
| `GET /api/admin/views/slots` | `WaitingPerson` esteso con `participant_id`, `plus_one` (bool) e `invited_by`; la posizione è quella effettiva; il CSV guadagna le colonne «+1 verificato» e «Invitato da» |
| `GET /api/admin/views/report` | report in JSON; `?format=csv` con `app/csv_export.py`, righe `sezione;voce;confermate;in attesa;totale` |

L'endpoint per `participant_id` serve perché chi è solo in lista non ha una prenotazione, quindi non ha un `booking_id` (D-028).

## Pagine

- `AdminRegistrationDetail.tsx`: blocco «Invitato da» con la spunta «+1 verificato» (etichetta collegata, stato letto dagli screen reader), chi e quando.
- `AdminSlots.tsx`: nella lista d'attesa di ogni slot, posizione, `StatusBadge`-style «+1» o «da verificare» (testo sempre scritto, come per gli stati) e la spunta accanto al nome.
- Nuova `AdminReport.tsx`, voce «Report» in `AdminLayout.tsx` dopo «Contributi». Una tabella per sezione con `<caption>` e intestazioni `scope`, come le viste dell'MVP 3. `CsvButton.tsx` riusato.
- `styles.css`: regole `@media print` che nascondono intestazione, navigazione e bottoni e tolgono lo scorrimento orizzontale delle tabelle; colori solo da token (lo controlla `theme.test.ts`).

## Impatti sugli MVP precedenti

- **MVP 3, 5 e 6**: le viste non cambiano; il report riusa le stesse regole di presenza e di pagato, quindi i numeri coincidono con «Settimana», «Pasti» e «Attività».
- **MVP 4**: cambia solo l'ordine con cui si sceglie chi promuovere; email, blocco, limite e chiusura delle voci restano. Il test `queue` esistente (ordine di arrivo) resta valido senza priorità.
- **MVP 8**: le pagine nuove usano i token e i badge già presenti.

## Scelte tecniche da registrare in `decisions.md`

- Priorità +1 calcolata al momento della promozione, mai salvata come posizione.
- Verifica del +1 sul partecipante, con endpoint per id partecipante (chi è solo in lista non ha una scheda).
- Report calcolato a lettura, senza tabelle né snapshot; CSV in formato lungo; scomposizione del dovuto con una riga «scarto».
