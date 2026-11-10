# MVP 27 · Design

## Dati e migrazione `0027_contribution_hidden`

Migrazione additiva dopo `0026_exemptions_refunds` (se nel frattempo ne arriva un'altra, si prende il numero successivo alla testa corrente).

- `contribution.hidden_at` (datetime UTC, null), `contribution.hidden_by_id` (FK a `participant`, null), `contribution.hidden_reason` (stringa breve, null).
- Il tipo `wanted_skill` (12 caratteri) sta in `kind` `Unicode(16)`; **non c'è un CHECK** sulla colonna (verificato in `0007_activities`), quindi nessun vincolo da cambiare.
- Cronologia: stesso meccanismo delle altre azioni admin sulle prenotazioni (voce con autore e data); da riusare quello esistente delle modifiche della scheda.
- Downgrade: elimina le tre colonne (batch su SQLite, vincoli esplicitati per SQL Server).

## Tipo `wanted_skill`

- `CONTRIB_WANTED_SKILL` e `CONTRIBUTION_KINDS` in `models.py`; `validate_contribution` in `domain/activities.py` lo accetta senza altre modifiche.
- I due `Literal["talk","topic","skill"]` di `api/me.py` (`ContributionIn`) e `api/admin_views.py` (filtro) si estendono.
- Etichette da allineare: `KIND_LABELS` (`admin_views.py`), `CONTRIBUTION_LABELS` (`services/report_export.py`), `admin_texts.py`, testo `contribution.invalid_kind` in `i18n.py` (oggi elenca tre tipi), `KIND_KEYS` in `Contributions.tsx`, tipi TS in `auth.tsx` e `AdminContributions.tsx`, `AdminReport.tsx`, chiavi `contrib.*` / `rep.*` IT/EN, testi introduttivi `contrib.intro` e `contrib.adminIntro`. `domain/report.py` conta già per ogni voce di `CONTRIBUTION_KINDS`.

## Lettura per i partecipanti

`GET /api/me/proposals?kind=` in `api/me.py`, con `require_privacy_acceptance` come le altre letture personali. Logica in `services/contributions.py`:

1. Accesso: prenotazione corrente (`booking_changes.get_current_booking`) con `occupies_seats(effective_status(...))`, oppure admin. Altrimenti 403.
2. Contributi di tutte le prenotazioni attive dell'edizione corrente (stesso schema di `contribution_rows` in `services/views.py`), esclusi i propri (stesso partecipante) e quelli con `hidden_at`.
3. Consenso in batch: nuovo `consents.attendance_authorized(db, edition, participant_ids)` in `services/consents.py`. Una sola query sui `ConsentEvent` dell'edizione con `kind = attendance`, poi `latest_by_kind` e `ConsentState.is_authorized_for_current_document` di `domain/consents.py` per ogni partecipante. Nessun N+1.
4. Proiezione: `{ id, kind, title, description, author: { display_name } | null }`. Quando non c'è consenso `author` è `null`; non esistono altri campi dell'autore.
5. Ordine stabile (tipo, poi data di creazione); nessuna paginazione per ora (volumi piccoli, nel Backlog se crescono).

Il filtro si ricalcola a ogni lettura; la risposta ha `Cache-Control: no-store`.

## Admin

- `POST /api/admin/contributions/{id}/hide` (corpo: motivo facoltativo) e `.../unhide`, `require_admin`, idempotenti, con voce di cronologia.
- Vista e CSV dei contributi (`admin_views.py`) con colonna «Nascosta»; il report non cambia i totali.
- `AdminContributions.tsx`: pulsanti «Nascondi / Mostra» con conferma (`ConfirmDialog`) e marcatura delle righe nascoste.

## Frontend

- `Contributions.tsx`: nuovo comando «Proposte degli altri» visibile solo con prenotazione attiva; apre `ProposalsDialog` basato su `InfoDialog` (introdotto dall'MVP 26; se il 27 parte per primo si crea in questo MVP e il 26 lo riusa).
- Filtro per tipo, caricamento, vuoto, errore con «Riprova», «Autore non mostrato» per le anonime. I dati si caricano a ogni apertura e non restano in uno stato globale: al logout il componente è smontato.
- Il form dei contributi mostra l'avviso sul testo libero (`contrib.visibleNotice`).
- Tutti i testi in `frontend/src/i18n/{it,en}.ts`; messaggi del server in `backend/app/i18n.py`.

## Impatti sugli MVP precedenti

- MVP 17: si riusa il consenso «presenza» senza cambiarlo.
- MVP 20: chi ha l'informativa pendente può leggere ma non modificare i contributi (regola esistente); la consultazione delle proposte è una lettura e resta permessa.
- Il quarto tipo non cambia importi, presenze o email.

## Test previsti

Vedi [tasks.md](tasks.md). Guide `participant/07-contributions.md` e `admin/06-contributions.md` IT/EN.
