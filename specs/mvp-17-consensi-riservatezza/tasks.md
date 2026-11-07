# MVP 17 · Task

**Stato: in implementazione.** Otto task ordinati. Ogni task si spunta dopo aver eseguito le verifiche pertinenti.

Sequenza, dipendenze e condizioni di rilascio nel [piano operativo comune 17–18](../piano-mvp-17-18.md); questa rimane la checklist canonica del 17.

- [x] **T17-1 · Modello e migrazione 0016.** Corpi IT/EN nullable per legacy, finalità e `consent_event` indipendente dal booking; upgrade/downgrade in test, dati popolati, metadata e SQL Server, nessuna prova fittizia. Verificato da zero/0015 e confrontato il metadata su SQLite; SQL Server per la nuova migrazione resta da verificare.
- [x] **T17-2 · Dominio e servizi delle scelte.** Stato per edizione/finalità, validità versione, no-op e conflitti; test concesso/negato/revocato/non espresso, versione vecchia, documento di altra edizione e concorrenza. Verificati 9 test di dominio/servizio; gli handler HTTP verranno innestati nei task successivi.
- [ ] **T17-3 · Pubblicazione e letture legali.** Editor/API IT/EN con versione unica e legacy leggibile; test pubblicazione concorrente, testi incompleti e immutabilità delle versioni.
- [ ] **T17-4 · Iscrizione e sola lista.** Integrare scelte nella transazione; test account nuovo/noto/scaduto, più liste, rollback per capienza/testi e nessuna modifica anonima di prove esistenti. Verificare la minimizzazione della ricevuta.
- [ ] **T17-5 · Gestione autenticata e lettura admin.** Endpoint propri, sezione personale anche senza booking, dettaglio admin solo lettura; test accessi, proprietà, revoca con testo aggiornato e sopravvivenza degli eventi al ciclo booking, senza implementare lo storico A6.
- [ ] **T17-6 · Form e gestione errori IT/EN.** Caselle, testo/versioni, indisponibilità e dati conservati al cambio lingua o conflitto legale; test componenti, sola lista e navigazione da tastiera.
- [ ] **T17-7 · Guide e collaudo.** Aggiornare guide IT/EN e verificare [test-manuali.md](test-manuali.md), telefono/desktop/iframe; tenere i testi legali definitivi separati dai dati di test.
- [ ] **T17-8 · Validazione e chiusura.** Suite e lint pertinenti, migrazione da zero/legacy nei due database; aggiornare progress/domain con sole variazioni approvate e preparare checklist PR. Distinguere meccanismo completato da prontezza dei testi di produzione.

Prima dell'implementazione il branch previsto è `feat/mvp-17-consensi-riservatezza`; nessun branch o commit applicativo viene creato dalla preparazione della spec.
