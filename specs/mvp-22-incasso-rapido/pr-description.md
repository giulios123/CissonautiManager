# MVP 22 · Checklist per la revisione

## Verifiche automatiche

- [ ] CI backend SQLite verde.
- [ ] CI backend SQL Server verde, incluse migrazioni da zero e dalla revisione precedente.
- [ ] Test frontend, lint, TypeScript, build e controllo Guide IT/EN verdi.
- [ ] Verificare che i pagamenti dalla scheda e dal tasto rapido esistente mantengano il comportamento corrente.

## Collaudo per gli organizzatori

- [ ] Completare `test-manuali.md` con un'edizione di prova e email in console.
- [ ] Verificare pagamento parziale, conferma quota con extra residui, annullo e ripetizione di invio.
- [ ] Dopo il deploy, controllare la finestra di annullo, il job orario e la ricezione di una sola email.
