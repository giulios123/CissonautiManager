# MVP 17 · Consensi facoltativi e riservatezza

La registrazione raccoglie i consensi facoltativi separatamente dai consensi già obbligatori. I testi legali sono versionati per edizione e disponibili in italiano e inglese; gli account esistenti non cambiano le proprie scelte per effetto di una richiesta anonima. La persona può gestire le proprie scelte da una vista autenticata, mentre l'admin le consulta in sola lettura.

La migrazione 0016 aggiunge documenti legali bilingui ed eventi di consenso indipendenti dalla prenotazione. Il flusso d'iscrizione registra le scelte nella stessa transazione e supporta anche chi entra soltanto in lista d'attesa. Le informative effettive da pubblicare in produzione restano da validare.

## Verifiche

- Test mirati: 104 backend/25 frontend per testi e pubblicazione; 62 backend/21 frontend per iscrizione; 50 backend per gestione autenticata; 2 test dedicati e 19 frontend per il modulo.
- Il maintainer conferma superate tutte le prove SQL.
- CI della PR e procedure manuali in [`test-manuali.md`](test-manuali.md) ancora da eseguire; nessun deploy o invio reale è stato fatto.

## Prove manuali per gli organizzatori

Da fare su un'edizione di prova, usando testi legali fittizi espliciti e mai pubblicandoli in produzione:

- [ ] Cambiare lingua IT/EN nel modulo e controllare che le finalità mostrino testi equivalenti e la stessa versione.
- [ ] Completare una nuova iscrizione con consensi diversi; verificare che le scelte siano visibili solo dopo l'accesso e non cambino inserendo l'email dal modulo anonimo.
- [ ] Ripetere con una persona già registrata e con una che entra solo in lista d'attesa.
- [ ] Revocare un consenso dalla pagina personale; verificare aggiornamento della scelta e storico, anche dopo aver rimosso una prenotazione di prova.
- [ ] In admin, verificare la lettura delle scelte senza controlli che permettano di modificarle al posto della persona.
- [ ] Usare il modulo da telefono, desktop e iframe e controllare tastiera, cambio lingua e messaggi di errore.
