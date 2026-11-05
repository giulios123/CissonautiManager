# MVP 5 · Pranzi e cene · Task

Branch di implementazione: `claude/quirky-meitner-qn9hwh` (vincolo di push della sessione). Parte dopo la chiusura dell'MVP 4.

**Dimensione**: 10 task.

- [x] **1. Migrazione 0006**: prezzi su `edition`, tabella `booking_meal`, colonne di regime, allergie e consenso su `booking`, tipo di testo `health`.
  Test: upgrade e downgrade da zero; edizioni e prenotazioni esistenti senza pasti.
- [x] **2. Regole pure**: `can_have_lunch`, `can_have_dinner`, `allowed_meals`, `meals_to_drop`, `check_meal_change`, `check_health_data`, `diet_counts`, `compute_amount_due`.
  Test: pranzo con sola mattina e con solo pomeriggio; cena con sera esplicita e derivata; nessun pasto senza presenza; pasti che cadono togliendo uno slot (e cena che resta con l'intero giorno); giorno passato; allergie senza consenso rifiutate e consenso tolto che le svuota; importo a zero pasti uguale a `compute_fee`.
- [x] **3. Importo unico e pasti che cadono**: `recompute_amount` al posto di `compute_fee`; `change_slots` toglie i pasti senza titolo.
  Test: tutti i test esistenti su importi e cambio slot restano verdi; pasto tolto riportato nella risposta e nella cronologia admin.
- [x] **4. Impostazioni**: prezzi di pranzo e cena, testo del consenso sanitario versionato.
  Test: prezzi negativi rifiutati; nuova versione del consenso; l'iscrizione resta aperta senza testo del consenso.
- [x] **5. Pasti dalla pagina personale**: `change_meals`, `PUT /api/me/booking/meals` con anteprima, `MealEditor`.
  Test: adesione e ritiro con importo ricalcolato; in attesa coperta che diventa confermata con email; confermata che resta tale; stato non valido rifiutato; pasto non ammesso rifiutato; giorno passato rifiutato e oggi ammesso. Frontend: caselle solo nei giorni di presenza, anteprima.
- [x] **6. Esigenze alimentari**: `PUT /api/me/booking/dietary`, sezione nella pagina.
  Test: regime senza consenso; allergie con consenso e versione salvata; errore senza consenso; consenso tolto che cancella; campo assente senza testo pubblicato; allergie assenti da email e risposte pubbliche; prenotazione rimossa che porta via i dati.
- [x] **7. Pasti dalla scheda admin**: `PUT /api/admin/registrations/{id}/meals`, scheda estesa.
  Test: giorni passati ammessi; cronologia scritta; 403 per un partecipante; regime e allergie visibili all'admin.
- [x] **8. Vista Pasti**: endpoint (+ CSV) e pagina.
  Test: conteggi per giorno e pasto; scadute e disdette escluse; conteggio per regime con «senza indicazione»; allergie con nome; CSV con una riga per persona; avviso prima del download.
- [ ] **9. Settimana**: colonne pranzi e cene nella vista e nel CSV.
  Test: conteggi per giorno; giorni senza pasti a zero; totali.
- [ ] **10. Chiusura**: lint e test verdi, migrazioni da zero, Memory Bank (modifiche a `domain.md` approvate, `decisions.md`), README, descrizione PR con checklist per organizzatori.

## Da verificare a mano

- Aprire il CSV dei pasti in Excel: accenti, regimi e allergie leggibili.
- Provare da telefono la sezione pasti con un'edizione di una settimana.
- Controllare con chi cucina che la vista «Pasti» dia le informazioni che servono.
