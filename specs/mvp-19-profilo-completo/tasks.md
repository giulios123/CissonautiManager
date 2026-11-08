# Checklist implementazione · MVP 19

- [x] 1. Requisiti, design, decisioni e prove manuali documentati.
- [x] 2. Modello e migrazione 0018 additiva; upgrade/downgrade SQLite.
- [x] 3. Cataloghi locali ISTAT/ISO, ricerca comuni, province e fallback geografici.
- [x] 4. Validazione, completezza server e derivazione partecipazione precedente.
- [x] 5. Nuove iscrizioni e sola lista; account noti protetti dal mutamento anonimo.
- [x] 6. API personale e richiamo precompilato non bloccante.
- [x] 7. API e scheda admin, audit, guida IT/EN.
- [x] 8. Suite completa, lint, TypeScript, build e checklist guida.

## Prove automatiche previste

- Nuovo invio e sola lista con profilo obbligatorio; atomicità e protezione account esistente.
- Ricerca città, omonimie, codice ISTAT non corrispondente, paese e città non censita.
- Dichiarazione social assente, derivazione storico confermato e dichiarazione senza storico.
- Completamento autenticato, accesso negato non autenticato, scheda admin senza booking e cronologia.
- Migrazione da zero e downgrade con database SQLite; SQL Server tramite CI.
- Suite frontend, build, TypeScript, lint e controllo guide.

Il collaudo visivo per telefono/desktop/tastiera/iframe e il test SQL Server restano da eseguire in CI o sul rilascio; vedi `test-manuali.md` e `pr-description.md`.
