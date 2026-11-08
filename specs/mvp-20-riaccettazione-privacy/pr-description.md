# MVP 20 · Nuova accettazione privacy

Per una persona associata a un'edizione, una nuova versione dell'informativa richiede una scelta esplicita dopo l'accesso. Finché resta in sospeso, l'API impedisce di cambiare presenze, pasti, attività, proposte o di entrare in una lista d'attesa; lettura, pagamenti, revoche dei consensi, dati alimentari, uscita dalla lista e disdetta restano disponibili. Le prenotazioni e le adesioni precedenti non vengono modificate.

La migrazione `0019`, dopo la migrazione profilo `0018` già presente in `main`, conserva lo storico privacy disponibile, segnando la lingua delle vecchie prove come sconosciuta. La richiesta email passa dal job orario esistente e parte una sola volta per persona, edizione e versione privacy. Una prova inviata da un account già noto nel modulo anonimo non vale come nuova accettazione.

## Verifiche automatiche

- Test backend mirati in SQLite su privacy, registrazione, consensi e migrazioni; suite frontend completa (401 test) e 3 test privacy mirati sulla versione finale; Ruff, ESLint/Prettier, TypeScript, build Vite e controllo guide IT/EN.
- La suite backend completa è stata interrotta al 19% dopo circa dieci minuti per la lentezza del runner locale.
- La migrazione `0019` viene provata con dati legacy duplicati e con lingua non ricostruibile; la sequenza `0018`/`0019` viene verificata dalla CI.
- Le prove SQL Server e quelle visive in ambiente reale restano da eseguire.

## Checklist per gli organizzatori

- [ ] In un'edizione di prova, pubblicare una nuova informativa con testi IT/EN e controllare che la versione precedente resti nello storico.
- [ ] Accedere con un account che ha già una prenotazione: la pagina personale mostra il testo nella lingua scelta e la casella parte vuota.
- [ ] Con l'accettazione ancora pendente, verificare che si possa leggere la pagina, registrare un pagamento, modificare i dati alimentari, revocare consensi, lasciare la lista d'attesa o disdire; verificare che non si possano cambiare presenze, pasti, attività, proposte o aggiungere una lista.
- [ ] Accettare la versione corrente e verificare che le modifiche tornino disponibili senza una nuova iscrizione.
- [ ] Con un account già esistente, provare la reiscrizione dal modulo pubblico: la nuova versione resta pendente fino all'accesso autenticato.
- [ ] Dalla scheda organizzatori, controllare versione corrente, versione accettata, stato e storico, inclusa la lingua non disponibile per le prove legacy.
- [ ] In ambiente di prova con email in console, eseguire il job con una prenotazione attiva e una lista aperta pendenti; rieseguirlo e controllare che non parta una seconda richiesta. Verificare che le persone senza associazioni attive o già aggiornate non ricevano il messaggio.
- [ ] Ripetere il flusso da telefono e da desktop, in italiano e in inglese.

## Prima dell'uso reale

- [ ] Applicare la migrazione su SQL Server tramite CI o database di prova.
- [ ] Far validare agli organizzatori il testo legale definitivo in italiano e inglese.
- [ ] Verificare recapito e collegamento al login nei client email usati dall'organizzazione.

Nessuna email reale, pubblicazione legale reale, attivazione sui dati correnti o deploy è stata eseguita in questa implementazione.
