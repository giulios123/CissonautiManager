# Profilo completo e iscritti precedenti

I nuovi invii raccolgono un profilo completo anche per chi entra solo in lista d'attesa. I dati annuali restano separati dai contatti riutilizzabili; il catalogo ISTAT e l'elenco paesi sono locali. Gli account già noti completano le risposte dopo login e l'admin può correggere il profilo anche senza una prenotazione.

La migrazione 0018 è additiva. Il completamento non modifica prenotazioni, slot, importi, scadenze, liste d'attesa o consensi. Una prenotazione confermata nell'edizione precedente determina la partecipazione; senza prova si conserva la dichiarazione esplicita.

## Verifiche automatiche

- 1091 test backend completi passati prima delle ultime verifiche profilo; 71 test backend mirati passati dopo le modifiche di validazione e altri 16 test profilo/migrazione dopo l'ultima correzione del catalogo.
- 399 test frontend completi passati prima dell'ultimo test del richiamo; 72 test mirati di registrazione, pagina personale e lingua inglese passati dopo gli ultimi cambi.
- Ruff, ESLint/Prettier, TypeScript, build e controllo guide passati. Rimangono un warning ESLint preesistente e l'avviso Vite per bundle >500 kB.
- Migrazione upgrade/downgrade SQLite verificata; SQL Server da verificare in CI.

## Collaudo per gli organizzatori

- [ ] Da telefono e desktop, iscrivi una persona scegliendo un comune e controlla provincia e regione.
- [ ] Prova un comune omonimo: scegli la provincia giusta dall'elenco.
- [ ] Prova un paese estero e una città italiana non presente, indicando la provincia senza regione automatica.
- [ ] Prova entrambi i profili social e le dichiarazioni «Non possiedo»; lascia anche un campo vuoto e verifica la validazione.
- [ ] Iscrivi una persona solo in lista d'attesa e controlla che vengano richiesti gli stessi dati.
- [ ] Ripeti l'invio con l'email di un account già noto: il profilo non deve cambiare. Accedi e completalo nella pagina personale.
- [ ] Cambia lingua e giorni durante il modulo e controlla che i dati restino. Prima/dopo confronta importi, stati, scadenze, slot, liste e consensi.
- [ ] Accedi come admin, correggi il profilo di una persona senza prenotazione e controlla la cronologia.
- [ ] Naviga la registrazione da tastiera e verifica l'iframe in Google Sites su cui è incorporato il modulo.

Nessun deploy, invio email reale o test su SQL Server è compreso in questa implementazione locale.
