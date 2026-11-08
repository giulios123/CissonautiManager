# MVP 22 · Checklist per la revisione

## Verifiche automatiche

- [ ] CI backend SQLite verde.
- [x] CI backend SQL Server verde, incluse migrazioni da zero e dalla revisione precedente (confermato dal maintainer).
- [x] Test frontend, lint, TypeScript, build e controllo Guide IT/EN verdi.
- [ ] Verificare che i pagamenti dalla scheda e dal tasto rapido esistente mantengano il comportamento corrente.

## Collaudo per gli organizzatori

- [x] Collaudo manuale completato dal maintainer.
- [ ] Verificare pagamento parziale, conferma quota con extra residui, annullo e ripetizione di invio.
- [ ] Dopo il deploy, controllare la finestra di annullo, il job orario e la ricezione di una sola email.
