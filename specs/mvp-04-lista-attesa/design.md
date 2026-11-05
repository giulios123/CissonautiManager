# MVP 4 · Lista d'attesa · Design

## Modello dati (migrazione 0005)

Su `edition`: `waitlist_percent` (int, default 20).

Nuova tabella `waitlist_entry`:

| Campo | Scopo |
|-------|-------|
| `id` | |
| `slot_id` | slot pieno per cui la persona aspetta |
| `participant_id` | chi aspetta |
| `created_at` | ordine di arrivo |
| `closed_at` (nullable) | voce chiusa: promossa, uscita, rimossa dall'admin, disdetta |
| `close_reason` (nullable) | `promoted`, `left`, `removed`, `cancelled`, `booked` |
| `promoted_booking_id` (nullable) | prenotazione che ha ricevuto lo slot |
| `privacy_document_id`, `privacy_accepted_at` (nullable) | testi accettati da chi entra in lista dal modulo |
| `disclaimer_document_id`, `disclaimer_accepted_at` (nullable) | idem |

Una voce è attiva se `closed_at IS NULL`. Al massimo una voce attiva per (slot, persona): il controllo sta nel servizio, sotto il lock dello slot (un indice unico filtrato non è portabile tra SQLite e SQL Server). Le voci chiuse restano: servono alla cronologia e al report dell'MVP 7.

## Regole di dominio (funzioni pure)

In `app/domain/waitlist.py`:

- `waitlist_limit(capacity: int | None, percent: int) -> int`: `None` (sera) dà 0; altrimenti `capacity * percent // 100`.
- `can_join(free: int | None, active_entries: int, limit: int, already_booked: bool, already_listed: bool, past_day: bool) -> JoinCheck`: con motivo del rifiuto (`not_full`, `list_full`, `already_booked`, `already_listed`, `past_day`).
- `queue(entries) -> list`: ordine di promozione, oggi per `created_at` e poi `id`. È il punto in cui l'MVP 7 aggiungerà la priorità del +1.
- `position(entries, entry_id) -> int`: posizione mostrata al partecipante.
- `hold_after_promotion(current_expiry: datetime, now: datetime, hold_days: int) -> datetime`: la più lontana tra la scadenza attuale e `hold_deadline(now, hold_days)` (`app/domain/booking.py`).
- `promotion_kind(status) -> "add_to_pending" | "add_to_confirmed" | "new_booking"`.

Il ricalcolo dei promemoria dopo l'allungamento del blocco riusa `reminders_to_keep_after_extension` (`app/domain/reminders.py`).

## Servizi

`app/services/waitlist.py`:

- `join(db, participant, slot, now, legal=None)`: blocca lo slot con `slots_for_update` (`app/services/seats.py`), verifica `can_join` con `free_by_slot` e il conteggio delle voci attive, crea la voce.
- `leave(db, participant, entry_id, now)` e `remove(db, admin, entry_id, now)` (con `audit.log`).
- `close_for_participant(db, participant, reason)`: usata dalla disdetta.
- `promote_freed(db, sender, settings, slot_ids, now) -> list[Promotion]`: per ogni slot, sotto lock, finché ci sono posti liberi e voci in coda, promuove il primo. Promozione: prenotazione attiva della persona (`get_current_booking` in `booking_changes.py`, con `effective_status`) a cui si aggiunge lo slot, oppure nuova `Booking` con i testi legali della voce. Importo con `compute_fee` (dall'MVP 5 con `recompute_amount`). Commit, poi email.
- La voce di una persona che prenota da sé lo stesso slot si chiude con `booked` dentro `change_slots` e `register`.

`app/services/registration.py`: `RegistrationData` guadagna `waitlist_slot_ids`. Gli slot liberi seguono il flusso di oggi; quelli in lista passano da `join` nella stessa transazione. Con soli slot in lista non nasce la `Booking`: `RegistrationResult` ha `booking=None` e la lista delle voci. Il controllo D-005 sull'iscrizione attiva considera anche le voci attive (chi è già in lista riceve il magic link).

Agganci a `promote_freed`, chiamato dopo il commit dell'operazione che libera i posti: `request_cancellation` e `change_slots` (`booking_changes.py`), azioni admin su slot e disdetta (`api/admin_registrations.py`), salvataggio delle Impostazioni quando una capienza sale (`services/edition.py`).

Job orario: `app/jobs/send_reminders.py` aggiunge, dopo `expire_overdue`, un passo che cerca gli slot pieni con voci attive e posti liberi e chiama `promote_freed`. Stesso comando e stessa pianificazione: il Bicep non cambia. Il riepilogo nei log conta anche le promozioni.

## Email

Nuovi template in `app/email/templates.py`:

- `waitlist_joined_email`: conferma dell'ingresso in lista dal modulo pubblico (con magic link), oppure sezione aggiunta a `registration_email` quando ci sono anche slot liberi.
- `waitlist_promoted_email`: «si è liberato un posto» con slot, nuovo importo, saldo, istruzioni di pagamento e, se in attesa, la scadenza; per una nuova prenotazione anche il magic link.
- `cancellation_email`: una riga in più quando la disdetta chiude voci in lista.

## Endpoint

| Metodo e path | Scopo |
|---------------|-------|
| `GET /api/public/edition` | esistente, gli slot pieni guadagnano `waitlist_open` e `waitlist_free` |
| `POST /api/public/registrations` | esistente, accetta `waitlist_slot_ids`; errori `waitlist_full`, `slot_not_full` |
| `GET /api/me` | esteso con `waitlist: [{entry_id, slot, position}]`, anche senza prenotazione |
| `POST /api/me/waitlist` | `{slot_id}` |
| `DELETE /api/me/waitlist/{entry_id}` | uscita dalla lista |
| `GET /api/admin/views/slots` | esteso con la coda per ogni slot (+ CSV) |
| `DELETE /api/admin/waitlist/{entry_id}` | rimozione da parte dell'admin |
| `GET /api/admin/registrations` | include chi è solo in lista, con stato `in_lista` |
| `PUT /api/admin/edition` | esteso con `waitlist_percent` |

## Pagine

- `Registration.tsx`: gli slot pieni con lista aperta hanno la casella «in lista»; riepilogo finale diviso tra prenotato e in lista.
- `Personal.tsx`: sezione «Lista d'attesa» con posizione e «Esci dalla lista»; nel `SlotEditor` gli slot pieni offrono «Mettiti in lista».
- `AdminSlots.tsx`: coda sotto ogni slot pieno, con «Rimuovi»; `AdminRegistrationDetail.tsx` mostra le voci; `AdminSettings.tsx` la percentuale.

## Impatti sugli MVP precedenti

- **MVP 1**: la registrazione può terminare senza prenotazione; i test esistenti restano validi perché senza `waitlist_slot_ids` il flusso non cambia.
- **MVP 2**: disdetta e cambio slot chiamano la promozione; il job orario fa un passo in più.
- **MVP 3**: «Persone» e «Giorni e slot» mostrano la lista; la scheda di una persona senza prenotazione esiste (oggi la scheda è per prenotazione: si apre per persona quando non c'è prenotazione).
- **MVP 7**: la priorità del +1 si innesta in `queue`.

## Scelte tecniche da registrare in `decisions.md`

- Voci di lista chiuse, mai cancellate, con motivo.
- Promozione dopo il commit dell'operazione che libera il posto, in una transazione propria con lock sullo slot.
- Promozione delle scadenze nel job orario esistente invece che alla lettura (la lettura non manda email).
- Testi legali salvati sulla voce per chi è solo in lista.
