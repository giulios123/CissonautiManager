# MVP 21 · Checklist per la revisione

## Verifiche automatiche

- [ ] CI backend SQLite verde.
- [ ] CI backend SQL Server verde, incluse migrazioni da zero e dalla revisione precedente.
- [ ] Ruff, formattazione, ESLint/Prettier, TypeScript, test frontend, build e controllo Guide IT/EN verdi.
- [ ] Nessun deploy o esito manuale dichiarato sulla sola base della CI.

## Collaudo per gli organizzatori

- [ ] Completare `test-manuali.md` con dati di prova e registrare gli esiti.
- [ ] Prima del merge su `main`, definire e registrare il criterio di conservazione da applicare al registro.
- [ ] Dopo il deploy, verificare che la vista sia disponibile solo agli admin e che le nuove disdette siano trovabili dopo la rimozione.
