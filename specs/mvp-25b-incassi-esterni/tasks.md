# MVP 25b · Task

- [x] **T25b-1** Funzioni pure per dovuto, versato, saldo e tetto della restituzione. Test: voce al fornitore, esterno non pagante, cambio da pagante a non pagante con credito.
- [x] **T25b-2** Modello e migrazione `0025_external_movements`; upgrade e downgrade su SQLite, indice parziale compatibile con SQL Server.
- [x] **T25b-3** API di pagamenti, restituzioni e annulli con idempotenza, eliminazione bloccata e cronologia. Test: doppio invio con la stessa chiave, restituzione oltre il credito (422), annullo con motivo, 403.
- [x] **T25b-4** Sezione «Esterni» in «Da incassare». Test: compaiono solo i paganti con saldo da versare, ricerca per nome.
- [x] **T25b-5** Report e CSV (movimenti e riepilogo). Test di riconciliazione: 6 € da un esterno aumentano il totale evento di 6 €, quote e `Payment` dei booking intatti, costi del fornitore fuori.
- [x] **T25b-6** Frontend: registro movimenti nel dettaglio, finestra in «Da incassare», report, i18n IT/EN. Test vitest.
- [x] **T25b-7** Guide IT/EN ed etichette inglesi dei CSV.
- [x] **T25b-8** Suite completa (backend 1251, frontend 430), Ruff, lint, TypeScript, build e migrazioni locali verdi; `pr-description.md` pronta. Restano CI SQL Server e collaudo organizzatori.

Scostamenti rispetto al design: «Da incassare» degli esterni ha un endpoint proprio, `GET /api/admin/guests/to-collect`, così la lista delle prenotazioni (`/api/admin/views/to-collect`) resta identica; la sezione sta in fondo alla stessa pagina. Il CSV dei movimenti è `GET /api/admin/guests/movements?format=csv`. Un pagamento su cui si appoggia una restituzione non si annulla finché la restituzione non è annullata (409). In «Da incassare» il saldo mostrato è il netto di versamenti e restituzioni.
