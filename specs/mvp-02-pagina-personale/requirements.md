# MVP 2 · Pagina personale · Requisiti

Riferimento: `memory-bank/domain.md`. In caso di conflitto vince `domain.md`.

## US-1 · Email reali

Come partecipante voglio ricevere le email vere nella mia casella.

- Quando l'app gira con `EMAIL_PROVIDER=acs`, allora iscrizione, magic link, conferma pagamento, promemoria e conferma disdetta arrivano via Azure Communication Services dal mittente configurato.
- Quando l'invio fallisce, allora l'errore finisce nei log e l'operazione già salvata (iscrizione, pagamento, disdetta) non viene annullata.
- Quando `EMAIL_PROVIDER=console`, allora le email restano nei log come oggi.
- Quando `EMAIL_PROVIDER=acs` e manca `ACS_CONNECTION_STRING`, allora l'app non parte e il messaggio d'errore dice cosa manca.

## US-2 · Modifica degli slot

Come partecipante voglio cambiare i miei slot senza scrivere agli organizzatori.

- Quando apro `/io` con una prenotazione `in_attesa_pagamento` o `confermata`, allora vedo i giorni dell'edizione con i miei slot già selezionati e posso cambiarli.
- Quando aggiungo uno slot con posti liberi, allora viene aggiunto e l'importo dovuto è ricalcolato con la stessa regola dell'iscrizione.
- Quando aggiungo uno slot pieno, allora ricevo un errore che indica lo slot e la prenotazione non cambia.
- Quando tolgo uno slot, allora il posto si libera subito e l'importo dovuto è ricalcolato.
- Quando provo a salvare senza nessuno slot, allora vedo un errore: per rinunciare si usa la disdetta.
- Quando modifico gli slot, allora la scadenza del blocco non cambia.
- Quando la prenotazione è `confermata` e l'importo sale, allora resta `confermata` e il saldo mostra la differenza da versare.
- Quando la prenotazione è `confermata` e l'importo scende, allora resta `confermata` e il saldo mostra il credito.
- Quando lo stato è `scaduta`, `disdetta_richiesta` o `rimborsata`, allora la modifica è rifiutata.
- Prima di salvare vedo l'anteprima del nuovo importo e della differenza.
- Quando lo slot è nel passato (giorno già trascorso in Europe/Rome), allora il partecipante non può né aggiungerlo né toglierlo; solo l'admin può cambiarlo (MVP 3).

## US-3 · Saldo e istruzioni

- Quando apro `/io`, allora vedo importo dovuto, pagato, saldo (o credito se negativo), causale, canali di pagamento attivi con le istruzioni e la scadenza del blocco.
- Quando il saldo è positivo su una prenotazione `confermata` (dopo una modifica), allora vedo la differenza da versare con le stesse istruzioni.

## US-4 · Richiesta di disdetta

- Quando premo «Richiedi disdetta», allora compare una conferma esplicita che spiega che i posti si liberano subito e che il rimborso, se dovuto, lo gestiscono gli organizzatori.
- Quando confermo e la prenotazione ha pagamenti registrati, allora passa a `disdetta_richiesta`, i posti si liberano subito e parte un'email di conferma disdetta: il rimborso lo gestisce l'admin.
- Quando confermo e la prenotazione non ha pagamenti registrati, allora viene rimossa (nessun passaggio dall'admin), i posti si liberano subito e parte la stessa email di conferma. La persona resta registrata e può iscriversi di nuovo.
- Quando annullo la conferma, allora non cambia nulla.
- Quando lo stato non è `in_attesa_pagamento` o `confermata`, allora il pulsante non compare e l'API risponde con un errore.
- Quando ho disdetto (con o senza pagamenti) e mi iscrivo di nuovo con la stessa email, allora viene creata una nuova prenotazione (se c'è posto).

## US-5 · Promemoria di pagamento

- Quando un blocco `in_attesa_pagamento` raggiunge la metà del suo periodo, allora parte un promemoria, una sola volta.
- Quando mancano 24 ore alla scadenza, allora parte il secondo promemoria, una sola volta.
- Quando la prenotazione è `confermata`, `scaduta`, `disdetta_richiesta` o `rimborsata`, o i pagamenti coprono l'importo, allora non parte nessun promemoria.
- Quando il job gira in ritardo e sono dovuti entrambi, allora parte solo il secondo.
- Quando il blocco è più corto di 48 ore (le due soglie si sovrappongono), allora parte solo il promemoria a metà.
- Quando il job viene rilanciato, allora non rimanda promemoria già inviati.
- Quando una prenotazione scaduta viene riattivata da un pagamento (nuovo blocco), allora i promemoria ripartono da capo.
- Il job gira ogni ora, anche se l'app è spenta a riposo.

## US-6 · Accesso

- Quando il cookie di sessione (14 giorni) è valido, allora `/io` si apre senza nuovo login.
- Quando non lo è, allora vengo mandato a `/accedi` dove posso chiedere un nuovo link (già presente dall'MVP 1, qui solo verificato con email reali).

## Modifiche a domain.md

Proposte (approvate, da riportare in `domain.md` alla chiusura):

1. **Modifica slot**: modificando gli slot la scadenza del blocco non cambia.
2. **Confermata con importo che sale**: la prenotazione resta `confermata`; il saldo positivo è la differenza da versare e compare tra i pagamenti da verificare (MVP 3).
3. **Giorni passati**: gli slot di giorni già trascorsi (Europe/Rome) non si aggiungono né si tolgono.
4. **Promemoria**: se il blocco è più corto di 48 ore parte solo quello a metà.
5. **Disdetta senza pagamenti**: la prenotazione viene rimossa e i posti si liberano; con pagamenti passa a `disdetta_richiesta` come oggi.

Approvate dal maintainer il 2026-11-05: si applicano a `domain.md` in chiusura dell'MVP.
