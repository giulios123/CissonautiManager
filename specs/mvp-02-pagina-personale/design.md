# MVP 2 · Pagina personale · Design

## Modello dati (migrazione 0003)

Nuove colonne su `booking`, tutte `UtcDateTime` nullable salvo dove indicato:

| Campo | Scopo |
|-------|-------|
| `hold_started_at` | inizio del blocco corrente. Backfill = `created_at`. Cambia solo alla riattivazione, perché i promemoria sono relativi al blocco, non alla creazione |
| `reminder_mid_sent_at` | invio del promemoria a metà blocco |
| `reminder_final_sent_at` | invio del promemoria 24 ore prima della scadenza |
| `cancel_requested_at` | quando il partecipante ha chiesto la disdetta |

La riattivazione in `services/payments.py` imposta `hold_started_at = now` e azzera i due campi dei promemoria. Vale anche per la lista d'attesa (MVP 4), che userà lo stesso meccanismo.

## Regole di dominio (funzioni pure)

In `app/domain/booking.py`:

- `can_edit_slots(status) -> bool`: vero per `in_attesa_pagamento` e `confermata`.
- `can_request_cancellation(status) -> bool`: stesse condizioni.
- `is_past_day(day, now) -> bool`: il giorno è trascorso in Europe/Rome.

In `app/domain/reminders.py`:

- `due_reminder(hold_started_at, hold_expires_at, mid_sent_at, final_sent_at, now) -> "mid" | "final" | None`.
  - soglia a metà: `started + (expires - started) / 2`;
  - soglia finale: `expires - 24h`;
  - se `expires - started < 48h` (soglie sovrapposte) esiste solo `mid`;
  - se `now >= expires` non è dovuto nulla (la prenotazione è scaduta);
  - se è passata la soglia finale ed `final` non è stato inviato, risponde `final` anche se `mid` non è mai partito.

La logica di stato resta in `effective_status`; il job non decide da solo se una prenotazione è scaduta.

## Servizi

`app/services/booking_changes.py` (riusato dall'admin nell'MVP 3):

- `change_slots(db, booking, slot_ids, now, force=False) -> ChangeResult`:
  1. rifiuta stati non modificabili;
  2. blocca gli slot con `slots_for_update` (già pronto per SQL Server);
  3. per i soli slot **aggiunti** verifica i posti con `free_by_slot` e `has_free_seat`; gli slot già miei non contano come nuova occupazione;
  4. rifiuta giorni passati (salvo `force`, usato solo dall'admin);
  5. ricalcola `amount_due_cents` con `compute_fee` sull'insieme finale;
  6. non tocca stato né `hold_expires_at`.
- `request_cancellation(db, sender, booking, now) -> CancelOutcome`: senza pagamenti registrati elimina `booking_slot` e `booking` (esito `removed`); con pagamenti stato `disdetta_richiesta` e `cancel_requested_at` (esito `requested`). In entrambi i casi i dati dell'email si leggono prima dell'eliminazione e l'email di conferma parte dopo il commit.

Errori di dominio: `SlotsFull`, `InvalidSlots`, `NotEditable`, `PastDay`, `EmptySelection`.

## Email

- `app/email/acs.py`: `AcsEmailSender` con `azure-communication-email` (`EmailClient.from_connection_string`, `begin_send`). Gli errori sono loggati e non propagati.
- `build_email_sender` gestisce `acs`; con `acs` e senza stringa di connessione l'app non parte.
- Testi in italiano, un unico modulo `app/email/templates.py` (oggi le stringhe stanno dentro i servizi): iscrizione, magic link, conferma pagamento, promemoria, disdetta.

## Job promemoria

`app/jobs/send_reminders.py`, lanciato con `python -m app.jobs.send_reminders`:

1. `expire_overdue`;
2. carica le prenotazioni `in_attesa_pagamento` non coperte;
3. per ciascuna calcola `due_reminder`;
4. in una transazione per riga: scrive `reminder_*_sent_at` e fa commit **prima** di spedire l'email. Un invio fallito perde un promemoria (accettato: meglio di un doppio invio, e l'errore è nei log);
5. stampa un riepilogo (esaminate, inviate per tipo).

## Endpoint

| Metodo e path | Accesso | Scopo |
|---------------|---------|-------|
| `PUT /api/me/booking/slots` | sessione | `{slot_ids}`: modifica gli slot, risponde con la prenotazione aggiornata. 409 con l'elenco degli slot pieni, 422 per selezione vuota o giorno passato, 409 `not_editable` per stato non valido |
| `POST /api/me/booking/cancel` | sessione | disdetta; risponde `{outcome: "removed" | "requested"}` |
| `GET /api/me` | sessione | esteso con `editable` e `can_cancel` |
| `GET /api/public/edition` | pubblico | già esistente, usato per i posti liberi |

La prenotazione su cui si agisce è quella più recente del partecipante nell'edizione attiva (come `GET /api/me`).

## Pagine

`/io` (`frontend/src/pages/Personal.tsx`) si divide in sezioni:

- **Riepilogo**: stato, importo, pagato, saldo o credito, scadenza, causale, istruzioni.
- **I tuoi slot**: giorni e slot come nel modulo di iscrizione, con i miei già selezionati. Riuso di `feePreview`, `isFull` e `seatsLabel` da `frontend/src/booking.ts`. Anteprima di nuovo importo e differenza prima di salvare. Gli slot di giorni passati sono disabilitati.
- **Disdetta**: pulsante con dialogo di conferma accessibile (focus gestito, `Esc`, ruoli ARIA).
- **Password**: già presente.

## Infrastruttura

- `infra/main.bicep`: Communication Service, Email Service, dominio gestito Azure (`AzureManagedDomain`), collegamento dominio e servizio, `ACS_CONNECTION_STRING` come segreto, `EMAIL_PROVIDER=acs`, `EMAIL_FROM` dal dominio.
- **Container Apps Job** con trigger `Schedule` e cron `0 * * * *`, stessa immagine, stessi segreti, comando `python -m app.jobs.send_reminders`. Gira anche se l'app è a zero repliche.
- `deploy.yml`: aggiorna l'immagine del job insieme a quella dell'app.
- `infra/README.md`: sezione email (limiti di invio bassi del dominio gestito, rischio spam, passaggio a dominio proprio come evoluzione) e sezione job.
- `.env.example`: già contiene le variabili; aggiornare i commenti.

## Impatti sugli MVP precedenti

- `register` e `payments` usano i nuovi testi email e impostano `hold_started_at`.
- `booking_view` non espone `hold_started_at` (alla UI non serve): aggiunge solo `editable` e `can_cancel`.
- Il flusso admin dell'MVP 1 non cambia. Il servizio `change_slots` viene riusato nell'MVP 3.

## Scelte tecniche da registrare in `decisions.md`

- Container Apps Job orario invece di cron GitHub Actions.
- Dominio gestito Azure per l'email, evoluzione a dominio proprio.
- Segno l'invio prima di spedire (al più una volta, mai doppio).
- Importo che sale su prenotazione confermata: resta confermata.
- Disdetta senza pagamenti: la prenotazione si elimina (si perde la traccia dei testi legali accettati, accettato perché non è mai stato versato nulla).
