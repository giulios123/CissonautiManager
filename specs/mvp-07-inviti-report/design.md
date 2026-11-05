# MVP 7 · Inviti e report · Design

## Ipotesi sugli MVP 4-6

Gli MVP 4, 5 e 6 sono in lavorazione e il loro codice non è ancora disponibile. Questo design si appoggia su ciò che dicono `domain.md` e la roadmap. **Prima del task 1** si confrontano le ipotesi con il codice reale e si aggiorna questo file.

| MVP | Ipotesi | Usata da |
|-----|---------|----------|
| 4 | Esiste un'entità di iscrizione in lista d'attesa per slot, con persona, slot, data di ingresso e stato (in lista, promossa, uscita). | US-2, US-3, report |
| 4 | Esiste una funzione unica che, liberato un posto, sceglie «il primo in lista» e lo promuove. | US-2 |
| 4 | Esiste una vista admin della lista d'attesa con CSV. | US-3 |
| 5 | Esistono adesioni ai pasti per giorno (pranzo, cena) legate alla prenotazione, con prezzo flat dall'edizione. | report |
| 5 | Le esigenze alimentari sono salvate con consenso e si sa per ogni pasto chi le ha. | report (solo conteggi) |
| 6 | Esistono attività con prezzo, capienza opzionale e adesioni legate alla prenotazione. | report |
| 4-6 | L'importo dovuto della prenotazione include già pasti e attività. | report, incassi |

Se un'ipotesi cade, si corregge il design senza improvvisare (AGENTS.md, B2.5).

## Modello dati (migrazione successiva all'ultima degli MVP 4-6)

Su `participant`, accanto a `invited_by` che sta già lì:

| Campo | Scopo |
|-------|-------|
| `plus_one_verified_at` (UtcDateTime, nullable) | quando l'admin ha verificato il legame; `NULL` = non verificato |
| `plus_one_verified_by_id` (FK `participant`, nullable) | admin che l'ha verificato |

Sul partecipante e non sulla prenotazione perché il campo «chi ti ha invitato?» è del partecipante. Il modello prevede un'edizione alla volta (domain.md, Fuori scope); con più edizioni la verifica andrà spostata, ed è annotato come limite.

Il report non ha tabelle: si calcola a lettura.

## Regole di dominio (funzioni pure)

Nel modulo della lista d'attesa dell'MVP 4 (presumibilmente `app/domain/waitlist.py`):

- `can_verify_plus_one(invited_by: str | None) -> bool`: vero solo se il testo, ripulito dagli spazi, non è vuoto.
- `waitlist_priority_key(verified: bool, joined_at: datetime, entry_id: int) -> tuple`: `(not verified, joined_at, entry_id)`. L'id rompe le parità esatte.
- `ordered_waitlist(entries) -> list`: ordina con la chiave sopra. La promozione dell'MVP 4 prende il primo di questa lista invece di ordinare per data.

In `app/domain/report.py`:

- `edition_report(...) -> EditionReport`: riceve righe già lette (prenotazioni con stato effettivo, presenze, pasti, attività, lista d'attesa, pagamenti, rimborsi) e restituisce dataclass per sezione. Riusa `presences` e `week_summary` di `app/domain/presence.py` per le presenze e la regola dei pagamenti annullati (D-021) per gli incassi.
- Picco = massimo dei presenti su tutti gli slot; media = media sugli slot di mattina e pomeriggio dei giorni dell'edizione; giorni-persona = somma per persona dei giorni con almeno uno slot.
- Presenze, pasti e attività sono contati separatamente per prenotazioni `confermata` e `in_attesa_pagamento`, con il totale.
- Netto = versato meno rimborsato. Da incassare = somma dei saldi positivi delle prenotazioni attive. Crediti = somma dei saldi negativi.

## Servizi

- `app/services/participants.py` (o nuovo `plus_one.py`): `set_plus_one_verified(db, actor, participant, verified)`; scrive in `audit_log` con `app/services/audit.py` («+1 verificato» / «+1 non più verificato», con il testo di «invitato da»).
- Promozione dell'MVP 4: legge `plus_one_verified_at` insieme alle iscrizioni in lista e usa `ordered_waitlist`.
- `app/services/views.py`: `report_data(db, now)` che legge tutto con `expire_overdue` come le altre viste e chiama `edition_report`.

## Endpoint (tutti `require_admin`)

| Metodo e path | Scopo |
|---------------|-------|
| `PUT /api/admin/registrations/{id}/plus-one` | `{verified: bool}`; 422 se «invitato da» è vuoto |
| `GET /api/admin/registrations/{id}` | esteso con `plus_one_verified_at` e `plus_one_verified_by` |
| vista lista d'attesa dell'MVP 4 | estesa con posizione effettiva, `plus_one_verified`, `invited_by` (anche nel CSV) |
| `GET /api/admin/views/report` | report in JSON; `?format=csv` con `app/csv_export.py`, righe `sezione;voce;valore` |

Stesso schema di `app/api/admin_views.py`: un endpoint per vista, CSV sullo stesso path.

## Pagine

- `AdminRegistrationDetail.tsx`: blocco «Invitato da» con la spunta «+1 verificato» (etichetta collegata, stato letto dagli screen reader), chi e quando.
- Vista lista d'attesa (MVP 4): colonna posizione, etichetta «+1» o «da verificare».
- Nuova `AdminReport.tsx`, voce «Report» in `AdminLayout.tsx`. Una tabella per sezione con `<caption>` e intestazioni `scope`, come le viste dell'MVP 3. `CsvButton.tsx` riusato.
- `styles.css`: regole `@media print` che nascondono navigazione e bottoni e tolgono lo scorrimento orizzontale delle tabelle.

## Impatti sugli MVP precedenti

- **MVP 3**: le viste non cambiano; il report riusa le stesse regole di presenza e di pagato, quindi i numeri coincidono con «Settimana» e «Persone».
- **MVP 4**: cambia solo l'ordine con cui si sceglie chi promuovere; email, blocco e limite restano. I test dell'MVP 4 sull'ordine di ingresso restano validi quando nessuno è verificato.
- **MVP 5 e 6**: nessuna modifica, solo lettura.

## Scelte tecniche da registrare in `decisions.md`

- Priorità +1 calcolata al momento della promozione, mai salvata come posizione.
- Verifica del +1 sul partecipante, non sulla prenotazione.
- Report calcolato a lettura, senza tabelle né snapshot; CSV in formato lungo «sezione;voce;valore» invece di un file per sezione.
