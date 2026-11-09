# MVP 25c · Task

- [ ] **T25c-1** Funzioni pure: importi con esenzioni, pasto compreso che salta le voci esentate, versato netto, tetto del rimborso attivo e della disdetta. Test parametrizzati.
- [ ] **T25c-2** Modelli e migrazione `0026_exemptions_refunds` (categoria, flag, `booking_refund`, token di anteprima); upgrade e downgrade su SQLite, vincoli compatibili con SQL Server.
- [ ] **T25c-3** Integrazione nel calcolo unico, in `paid_total`, nel tetto della disdetta e nelle impronte MVP 18/23. Regressione sull'intera suite.
- [ ] **T25c-4** Anteprima e applicazione delle esenzioni con lock, conflitto, idempotenza, notifica di conferma e cronologia. Test: in attesa che si conferma, confermata che resta tale, nessun pagamento cambiato, 403.
- [ ] **T25c-5** Rimborso su prenotazione attiva e suo annullo. Test: stato invariato, oltre il credito (422), doppio invio, annullo di un pagamento dopo un rimborso.
- [ ] **T25c-6** Pagina personale e API `me` con voci esenti e rimborsi, senza la categoria. Test backend e frontend.
- [ ] **T25c-7** Interfaccia admin: pannello, rimborso, elenco e CSV Persone, report, i18n IT/EN.
- [ ] **T25c-8** Guide IT/EN, admin e partecipante.
- [ ] **T25c-9** Suite completa, lint, migrazioni da zero (SQLite e SQL Server in CI), prove manuali, descrizione PR.
