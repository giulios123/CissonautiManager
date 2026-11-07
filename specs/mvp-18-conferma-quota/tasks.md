# MVP 18 · Task

**Implementazione in corso.** Dieci task ordinati, ciascuno con verifiche significative. Se il lavoro concreto supera questi confini, rivedere il pacchetto prima di allargarlo.

Sequenza, dipendenze e condizioni di attivazione nel [piano operativo comune 17–18](../piano-mvp-17-18.md); questa rimane la checklist canonica del 18.

- [x] **T18-1 · Calcolo e invarianti.** Funzione unica quota+totale, soglia di conferma, residuo operativo e credito; 46 test mirati passati su quota base/giorni distinti, extra e provider, insieme ai percorsi di prezzo esistenti.
- [x] **T18-2 · Modello/migrazione 0017.** Politica edizione, quota salvata e metadati del ciclo notifica; migrazione neutra da zero/legacy e metadata verificati su SQLite (12 test migrazione/importi passati). Il maintainer conferma superate tutte le prove SQL; la migrazione non attiva la politica e non invia email.
- [x] **T18-3 · Percorsi di conferma.** Registrazione gratuita, pagamenti, annulli, riattivazione, ricalcolo e promozione applicano la soglia della politica; 49 test mirati passati, inclusa soglia esatta/parziale, annullo che riporta in attesa, quota zero senza pagamento fittizio e i percorsi admin esistenti.
- [x] **T18-4 · Ricalcoli e report.** I ricalcoli salvano quota e totale insieme; API, report e CSV distinguono quota, residuo per confermare e saldo complessivo. Verificati prezzi aggiornati su slot/pasti/prezzi, riconciliazione e costi provider esclusi; 125 test backend mirati e 8 frontend passati, build/lint frontend verdi.
- [x] **T18-5 · Preview e applicazione admin.** API no-store con lock edizione/prenotazioni, fingerprint di tariffe/stati/scadenze/versamenti/selezioni/notifiche, idempotenza, audit e commit unico. 88 test backend mirati passati, inclusi dati cambiati, scadenza tra lettura e applicazione, blocker, pagamenti/hold intatti, chiuse e scadute escluse.
- [ ] **T18-6 · Ciclo di notifica e job.** Conferme da pagamento e senza nuovo incasso, coda differita ereditata senza doppio invio, annullo e reclamazione atomica; test timer/job concorrenti e fallimenti. Promemoria sulla sola quota, cadenza invariata.
- [ ] **T18-7 · Contratti e UI importi.** Schemi e pagina personale/ricevuta/scheda/Da incassare/editor con quota, residuo e totale; test IT/EN, credito e nessuna scadenza per soli extra. Nessuna modale B3.
- [ ] **T18-8 · UI di attivazione.** Impostazioni con differenze, credito prima/dopo ed email previste; test accessi, anteprima obsoleta, doppio clic, annullo e compatibilità politica legacy.
- [ ] **T18-9 · Cataloghi, email e guide.** Microtesti IT/EN, nuova conferma senza falso incasso e sezioni guide pertinenti; test template e segnaposto, checklist manuale [test-manuali.md](test-manuali.md).
- [ ] **T18-10 · Validazione e chiusura.** Suite/lint pertinenti, upgrade da zero e legacy SQLite/SQL Server, collaudo del passaggio su dati sintetici; aggiornare progress/domain approvato e checklist PR, distinguendo distribuzione del codice da attivazione reale della politica.

Branch di implementazione: `feat/mvp-18-conferma-quota`, derivato dalla base del 17. La distribuzione e l'attivazione reale della regola sono passaggi separati e non sono state eseguite.
