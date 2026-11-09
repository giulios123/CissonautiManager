# MVP 25a · Design

## Dati e migrazione `0024_external_guests`

Migrazione additiva dopo `0023_included_meal`; nessuna modifica ai dati esistenti.

- **`external_guest`**: `id`, `edition_id` (FK, indicizzato), `first_name`, `last_name`, `phone` (nullable), `reference` (nullable), `internal_note` (nullable), `payer` (`paying` | `non_paying`), `diet` (stessi valori di `Booking.diet`), `allergies` (nullable), `allergies_consent_at`, `allergies_consent_by_id` (FK `participant`, nullable), `created_at`, `created_by_id`.
- **`external_guest_meal`**: PK (`guest_id`, `date`, `kind`), FK con cancellazione a cascata.
- **`external_guest_activity`**: PK (`guest_id`, `activity_id`), `joined_at`; FK a `activity` senza cascata (l'attività con aderenti non si elimina).

Le chiavi primarie impediscono la stessa voce due volte per lo stesso esterno. Le date dei pasti devono cadere tra `start_date` e `end_date` dell'edizione.

Il campo `payer` serve in 25a come etichetta e in 25b come regola economica: nasce già qui per non dover migrare di nuovo l'anagrafica.

## Regole pure (`backend/app/domain/external.py`)

- `normalize_name(first, last)`: confronto senza maiuscole e con spazi compressi.
- `find_duplicates(candidate, guests, active_participants)`: restituisce gli omonimi, distinguendo esterni e iscritti.
- `check_guest_meal(day, edition_days)`: i pasti degli esterni non richiedono presenza; sono ammessi tutti i giorni dell'edizione.
- `merge_people(...)`: unisce iscritti ed esterni per i conteggi, con chiavi distinte (`p:<id>` / `g:<id>`), così la stessa persona non è contata due volte.
- Le funzioni di `domain/activities.py` (`check_join`, `check_activity_edit`, `check_activity_delete`) ricevono il numero totale di aderenti (iscritti + esterni); nessuna nuova logica di capienza.

## Servizi

- `services/guests.py`: creazione, modifica, eliminazione, assegnazione di pasti e attività, tutto con `audit.log` e nella stessa transazione. Le attività usano `activities_for_update` per il blocco, come `change_activities`.
- `services/seats.py`: `occupied_by_activity` somma anche `external_guest_activity`. `free_by_activity`, `offers_for`, `admin_activities` e `change_activities` ereditano il comportamento senza altre modifiche. Un esterno non ha stato né scadenza: occupa sempre.
- `services/views.py`: `load_meals` aggiunge `MealRow` con `kind="guest"`; `activity_signup_days` e la vista settimana contano le persone con `merge_people`; `participants()` di `services/activities.py` include gli esterni con l'etichetta.
- `domain/report.py` e `services/views.load_report`: `Split` riceve il campo `external`; `total` = confermate + in attesa + esterni. `ActivityRow.expected_cents` resta calcolato sui soli iscritti (nessun importo per gli esterni in 25a). `services/report_export.py` aggiunge la colonna «Esterni».

## API (`backend/app/api/admin_guests.py`)

Router `/api/admin/guests` con `dependencies=[Depends(require_admin)]`, registrato in `main.py` accanto agli altri router admin.

- `GET ""` (+ `format=csv`): elenco con pasti e attività.
- `POST ""`: crea; risponde 409 `guests.duplicate` con gli omonimi se non c'è `confirm_duplicate`.
- `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`.
- `PUT /{id}/meals`: elenco `[{date, kind}]`.
- `PUT /{id}/activities`: `{activity_ids, force}`; 409 `activities.full_force` se piena senza `force`; avviso `warn.over_capacity` con `force`.
- Allergie: `PATCH` accetta `allergies` solo con `allergies_consent: true`; con `false` cancella allergie e consenso.

Messaggi nel catalogo `backend/app/i18n.py` (via `admin_texts.py`) in IT e EN. Le risposte dei partecipanti (`api/me.py`) non cambiano, salvo i posti liberi.

## Frontend

- Pagina `AdminGuests.tsx` (elenco, creazione, dettaglio) con griglia dei pasti per giorno che mostra destinatario e prezzo sola lettura (il prezzo è informativo fino al 25b), e riuso di `ActivityPicker` per le attività.
- Rotta `adminGuests` in `routes.ts` e `App.tsx`, voce nel menu di `AdminLayout`.
- Etichetta «Esterno» in `AdminMeals`, `AdminActivityDetail`, `AdminWeek` e colonna «Esterni» in `AdminReport`.
- Chiavi `guests.*` e correlate in `frontend/src/i18n/{it,en}.ts`.

## Guida

Nuovo `frontend/src/guide/{it,en}/admin/16-guests.md`, collegato in `ADMIN_PAGES` (`guide/content.ts`) e in `guide/content.test.ts`. Aggiornare `03-week`, `04-meals`, `05-activities`, `07-report` in entrambe le lingue.

## Impatti sugli MVP precedenti

- Capienze (MVP 6): i posti liberi calano; nessun cambio per le prenotazioni esistenti.
- Pasti (MVP 5): nessuna capienza dei pasti; i conteggi crescono.
- Report (MVP 7): nuova colonna; gli importi non cambiano.
- Edizioni (F): i dati nascono con `edition_id`, senza ulteriori accorgimenti.

## Verifiche

Test di dominio per omonimi, normalizzazione, giorni ammessi e unione dei conteggi. Test API: 403 per i non admin, nessun `Booking` o `Participant` creato, 409 sui doppioni e conferma esplicita, capienza con e senza `force`, allergie solo con consenso, cancellazione a cascata. Test di coerenza fra pasti, attività, settimana e report. Migrazione da zero e da `0023` su SQLite e SQL Server (CI). `test_i18n_admin.py`: il nuovo CSV in `CSV_URLS` e le etichette in `LABELS_EN`. Vitest per pagina, rotta e etichette.

## Modifiche a domain.md

Vedere la proposta in [requirements.md](requirements.md#modifiche-a-domainmd). Applicarla solo dopo approvazione del maintainer.
