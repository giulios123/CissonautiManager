# Progress

## Stato degli MVP

| MVP | Nome | Stato |
|-----|------|-------|
| 0 | Bootstrap (Memory Bank, AGENTS.md, roadmap, spec MVP 1) | fatto |
| 1 | Iscrizione base | fatto salvo il task 15 (verifica in Google Sites e chiusura), aperto e non bloccante |
| 2 | Pagina personale | spec scritta (`specs/mvp-02-pagina-personale/`), in attesa di conferma |
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

## Bug corretti fuori MVP

- 2026-11-04: nel riepilogo e nelle email il pomeriggio compariva prima della mattina (ordinamento per nome del periodo). Corretto ordinando per orario di inizio, con test di regressione.
