# MVP 3 · Pannello admin completo · Task

Branch di implementazione: `feat/mvp-03-pannello-admin`. Parte dopo la chiusura dell'MVP 2.

**Dimensione**: 13 task, sopra la soglia di circa 10. Il maintainer ha scelto di tenerlo unico. Se in corso d'opera pesa troppo, il punto naturale di taglio è dopo il task 7 (viste e CSV) contro i task 8-12 (azioni).

- [x] **1. Migrazione 0004**: colonne rimborso su `booking`, colonne annullamento su `payment`, tabella `audit_log`; `paid_total` e `booking_view` escludono i pagamenti annullati.
  Test: upgrade e downgrade da zero; i saldi dell'MVP 1 restano invariati; un pagamento annullato non conta.
- [x] **2. Regole pure**: `has_evening`, `presence_by_slot`, `week_summary`, `review_reason`, `can_remove_admin`, `can_refund`, `status_after_void`.
  Test: sera esplicita, derivata e assente; scadute e disdette escluse dai presenti; ogni motivo di revisione; rimozione di sé, dell'ultimo admin e dell'admin seed rifiutata; rimborso oltre il pagato; confermata che scende sotto il dovuto torna in attesa.
- [x] **3. Export CSV**: `app/csv_export.py` e risposta con download.
  Test: separatore e BOM; virgola decimale; fuso Europe/Rome; accenti ed emoji; protezione dalle formule; nome file.
- [x] **4. Vista per persona**: `GET /api/admin/views/people` (+ CSV) e pagina.
  Test: filtri e ricerca; presenza serale derivata; CSV uguale alle righe filtrate; 403 per un partecipante.
- [x] **5. Vista per giorno e slot**: endpoint (+ CSV) e pagina.
  Test: presenti, capienza e liberi; sera derivata marcata; scadute e disdette escluse; sera senza limite.
- [x] **6. Settimana aggregata**: endpoint (+ CSV) e pagina.
  Test: conteggi per periodo; persone distinte; giorni vuoti a zero.
- [x] **7. Pagamenti da verificare**: endpoint (+ CSV) e pagina.
  Test: un caso per motivo; esce dalla vista quando si risolve.
- [ ] **8. Gestione admin**: servizio, endpoint e pagina.
  Test: promozione di un iscritto; creazione di un nuovo admin che entra col magic link; rimozione e i tre rifiuti; nessun limite di numero.
- [ ] **9. Rimborso**: servizio, endpoint e azione nella scheda.
  Test: passaggio a `rimborsata` con importo, data e nota; oltre il pagato rifiutato; stato non valido rifiutato; nessuna email inviata; cronologia scritta.
- [ ] **10. Modifica anagrafica, proroga e riattivazione manuale**: `PATCH` e `reactivate`.
  Test: email duplicata rifiutata; proroga ricalcola i promemoria; riattivazione con e senza posto; cronologia scritta.
- [ ] **11. Slot e disdetta da admin**: `PUT .../slots` con `force`, `POST .../cancel`.
  Test: capienza superata solo con `force` e segnalata; giorni passati ammessi; importo ricalcolato; disdetta per conto del partecipante con email; cronologia scritta.
- [ ] **12. Annullamento dei pagamenti**: servizio, endpoint e azione nella scheda.
  Test: motivo obbligatorio; non conta nel pagato; confermata torna in attesa con nuovo blocco; doppio annullamento rifiutato; cronologia scritta.
- [ ] **13. Chiusura**: lint e test verdi, migrazioni da zero, aggiornamento di Memory Bank e README, descrizione PR con checklist per organizzatori.

## Da verificare a mano

- Aprire i CSV in Excel o Numbers: accenti, importi e date corretti.
- Provare le viste con i dati reali dell'edizione.
- Rimuovere un admin e controllare che non possa più entrare nel pannello.
