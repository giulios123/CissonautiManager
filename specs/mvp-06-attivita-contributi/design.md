# MVP 6 · Attività e contributi · Design

## Modello dati (migrazione 0007)

Nuova tabella `activity`:

| Campo | Scopo |
|-------|-------|
| `id`, `edition_id` | |
| `title`, `description` | testo mostrato ai partecipanti |
| `date`, `period` | giorno dell'edizione e fascia (`morning`, `afternoon`, `evening`) |
| `time_label` (nullable) | orario indicativo libero |
| `price_cents` (int, default 0) | 0 vuol dire gratuita |
| `capacity` (nullable) | `None` vuol dire senza limite |
| `created_at` | |

Nuova tabella `booking_activity`: `booking_id`, `activity_id` (chiave primaria composta), `joined_at`.

Nuova tabella `contribution`: `id`, `booking_id`, `kind` (`talk`, `topic`, `skill`), `title`, `description` (nullable), `created_at`, `updated_at`. Le righe si cancellano con la prenotazione.

## Regole di dominio (funzioni pure)

In `app/domain/activities.py`:

- `is_eligible(periods_that_day, activity_period) -> bool`: la sera usa `has_evening` (`app/domain/presence.py`).
- `activities_to_drop(activities, periods_by_day)`: stessa forma di `meals_to_drop` (MVP 5).
- `check_join(eligible, free, past_day, allow_past, force) -> JoinCheck`: motivi `not_present`, `full`, `past_day`.
- `check_activity_edit(joined, old, new) -> EditCheck`: prezzo, giorno e fascia fissi con iscritti; capienza mai sotto gli iscritti; eliminazione solo a zero iscritti.
- `available_seats` e `has_free_seat` di `app/domain/booking.py` si riusano per la capienza.

In `app/domain/contributions.py`: `validate_contribution(kind, title)`.

`compute_amount_due` (MVP 5) riceve anche la somma dei prezzi delle attività a pagamento.

## Servizi

- `app/services/activities.py`:
  - `create`, `update`, `delete` per l'admin, con `check_activity_edit` e `audit.log`.
  - `occupied_by_activity(db, ids, now)`: come `occupied_by_slot` (`app/services/seats.py`), conta solo le prenotazioni che occupano posti.
  - `activities_for_update(ids)`: lock con `with_for_update()` e hint `WITH (UPDLOCK, HOLDLOCK)` per SQL Server, come `slots_for_update` (D-011).
  - `change_activities(db, sender, booking, wanted_ids, now, allow_past=False, force=False, actor=None) -> ChangeResult`: stessa forma di `change_slots` e `change_meals`; ricalcolo con `recompute_amount`; conferma automatica se coperta.
- `change_slots` (`booking_changes.py`) chiama `activities_to_drop` accanto a `meals_to_drop`.
- `reactivate` (`services/booking_admin.py`) e `revive_expired` controllano anche i posti nelle attività; `SlotsFull` si estende con le attività piene, oppure nasce un `ActivitiesFull` gestito nello stesso modo dalla scheda.
- `app/services/contributions.py`: `add`, `update`, `remove` per il partecipante proprietario.

## Endpoint

| Metodo e path | Scopo |
|---------------|-------|
| `GET /api/me` | esteso: attività proposte (con posti liberi) e scelte, contributi |
| `PUT /api/me/booking/activities` | `{activity_ids, preview?}` |
| `POST /api/me/contributions` | `{kind, title, description}` |
| `PATCH /api/me/contributions/{id}` | modifica del proprio contributo |
| `DELETE /api/me/contributions/{id}` | rimozione |
| `GET /api/admin/activities` | elenco con iscritti (`?format=csv`) |
| `POST /api/admin/activities` | creazione |
| `PATCH /api/admin/activities/{id}` | modifica |
| `DELETE /api/admin/activities/{id}` | eliminazione senza iscritti |
| `GET /api/admin/activities/{id}` | iscritti (`?format=csv`) |
| `PUT /api/admin/registrations/{id}/activities` | `{activity_ids, force}` |
| `GET /api/admin/views/contributions` | `?kind=&format=csv` |
| `GET /api/admin/views/week` | esteso con le attività |

## Pagine

- `Personal.tsx`: sezione «Attività» (componente `ActivityPicker`, con anteprima dell'importo e posti liberi) e sezione «Cosa porti al camp» con i contributi.
- Nuove pagine `AdminActivities.tsx` (elenco e modulo) e `AdminActivityDetail.tsx` (iscritti); `AdminContributions.tsx`. Voci «Attività» e «Contributi» in `AdminLayout`.
- `AdminRegistrationDetail.tsx`: attività modificabili con «Forza oltre la capienza», contributi in sola lettura.
- `AdminWeek.tsx`: colonna «Attività».

## Impatti sugli MVP precedenti

- **MVP 2**: `change_slots` può togliere attività; la disdetta libera i posti senza codice nuovo (conta solo chi occupa posti).
- **MVP 3**: riattivazione con controllo delle attività; «Settimana» e scheda estese.
- **MVP 4**: nessuno (niente lista d'attesa per le attività).
- **MVP 5**: `recompute_amount` e `compute_amount_due` guadagnano le attività; la regola «cade se perdi il titolo» diventa comune a pasti e attività.
- **MVP 7**: il report userà adesioni e contributi.

## Scelte tecniche da registrare in `decisions.md`

- Attività legate a giorno e fascia, non a un orario libero, per riusare la regola della presenza.
- Prezzo, giorno e fascia bloccati dopo la prima adesione, così gli importi non cambiano alle spalle delle persone.
- Contributi su tabella propria, legati alla prenotazione.
