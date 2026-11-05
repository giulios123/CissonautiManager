# Progress

## Stato degli MVP

| MVP | Nome | Stato |
|-----|------|-------|
| 0 | Bootstrap (Memory Bank, AGENTS.md, roadmap, spec MVP 1) | fatto |
| 1 | Iscrizione base | fatto salvo il task 15 (verifica in Google Sites e chiusura), aperto e non bloccante |
| 2 | Pagina personale | codice fatto e provato in locale (task 1-8), infrastruttura Azure scritta ma non validata (task 9), chiusura documentale fatta (task 10) |
| 3 | Pannello admin completo | spec scritta (`specs/mvp-03-pannello-admin/`), in attesa di conferma |
| 4 | Lista d'attesa | da fare |
| 5 | Pranzi e cene | da fare |
| 6 | Attività e contributi | da fare |
| 7 | Inviti e report | da fare |

## Verifiche manuali

- **Bootstrap**: struttura del repo conforme alla Parte A; nessun codice applicativo. Nessuna verifica manuale funzionale prevista.

- **MVP 1a**, provato end to end in locale con browser (DB nuovo da migrazioni): login admin con password, creazione edizione e testi legali, iscrizione da telefono (10 € + 2 giorni = 12 €), magic link dall'email in console, pagina personale, registrazione pagamento con conferma, cookie httpOnly/Lax di 14 giorni, header CSP.
- **Slot serale (task 13)**: provato in browser su DB nuovo da migrazioni 0001 e 0002; la sera si prenota senza limite di posti e la sola sera costa 11 €.
- **CI su SQL Server**: ha trovato 4 problemi che SQLite nascondeva (D-011), tutti corretti. Immagine Docker: costruita dalla CI.
- **Deploy Azure (task 14)**: chiuso con successo dal maintainer, l'app parte su Container Apps e il login funziona.
- **Non verificato**: embed reale in Google Sites (task 15), email reali (MVP 2).

- **MVP 2**, provato end to end in locale con browser da telefono (DB nuovo da migrazioni, edizione 3-9 novembre con email in console): iscrizione dal modulo pubblico, magic link, cambio slot con anteprima della quota (12 € a 13 €), giorni passati bloccati e oggi modificabile, selezione vuota rifiutata, dialogo di disdetta (focus sul tasto sicuro, Esc lo chiude e riporta il focus), disdetta senza pagamenti con email e prenotazione rimossa. Il job `python -m app.jobs.send_reminders` parte da riga di comando su un database migrato.
- **Non verificato (MVP 2)**: `az bicep build`, `what-if` e primo deploy con ACS e job (task 9); email vere nella casella e fuori dalla posta indesiderata; il job che gira davvero ogni ora con l'app a zero repliche; disdetta con pagamenti provata solo nei test automatici.

## Bug corretti fuori MVP

- 2026-11-04: nel riepilogo e nelle email il pomeriggio compariva prima della mattina (ordinamento per nome del periodo). Corretto ordinando per orario di inizio, con test di regressione.
