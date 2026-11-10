# MVP 26 · Design

## Endpoint

`GET /api/admin/views/week/detail?metric=<m>&date=<YYYY-MM-DD>` in `backend/app/api/admin_views.py`, accanto a `week_view`, con la stessa dipendenza `require_admin`.

- `metric` ∈ `morning | afternoon | evening | people | lunch | dinner | activities`.
- `date` facoltativa: se manca vale tutta la settimana (totali). Se presente deve cadere nelle date dell'edizione, altrimenti 422.
- Risposta: `{ metric, date | null, count, adhesions?, distinct_people?, rows: [...] }`.
  - riga di persona: `{ date, booking_id, name, status, derived }`;
  - riga di pasto: `{ date, booking_id | null, guest_id | null, external, name, status | null }`;
  - riga di attività: `{ date, activity_id, activity_title, booking_id | null, guest_id | null, external, name }`.
- Non compaiono email, regime alimentare, allergie, note, importi, `payment_mode`.

## Nessuna formula nuova

I conteggi non si ricalcolano: si riusano i loader che alimentano `week_view` e `/views/slots` e `/views/meals`.

- **Coworking e persone:** `views_service.load_presence(db, now)` e `presence_by_slot` (`domain/presence.py`), con il flag `derived` per la sera (D-009). «Persone» = persone distinte del giorno, o della settimana per il totale (come `total_people` in `week_view`).
- **Pasti:** `views_service.load_meals(db, now)` (include gli esterni e i pasti con pagamento al fornitore, come `meal_counts_by_day`).
- **Attività:** oggi esiste solo `activity_signup_days(db, now)`, che restituisce date senza nomi. Si aggiunge `activity_signups(db, now)` in `services/views.py` che restituisce `(date, activity, persona | esterno)` e si riscrive `activity_signup_days` come `[s.date for s in activity_signups(...)]`, così il conteggio della tabella e quello del dettaglio nascono dalla stessa funzione.
- `count` è calcolato dal dettaglio stesso (lunghezza delle righe, o persone distinte per «persone»); un test confronta ogni metrica con la cella della `week_view`.

## Frontend

- Nuovo componente `frontend/src/InfoDialog.tsx`, ricavato da `ConfirmDialog.tsx` (focus trap, Esc, ritorno del focus): un solo comando «Chiudi», contenuto libero, larghezza maggiore tramite classe `.dialog-wide` in `styles.css` (oggi `[role="dialog"]` ha `max-width: 28rem`). Resta riusabile (l'MVP 27 lo usa per le proposte).
- `AdminWeek.tsx`: celle e totali diventano `<button class="link-number">` con `aria-label` composto dalle chiavi `week.detailOpen`. Il pulsante conserva il riferimento per il ritorno del focus (stesso schema di `AdminPayments.tsx`).
- Nuovo `WeekDetailDialog` (nello stesso file o in `pages/WeekDetail.tsx`): carica il dettaglio all'apertura, mostra caricamento/errore/vuoto, il confronto con il numero della cella, e l'elenco raggruppato per giorno per i totali.
- Chiavi `week.detail*` in `frontend/src/i18n/{it,en}.ts`; messaggi del server (se servono) in `backend/app/i18n.py`.
- Gli stili usano solo token esistenti (`theme.test.ts`).

## Impatti sugli MVP precedenti

Nessuna migrazione, nessun cambiamento di schema o di calcolo. La `week_view` e il suo CSV restano identici. Il 25a è già coperto perché pasti e attività leggono già gli esterni; il coworking non li include, e la modale lo riflette.

## Test previsti

Vedi [tasks.md](tasks.md). Guida `frontend/src/guide/{it,en}/admin/03-week.md` aggiornata in entrambe le lingue.
