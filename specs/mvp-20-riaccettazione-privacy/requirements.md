# MVP 20 · Nuova accettazione privacy

**Stato:** implementato localmente; suite backend completa, convalida SQL Server e prove manuali ancora da svolgere. Basato sul registro A5, D-055 e risposta D-081; usa il registro prove introdotto nel 17. Il 19 resta indipendente.

## US-20.1 · Rileggere e accettare la versione corrente

Come partecipante associato all'edizione voglio leggere l'informativa pubblicata e confermare esplicitamente la versione corrente.

- Quando viene pubblicata una nuova versione, allora al successivo accesso la mia pagina personale mostra il testo nella lingua scelta e una casella non preselezionata.
- Quando accetto dopo autenticazione, allora si aggiunge una prova con persona, edizione, documento, lingua e data UTC; le prove precedenti restano consultabili.
- Quando la versione inviata non è più corrente, allora il server non registra la scelta e la pagina ricarica il testo aggiornato.
- Quando la reiscrizione di un account esistente avviene dal modulo pubblico, allora l'accettazione resta in sospeso fino alla conferma autenticata.

## US-20.2 · Continuare a consultare e disdire

- Quando manca la nuova accettazione, allora sono disponibili consultazione e pagamenti già previsti, consensi e revoche, dati alimentari, uscita dalla lista d'attesa, password, lingua e disdetta.
- Quando manca la nuova accettazione, allora le API non consentono di modificare presenze, iscriversi a una lista d'attesa, pasti, attività o proposte.
- Quando le operazioni vengono eseguite dagli organizzatori, allora le autorizzazioni admin restano valide; nessun admin può registrare l'accettazione per conto del partecipante.

## US-20.3 · Ricevere una richiesta email

- Quando la privacy corrente è pendente per una prenotazione attiva o per una lista aperta dell'edizione attiva, allora il job orario invia una richiesta nella lingua salvata con un link al login.
- Quando la persona ha già accettato, non ha più un'associazione attiva, oppure la versione non è più corrente, allora non viene inviata una richiesta per quella versione.
- Quando un tentativo email è già stato registrato, allora riesecuzioni e job concorrenti non lo ripetono.

## Modifiche approvate e applicate a `domain.md`

La privacy accettata per la registrazione vale per lo specifico documento e la specifica edizione. La pubblicazione di una nuova versione richiede una nuova scelta autenticata. Fino ad allora si limitano le modifiche alle presenze e alle adesioni, mantenendo disponibili lettura, pagamenti, consensi, rimozione dalla lista e disdetta. L'invio della richiesta è un solo tentativo per persona, edizione e versione.
