# MVP 2 · Pagina personale · Task

Branch di implementazione: `feat/mvp-02-pagina-personale`.

- [x] **1. Migrazione 0003**: colonne `hold_started_at` (backfill da `created_at`), `reminder_mid_sent_at`, `reminder_final_sent_at`, `cancel_requested_at`; modello aggiornato.
  Test: upgrade e downgrade da zero; il backfill riempie `hold_started_at` su una riga esistente.
- [ ] **2. Regole pure**: `can_edit_slots`, `can_request_cancellation`, `is_past_day`, `due_reminder`.
  Test: stati modificabili; giorno passato in Europe/Rome a cavallo della mezzanotte; promemoria a metà; finale; sovrapposizione sotto 48 ore; in ritardo solo il finale; già inviati; scaduta.
- [x] **3. Modifica slot (servizio e API)**: `change_slots` e `PUT /api/me/booking/slots`.
  Test: aggiunta con posto; aggiunta su slot pieno 409; rimozione libera il posto; slot già miei non bloccano su capienza piena; selezione vuota; importo ricalcolato con giorni distinti; scadenza invariata; confermata resta confermata con saldo da versare e con credito; stati vietati; giorno passato; accesso senza sessione 401.
- [x] **4. Disdetta (servizio e API)**: `request_cancellation`, `POST /api/me/booking/cancel`, email di conferma.
  Test: con pagamenti passa a `disdetta_richiesta`; senza pagamenti la prenotazione sparisce (anche `booking_slot`) e la persona resta; posti liberati in entrambi i casi; email inviata una volta; stati vietati; riscrizione dopo disdetta crea nuova prenotazione.
- [x] **5. Riattivazione e blocco**: la riattivazione in `services/payments.py` reimposta `hold_started_at` e azzera i promemoria; `register` imposta `hold_started_at`.
  Test: dopo la riattivazione i promemoria possono ripartire.
- [x] **6. Email reali**: `AcsEmailSender`, `build_email_sender` con `acs`, testi in `app/email/templates.py`, errori solo loggati.
  Test con client finto: invio corretto, errore non propagato, avvio rifiutato senza stringa di connessione.
- [x] **7. Job promemoria**: `app/jobs/send_reminders.py`.
  Test: mid e final una sola volta; rilancio idempotente; niente su confermata, scaduta, disdetta, coperta; in ritardo solo il finale; riattivata riparte; riepilogo stampato.
- [x] **8. Interfaccia `/io`**: modifica slot con anteprima, saldo o credito, disdetta con dialogo di conferma.
  Test vitest: anteprima e differenza; slot pieno non selezionabile; slot passati disabilitati; dialogo (apre, annulla, conferma); errore 409 mostrato.
- [ ] **9. Infrastruttura** (SCRITTO, NON VALIDATO: `az` e il compilatore Bicep non erano disponibili in sessione): Bicep (ACS, dominio gestito, job orario), `deploy.yml` con passo di risveglio dell'app dopo il deploy, `infra/README.md`. Il job riceve l'immagine nuova dallo stesso deploy Bicep.
  Test: `az bicep build` senza errori; `what-if`; dopo il deploy il job compare e gira.
- [x] **10. Chiusura**: lint e test verdi, migrazioni da zero, aggiornamento di Memory Bank e README, descrizione PR con checklist per organizzatori (ricevere una email vera, cambiare slot, disdire, verificare un promemoria).

## Da verificare a mano (dopo il deploy)

- Una email vera arriva e non finisce in spam (dominio gestito).
- Il promemoria arriva davvero all'orario atteso con l'app a zero repliche.
