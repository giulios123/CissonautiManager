# MVP 6 · Attività e contributi · Task

Branch di implementazione: `claude/quirky-meitner-qn9hwh` (vincolo di push della sessione). Parte dopo la chiusura dell'MVP 5.

**Dimensione**: 10 task.

- [x] **1. Migrazione 0007**: tabelle `activity`, `booking_activity`, `contribution`.
  Test: upgrade e downgrade da zero.
- [x] **2. Regole pure**: `is_eligible`, `activities_to_drop`, `check_join`, `check_activity_edit`, `validate_contribution`, attività in `compute_amount_due`.
  Test: presenza per fascia, sera derivata; attività che cade togliendo lo slot; piena, giorno passato, non presente; prezzo, giorno e fascia fissi con iscritti; capienza sotto gli iscritti rifiutata; eliminazione con iscritti rifiutata; importo con attività gratuite e a pagamento.
- [x] **3. Gestione admin delle attività**: servizio, endpoint e pagina «Attività».
  Test: creazione con giorno fuori edizione rifiutata; modifiche ammesse e rifiutate; eliminazione; cronologia; 403 per un partecipante.
- [x] **4. Adesione dalla pagina personale**: `change_activities` con lock, `PUT /api/me/booking/activities`, `ActivityPicker`.
  Test: adesione e ritiro con importo ricalcolato; in attesa coperta che diventa confermata; piena rifiutata; non presente rifiutata; giorno passato rifiutato e oggi ammesso; query con l'hint per SQL Server. Frontend: solo attività dove si è presenti, posti liberi.
- [x] **5. Attività e cambi della prenotazione**: `change_slots` toglie le attività senza titolo; riattivazione con controllo dei posti.
  Test: attività tolta e riportata nella risposta e nella cronologia; posto liberato da scadenza e disdetta; riattivazione rifiutata con attività piena e accettata con «forza».
- [x] **6. Attività dalla scheda admin**: `PUT /api/admin/registrations/{id}/activities` con `force`.
  Test: capienza superata solo con `force` e segnalata; giorni passati ammessi; presenza sempre richiesta; cronologia.
- [ ] **7. Vista per attività**: elenco e dettaglio con CSV.
  Test: iscritti e posti; scadute e disdette escluse; CSV per attività e complessivo.
- [ ] **8. Contributi lato partecipante**: servizio, endpoint, sezione «Cosa porti al camp».
  Test: aggiunta, modifica, rimozione; titolo obbligatorio; tipo non valido rifiutato; nessuno modifica i contributi di altri; spariscono con la prenotazione rimossa.
- [ ] **9. Vista Contributi e Settimana**: vista con filtro e CSV; colonna «Attività» in «Settimana».
  Test: filtro per tipo; contributi di prenotazioni non attive segnati; CSV con le righe filtrate; conteggi per giorno nella settimana.
- [ ] **10. Chiusura**: lint e test verdi, migrazioni da zero, Memory Bank (modifiche a `domain.md` approvate, `decisions.md`), README, descrizione PR con checklist per organizzatori.

## Da verificare a mano

- Creare un'attività a pagamento con capienza 2 e farla riempire da due telefoni diversi.
- Togliere uno slot e controllare che l'attività sparisca e l'importo scenda.
- Aprire i CSV di attività e contributi in Excel.
