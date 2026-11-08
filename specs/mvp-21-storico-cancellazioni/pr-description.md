# MVP 21 · Checklist per la revisione

## Verifiche automatiche

- [ ] CI backend SQLite verde.
- [x] CI backend SQL Server verde, incluse migrazioni da zero e dalla revisione precedente (confermato dal maintainer).
- [x] Ruff, formattazione, ESLint/Prettier, TypeScript, test frontend, build e controllo Guide IT/EN verdi.
- [ ] Nessun deploy o esito manuale dichiarato sulla sola base della CI.

## Collaudo per gli organizzatori

- [x] Collaudo manuale A6 completato dal maintainer.
- [x] Conservazione scelta dal maintainer: un anno dalla cancellazione, applicato dal job orario.
- [ ] Dopo il deploy, verificare che la vista sia disponibile solo agli admin e che le nuove disdette siano trovabili dopo la rimozione.
