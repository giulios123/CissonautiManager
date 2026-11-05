# MVP 7 · Inviti e report · Task

Branch di implementazione: `feat/mvp-07-inviti-report` (se la sessione non può pushare su un branch con questo nome, si lavora su quello assegnato, come per gli MVP 2-8). Parte dopo la conferma di questa spec.

**Dimensione**: 9 task, sotto la soglia di circa 10. Punto di taglio naturale, se serve: task 1-5 (priorità +1) contro task 6-8 (report).

- [ ] **1. Migrazione 0008**: `plus_one_verified_at` e `plus_one_verified_by_id` su `participant`.
  Test: upgrade e downgrade da zero (anche con 0001-0007); i partecipanti esistenti risultano non verificati.
- [ ] **2. Regole pure della priorità**: `queue` e `position` con `priority_ids`, `can_verify_plus_one`.
  Test: verificato arrivato dopo passa davanti a non verificato arrivato prima; parità tra verificati per data e poi per id; nessun verificato = ordine di oggi (test esistenti invariati); `position` coerente con `queue`; testo vuoto o di soli spazi rifiutato.
- [ ] **3. Priorità nelle liste**: `active_entries` carica i verificati e li passa a `queue`.
  Test: liberando un posto viene promosso il +1 verificato; una verifica fatta dopo l'ingresso vale alla promozione successiva; togliendo la verifica torna l'ordine di arrivo; il limite della lista non cambia (con la lista piena nemmeno un +1 entra); `position_of` e la pagina personale seguono; email e promozione come nell'MVP 4.
- [ ] **4. Verifica del +1 da admin**: servizio, `PUT /api/admin/participants/{id}/plus-one`, estensione della scheda, spunta nella scheda e in «Giorni e slot».
  Test: verifica e rimozione salvate con chi e quando; 422 senza «invitato da»; 404 persona sconosciuta; 403 per un partecipante; cronologia scritta, anche senza prenotazione; svuotare «invitato da» dalla modifica dati fa cadere la verifica; vitest sulla spunta (etichetta, stato, errore).
- [ ] **5. Lista d'attesa con la priorità visibile**: posizione effettiva, «+1» e «da verificare» in `AdminSlots.tsx`, colonne nel CSV.
  Test: l'ordine della vista è quello di promozione; colonne e valori del CSV; vitest sull'etichetta.
- [ ] **6. Regole pure del report**: `edition_report`.
  Test: ogni sezione con dati minimi; confermate e in attesa separate; scadute, disdette e rimborsate escluse da presenze, pasti e attività ma contate negli incassi; pagamenti annullati esclusi; netto, da incassare e crediti; scomposizione del dovuto che torna al totale anche con un prezzo cambiato (riga «scarto»); picco, media e giorni-persona; sezioni vuote a zero.
- [ ] **7. Report: dati, endpoint e CSV**: `load_report`, `GET /api/admin/views/report`.
  Test: totali di presenza uguali alla vista «Settimana», pasti a «Pasti», attività a «Attività», incassi alla somma di «Persone»; CSV con BOM, `;`, virgola decimale; nessun nome né testo di allergie nel report, solo il numero; 403 per un partecipante.
- [ ] **8. Report: pagina e stampa**: `AdminReport.tsx`, voce di menu, `@media print`.
  Test vitest: tutte le sezioni presenti; importi formattati in euro; bottone CSV; sezione vuota a zero; `theme.test.ts` ancora verde.
- [ ] **9. Chiusura**: lint e test verdi, migrazioni da zero, Memory Bank (`progress.md`, `activeContext.md`, `decisions.md`, `domain.md` con le sole modifiche approvate), README e AGENTS.md se serve, descrizione PR con checklist per organizzatori.

## Da verificare a mano

- Con uno slot pieno e due persone in lista, verificare il +1 della seconda, liberare un posto e controllare che l'email arrivi a lei e che la prima veda scendere la sua posizione.
- Verificare un +1 che è solo in lista (senza scheda) da «Giorni e slot».
- Stampare il report dal telefono e dal computer (anche in PDF).
- Aprire il CSV del report in Excel o Numbers.
- Confrontare i numeri del report con quelli dell'edizione reale.
