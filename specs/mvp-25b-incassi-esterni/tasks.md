# MVP 25b · Task

- [ ] **T25b-1** Funzioni pure per dovuto, versato, saldo e tetto della restituzione. Test: voce al fornitore, esterno non pagante, cambio da pagante a non pagante con credito.
- [ ] **T25b-2** Modello e migrazione `0025_external_movements`; upgrade e downgrade su SQLite, indice parziale compatibile con SQL Server.
- [ ] **T25b-3** API di pagamenti, restituzioni e annulli con idempotenza, eliminazione bloccata e cronologia. Test: doppio invio con la stessa chiave, restituzione oltre il credito (422), annullo con motivo, 403.
- [ ] **T25b-4** Sezione «Esterni» in «Da incassare». Test: compaiono solo i paganti con saldo da versare, ricerca per nome.
- [ ] **T25b-5** Report e CSV (movimenti e riepilogo). Test di riconciliazione: 6 € da un esterno aumentano il totale evento di 6 €, quote e `Payment` dei booking intatti, costi del fornitore fuori.
- [ ] **T25b-6** Frontend: registro movimenti nel dettaglio, finestra in «Da incassare», report, i18n IT/EN. Test vitest.
- [ ] **T25b-7** Guide IT/EN ed etichette inglesi dei CSV.
- [ ] **T25b-8** Suite completa, lint, migrazioni da zero, prove manuali, descrizione PR.
