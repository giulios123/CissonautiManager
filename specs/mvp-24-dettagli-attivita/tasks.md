# MVP 24 · Task

- [x] **T24-1** Definire localizzazione/fallback e regole di validazione titolo/descrizione con test.
- [x] **T24-2** Aggiungere migrazione additiva per testi IT/EN e note revisionate, preservando i testi legacy; migrazione e sincronizzazione SQLite verificate.
- [x] **T24-3** Aggiornare API admin per IT/EN, fallback e scrittura atomica di nota più revisione.
- [x] **T24-4** Aggiornare API partecipante con schemi localizzati senza note e autorizzazione per ruolo.
- [x] **T24-5** Aggiornare schede admin e partecipante con orari, costo, destinatario, istruzioni e capienza.
- [x] **T24-6** Usare titolo localizzato in picker, liste e riepiloghi senza cambiare le regole di adesione.
- [x] **T24-7** Estendere il CSV admin con nota corrente, anche senza iscritti, mantenendo il controllo admin.
- [x] **T24-8** Aggiornare dizionari e guide IT/EN; checklist manuale preparata.
- [x] **T24-9** Suite backend completa (1117 test), frontend (410 test), Ruff, lint, typecheck, build, controllo Guide e migrazioni SQLite/SQL Server verificati. Il workflow CI del commit di review ha riportato `failure` senza job falliti nei dettagli disponibili; una nuova esecuzione sul head aggiornato deve confermare l’esito complessivo. Resta il collaudo manuale degli organizzatori.
