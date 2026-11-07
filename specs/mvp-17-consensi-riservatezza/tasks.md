# MVP 17 · Task

**Stato: T17-1–6 implementati sul branch** `feat/mvp-17-consensi-riservatezza`; T17-7/8 e i collaudi manuali restano aperti.

Sequenza, dipendenze e condizioni di rilascio nel [piano operativo comune 17–18](../piano-mvp-17-18.md); questa rimane la checklist canonica del 17.

- [x] **T17-1 · Modello e migrazione 0016.** Corpi IT/EN nullable per legacy, finalità e `consent_event` indipendente dal booking; upgrade/downgrade in test, dati popolati, metadata e SQL Server, nessuna prova fittizia. Verificato da zero/0015 e confrontato il metadata su SQLite; il maintainer conferma superate tutte le prove SQL.
- [x] **T17-2 · Dominio e servizi delle scelte.** Stato per edizione/finalità, validità versione, no-op e conflitti; test concesso/negato/revocato/non espresso, versione vecchia, documento di altra edizione e concorrenza. Verificati 9 test di dominio/servizio; gli handler HTTP verranno innestati nei task successivi.
- [x] **T17-3 · Pubblicazione e letture legali.** Editor/API IT/EN con versione unica e legacy leggibile; test versioni successive, testi incompleti e corpo originale. Validati 104 test backend pertinenti, 25 frontend, lint e build; il maintainer conferma superate tutte le prove SQL.
- [x] **T17-4 · Iscrizione e sola lista.** Integrare scelte nella transazione; test account nuovo/noto/scaduto, più liste, rollback per capienza/testi e nessuna modifica anonima di prove esistenti. Verificare la minimizzazione della ricevuta. Passati 62 test backend e 21 frontend; codice noto omesso dalla risposta e inviato solo nell'email al proprietario.
- [x] **T17-5 · Gestione autenticata e lettura admin.** Endpoint propri, sezione personale anche senza booking, dettaglio admin solo lettura; test accessi, revoca con testo aggiornato e sopravvivenza degli eventi alla rimozione del booking, senza implementare lo storico A6. Verificati 50 test backend mirati.
- [x] **T17-6 · Form e gestione errori IT/EN.** Caselle separate, testi/versioni, indisponibilità e selezione conservata al cambio lingua o conflitto; form con etichette native e navigazione da tastiera. Passati 2 test dedicati e 19 test frontend pertinenti; il lint ha solo il warning preesistente in `ConfirmDialog.tsx`.
- [ ] **T17-7 · Guide e collaudo.** Guide IT/EN aggiornate; eseguire [test-manuali.md](test-manuali.md) su telefono/desktop/iframe e registrare gli esiti. I test visivi manuali non sono stati eseguiti in questa sessione; tenere i testi legali definitivi separati dai dati di test.
- [ ] **T17-8 · Validazione e chiusura.** Suite e lint pertinenti, migrazione da zero/legacy nei due database; aggiornare progress/domain con sole variazioni approvate e preparare checklist PR. Distinguere meccanismo completato da prontezza dei testi di produzione.

T17-1–6 sono implementati e committati sul branch `feat/mvp-17-consensi-riservatezza`; il maintainer conferma superate le prove SQL. T17-7/8 restano aperti per CI della PR e prove manuali; i testi legali definitivi vanno validati prima della produzione.
