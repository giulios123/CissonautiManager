# MVP 29 · Design

## Dati e migrazione `0028_activity_source`

Migrazione additiva dopo `0027_contribution_hidden` (se arriva un'altra migrazione, si prende il numero successivo alla testa corrente).

- `activity.source_contribution_id` (FK nullable a `contribution.id`, nome esplicito `fk_activity_source_contribution`), `activity.source_title` (`Unicode(200)`, null) e `activity.request_key` (`Unicode(36)`, null).
- Indice univoco filtrato `uq_activity_request_key` su `request_key` `WHERE request_key IS NOT NULL`, con lo stesso schema di `uq_payment_request_key` e `uq_external_movement_request_key` (`mssql_where` e `sqlite_where`).
- Nessun `ON DELETE SET NULL` a database: il comportamento sarebbe diverso tra SQLite e SQL Server. Lo scollegamento è fatto dal servizio (sotto), dentro la stessa transazione della cancellazione.
- Le attività esistenti restano con le tre colonne a `NULL`. Downgrade: elimina indice e colonne (batch su SQLite, vincoli espliciti per SQL Server).

## Scollegare la fonte prima di cancellarla

Due punti cancellano contributi:

1. `services/contributions.remove` (l'autore cancella il proprio contributo).
2. `services/booking_changes.py` (~riga 276): `db.delete(booking)` per la disdetta senza pagamenti, con cascata `delete-orphan` su `Booking.contributions`.

In entrambi, **prima** della cancellazione, un unico helper `detach_activities(db, contribution_ids)` in `services/activities.py` fa `UPDATE activity SET source_contribution_id = NULL WHERE source_contribution_id IN (...)`. `source_title` è già stato copiato alla creazione, quindi resta. L'helper è chiamato anche per ogni altro percorso che elimini prenotazioni (cercare con `grep "db.delete(booking)"`; oggi è uno solo) e un test dedicato blocca nuovi percorsi che lo dimenticano (cancellazione di una booking con proposta collegata, con FK attive su SQLite).

## Creazione dall'API

`POST /api/admin/activities` (`api/admin_activities.py`) accetta due campi facoltativi in `ActivityIn`: `source_contribution_id: int | None` e `request_key: str | None` (UUID, max 36).

1. `require_admin`, come oggi.
2. Se `request_key` è presente e esiste già un'attività con quella chiave **nella stessa edizione**, si risponde `200` con quell'attività (senza ricrearla) e si ignorano gli altri campi. La prima creazione ha vinto.
3. Se `source_contribution_id` è presente: si carica il contributo con la sua prenotazione; deve esistere e avere `booking.edition_id == edizione corrente`, altrimenti 404 (`activity.source_not_found`). Non conta lo stato della prenotazione né `hidden_at`.
4. Si creano `source_contribution_id` e `source_title = contribution.title[:200]`; il resto passa per `activity_service.create` e per i controlli già esistenti. Cronologia: voce di audit con id della proposta.
5. Una `IntegrityError` sull'indice della chiave (due richieste in corsa) si traduce nella lettura dell'attività vincente, non in un 500.

`ActivityOut` non cambia per i partecipanti. L'admin riceve in più, solo in `ActivityDetailOut` e nell'elenco admin: `source: { contribution_id: int | None, title: str } | None`. `title` è `source_title` (la copia), così l'etichetta è stabile anche se la proposta viene modificata; `contribution_id = None` significa «non più disponibile».

## Lettura dalla parte dei contributi

`GET /api/admin/views/contributions` (`api/admin_views.py`, `contributions_view`) aggiunge a ogni riga `activities: [{ id, title, date, period }]`, calcolato con una sola query sulle attività dell'edizione con `source_contribution_id IN (...)` (nessun N+1). Il titolo è quello localizzato per la lingua della richiesta (come le altre viste attività). Il CSV dei contributi aggiunge la colonna «Attività create» (titoli separati da `; `).

Gli endpoint e gli schemi dei partecipanti (`/api/me/*`, `/api/me/proposals`, `/api/activities`) **non** leggono né serializzano le tre colonne nuove: un test confronta le chiavi dei payload.

## Frontend

- `AdminContributions.tsx`: pulsante «Crea attività» per riga e elenco «Attività create» con link a `/admin/activities/:id`. Il pulsante apre il modulo in una modale (`InfoDialog` di `frontend/src/InfoDialog.tsx`) con `ActivityForm`.
- `AdminActivities.tsx`: `ActivityForm` viene esportato in un file proprio (`ActivityForm.tsx`) per essere usato dalle due pagine, con `initial` precompilato e una prop `source`. Ogni apertura genera una nuova `request_key` (`crypto.randomUUID()`); il pulsante «Salva» si disabilita durante l'invio. Dopo un errore di rete la **stessa** chiave viene riusata per «Riprova».
- Precompilazione: la lingua dell'interfaccia riempie `title_<lang>` e `description_<lang>`; l'altra resta vuota. Data, fascia, orari, costo e capienza partono dai valori vuoti dell'attività nuova.
- `AdminActivityDetail.tsx`: riga «Dalla proposta «…»» con link alla vista contributi, oppure «(non più disponibile)» senza link.
- Testi nuovi in `i18n/{it,en}.ts` (`contrib.createActivity`, `contrib.activitiesCreated`, `activity.fromProposal`, `activity.fromProposalGone`) e `activity.source_not_found` in `backend/app/i18n.py`.

## Impatti sugli MVP precedenti

- MVP 24: i testi IT/EN restano obbligatori; nessuna scorciatoia sulle note interne (non si copiano dalla proposta).
- MVP 27: nessun cambio al payload delle proposte per gli altri partecipanti.
- Cancellazione dell'attività (regola esistente: solo senza iscritti): il collegamento sparisce con la riga, la proposta non cambia.
- Report ed export dei partecipanti non cambiano.

## Test previsti

Vedi [tasks.md](tasks.md). Guida admin `06-contributions.md` e `05-activities.md` IT/EN.
