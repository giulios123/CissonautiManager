# MVP 7 · Inviti e report · Task

Branch di implementazione: `feat/mvp-07-inviti-report`. Parte dopo la chiusura degli MVP 4, 5 e 6. **Prima del task 1**: confrontare la sezione «Ipotesi sugli MVP 4-6» di `design.md` con il codice reale e aggiornarla.

**Dimensione**: 8 task. Punto di taglio naturale, se serve: task 1-5 (priorità +1) contro task 6-7 (report).

- [ ] **1. Migrazione**: `plus_one_verified_at` e `plus_one_verified_by_id` su `participant`.
  Test: upgrade e downgrade da zero; i partecipanti esistenti risultano non verificati.
- [ ] **2. Regole pure**: `can_verify_plus_one`, `waitlist_priority_key`, `ordered_waitlist`, `edition_report`.
  Test: testo vuoto o di soli spazi rifiutato; verificato entrato dopo passa davanti a non verificato entrato prima; parità tra verificati per data e poi per id; nessun verificato = ordine di ingresso; ogni sezione del report con dati minimi; prenotazioni scadute e disdette escluse da presenze e pasti ma contate negli incassi; pagamenti annullati esclusi; netto, da incassare e crediti.
- [ ] **3. Promozione con priorità**: la promozione dell'MVP 4 usa `ordered_waitlist`.
  Test: liberando un posto viene promosso il +1 verificato; una verifica fatta dopo l'ingresso vale alla promozione successiva; togliendo la verifica torna l'ordine di ingresso; il limite della lista non cambia; email e blocco come nell'MVP 4.
- [ ] **4. Verifica del +1 da admin**: servizio, `PUT .../plus-one`, spunta nella scheda.
  Test: verifica e rimozione salvate con chi e quando; 422 senza «invitato da»; 403 per un partecipante; cronologia scritta; vitest sulla spunta (etichetta, stato, errore).
- [ ] **5. Lista d'attesa con priorità visibile**: posizione effettiva, «+1» e «da verificare» nella vista e nel CSV.
  Test: ordine della vista uguale a quello di promozione; colonne del CSV.
- [ ] **6. Report: endpoint e CSV**: `report_data` e `GET /api/admin/views/report`.
  Test: totali di presenza uguali alla vista «Settimana»; incassi uguali alla somma della vista «Persone»; CSV `sezione;voce;valore` con BOM e virgola decimale; nessun nome nelle esigenze alimentari; sezioni vuote a zero; 403 per un partecipante.
- [ ] **7. Report: pagina e stampa**: `AdminReport.tsx`, voce di menu, `@media print`.
  Test vitest: tutte le sezioni presenti; importi formattati in euro; bottone CSV.
- [ ] **8. Chiusura**: lint e test verdi, migrazioni da zero, Memory Bank (`progress.md`, `activeContext.md`, `decisions.md`, `domain.md` con le sole modifiche approvate), descrizione PR con checklist per organizzatori.

## Da verificare a mano

- Con uno slot pieno e due persone in lista, verificare il +1 della seconda, liberare un posto e controllare che l'email arrivi a lei.
- Stampare il report dal telefono e dal computer (anche in PDF).
- Aprire il CSV del report in Excel o Numbers.
- Confrontare i numeri del report con quelli dell'edizione reale.
