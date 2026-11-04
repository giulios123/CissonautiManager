# Progress

## Stato degli MVP

| MVP | Nome | Stato |
|-----|------|-------|
| 0 | Bootstrap (Memory Bank, AGENTS.md, roadmap, spec MVP 1) | fatto |
| 1 | Iscrizione base | in corso: 1a fatta (task 1-12), slot serale da fare (task 13), 1b da fare (task 14-15, deploy Azure) |
| 2 | Pagina personale | da fare |
| 3 | Pannello admin completo | da fare |
| 4 | Lista d'attesa | da fare |
| 5 | Pranzi e cene | da fare |
| 6 | Attività e contributi | da fare |
| 7 | Inviti e report | da fare |

## Verifiche manuali

- **Bootstrap**: struttura del repo conforme alla Parte A; nessun codice applicativo. Nessuna verifica manuale funzionale prevista.

- **MVP 1a**, provato end to end in locale con browser (DB nuovo da migrazioni): login admin con password, creazione edizione e testi legali, iscrizione da telefono (10 € + 2 giorni = 12 €), magic link dall'email in console, pagina personale, registrazione pagamento con conferma, cookie httpOnly/Lax di 14 giorni, header CSP.
- **Non verificato**: test su SQL Server (nessun Docker in sessione, li esegue la CI al primo push), build dell'immagine Docker, embed reale in Google Sites, email reali.

## Bug corretti fuori MVP

- 2026-11-04: nel riepilogo e nelle email il pomeriggio compariva prima della mattina (ordinamento per nome del periodo). Corretto ordinando per orario di inizio, con test di regressione.
