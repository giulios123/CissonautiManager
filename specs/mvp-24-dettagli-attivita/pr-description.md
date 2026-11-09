# MVP 24 · Dettagli e note delle attività

## Descrizione

Aggiunge titoli e descrizioni IT/EN per le attività, mantenendo il testo legacy come fallback. Partecipanti e admin possono aprire schede localizzate; gli admin possono aggiornare note riservate con storico di autore e data. Il CSV admin include la nota corrente anche quando un’attività non ha iscritti. Le regole attuali di adesione e capienza restano invariate.

Il branch `feat/mvp-24-dettagli-attivita` è indipendente dall’MVP 23. Le modifiche proposte a `domain.md` non sono state applicate. Non è stato eseguito alcun deploy.

## Verifiche automatiche

- Backend: 1114 test passati.
- Frontend: 410 test passati.
- Ruff, formattazione, lint, TypeScript, build, controllo Guide e sincronizzazione modelli/migrazioni: passati.
- Migrazione SQLite da zero e dalla revisione precedente: passata.
- SQL Server: da eseguire; il driver ODBC disponibile su macOS non carica OpenSSL e non consente la connessione al server temporaneo.

## Collaudo per gli organizzatori

La checklist dettagliata è in [`test-manuali.md`](test-manuali.md). Verificare almeno:

- creazione e modifica dei testi in entrambe le lingue e fallback delle attività legacy;
- correzione di orari e prezzi senza tradurre prima i testi;
- scheda da telefono e navigazione da tastiera;
- storico delle note con autore/data e assenza di note nei payload partecipante;
- CSV admin con e senza iscritti e rifiuto dell’URL diretto per anonimi e partecipanti.
