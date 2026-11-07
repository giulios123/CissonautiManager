# MVP 18 · Conferma con la sola quota

Quando l'admin abilita la nuova regola per un'edizione, il posto viene confermato appena i pagamenti coprono la quota di partecipazione (quota base più giorni scelti). Pasti e attività dell'organizzazione restano nel saldo complessivo ma non bloccano la conferma; le spese pagate direttamente al fornitore non entrano negli incassi. Le edizioni mantengono il comportamento attuale finché un admin non rivede l'anteprima e applica la regola.

La modifica introduce la quota salvata e i metadati dei cicli di notifica, aggiorna conferme, annulli, ricalcoli, lista d'attesa, promemoria, report e CSV, e aggiunge l'anteprima/application admin protetta da token e lock. Pagine, email e guide distinguono quota richiesta, totale organizzazione e saldo residuo; i modelli email personalizzati sono indicati in anteprima affinché l'admin li riveda. Quota zero non genera un pagamento fittizio. Distribuzione e attivazione reale restano operazioni separate.

## Verifiche

- Backend: 1083 test; Ruff e controllo formattazione passati.
- Frontend: 394 test; TypeScript, lint e build passati.
- SQLite: migrazioni da zero e legacy, casi di attivazione con dati sintetici coperti dalla suite.
- SQL: tutte le prove SQL confermate superate dal maintainer.
- Le procedure manuali in [`test-manuali.md`](test-manuali.md) non sono state eseguite; non sono stati effettuati deploy, invii email reali o applicazioni della policy ai dati correnti.

## Prove manuali per gli organizzatori

Da eseguire su un'edizione di prova dopo il rilascio:

- [ ] In Impostazioni, aprire l'anteprima e controllare per alcune persone quota, totale, versato e saldo prima/dopo. Annullare e verificare che la regola corrente resti attiva.
- [ ] Cambiare un prezzo o registrare un pagamento dopo l'anteprima: l'applicazione del vecchio risultato deve chiedere una nuova anteprima.
- [ ] Su un'iscrizione con extra, coprire la quota ma lasciare del saldo: il posto deve risultare confermato e gli extra restare visibili in «Da incassare»; non deve comparire un pagamento fittizio.
- [ ] Controllare le email in italiano e inglese: importo appena registrato, quota, totale e saldo devono essere distinti; una conferma senza pagamento non deve sembrare una ricevuta.
- [ ] Annullare un versamento in modo che la quota non sia più coperta: l'iscrizione deve tornare in attesa con il nuovo termine di blocco.
- [ ] Confrontare pagina personale, scheda admin, report e CSV; una voce pagata direttamente al fornitore non deve aumentare gli incassi dell'organizzazione.
