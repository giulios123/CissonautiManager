# MVP 25c · Task

- [x] **T25c-1** Funzioni pure: importi con esenzioni, pasto compreso che salta le voci esentate, versato netto, tetto del rimborso attivo e della disdetta. Test parametrizzati.
- [x] **T25c-2** Modelli e migrazione `0026_exemptions_refunds` (categoria, flag, `booking_refund`, token di anteprima); upgrade e downgrade su SQLite, vincoli compatibili con SQL Server.
- [x] **T25c-3** Integrazione nel calcolo unico, in `paid_total`, nel tetto della disdetta e nelle impronte MVP 18/23. Regressione sull'intera suite.
- [x] **T25c-4** Anteprima e applicazione delle esenzioni con lock, conflitto, idempotenza, notifica di conferma e cronologia. Test: in attesa che si conferma, confermata che resta tale, nessun pagamento cambiato, 403.
- [x] **T25c-5** Rimborso su prenotazione attiva e suo annullo. Test: stato invariato, oltre il credito (422), doppio invio, annullo di un pagamento dopo un rimborso.
- [x] **T25c-6** Pagina personale e API `me` con voci esenti e rimborsi, senza la categoria. Test backend e frontend.
- [x] **T25c-7** Interfaccia admin: pannello, rimborso, elenco e CSV Persone, report, i18n IT/EN.
- [x] **T25c-8** Guide IT/EN, admin e partecipante.
- [x] **T25c-9** Suite completa (backend 1322, frontend 447), Ruff, lint, TypeScript, build e migrazioni locali verdi; `pr-description.md` e `test-manuali.md` pronti. Restano CI SQL Server e collaudo organizzatori.

Scostamenti rispetto al design: gli endpoint stanno in `api/admin_exemptions.py` (`PUT /{id}/category`, `POST /{id}/exemptions/preview|apply`, `POST /{id}/refunds` e `/{id}/refunds/{rid}/void`); la sola categoria si salva senza anteprima; le voci con pagamento diretto al fornitore non si offrono per l'esenzione nell'interfaccia. Il «pagato» usato ovunque (`paid_total`, vista partecipante, email) è il **netto** dei rimborsi; nel report `paid_cents` resta lordo e il netto/crediti sottraggono i rimborsi (riga «di cui su iscrizioni attive»). Annullare un pagamento su cui si appoggia un rimborso è bloccato (409). Il CSV Persone ha le colonne «Categoria» e «Quota esente» in fondo.
