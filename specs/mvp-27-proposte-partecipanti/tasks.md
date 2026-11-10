# MVP 27 · Task

- [ ] **T27-1** Tipo `wanted_skill`: costanti, validazione, `Literal`, etichette di backend (CSV, report, `admin_texts`, messaggio di errore) e di frontend, chiavi IT/EN. Test: i quattro tipi in editor, admin, CSV e report; righe precedenti intatte.
- [ ] **T27-2** Migrazione `0027_contribution_hidden` e modello. Test: upgrade/downgrade su SQLite, vincoli compatibili con SQL Server.
- [ ] **T27-3** Helper batch `attendance_authorized` in `services/consents.py`. Test: concesso valido, revocato, negato, assente, versione precedente non riaccettata, due edizioni.
- [ ] **T27-4** `GET /api/me/proposals` con accesso, esclusioni e proiezione dell'autore. Test: autore con consenso, anonimo senza; nessun id/email/telefono nel payload; escluse proprie, scadute, disdette, in lista d'attesa, nascoste, altra edizione; 401/403; filtro per tipo.
- [ ] **T27-5** Admin: `hide`/`unhide` idempotenti con cronologia, colonna «Nascosta» in vista e CSV. Test: 403 per non admin, doppio invio, proposta nascosta fuori dalla consultazione ma visibile all'autore.
- [ ] **T27-6** Frontend partecipante: comando, `ProposalsDialog`, filtro, stati e avviso sul testo libero. Test: apertura/chiusura e focus, anonimo, vuoto, errore, comando assente senza prenotazione attiva.
- [ ] **T27-7** Frontend admin: nascondi/mostra con conferma e marcatura. Test.
- [ ] **T27-8** Guide IT/EN (partecipante e admin), `test-manuali.md` pronto, suite completa, Ruff, lint, TypeScript, build e migrazioni da zero verdi.
