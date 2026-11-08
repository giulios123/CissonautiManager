# MVP 22 · Altro importo da «Da incassare»

**Stato:** spec esecutiva per revisione. Dipende da MVP 18 e riusa registro, annullo e email differita di MVP 10.

## US-22.1 · Inserire un pagamento dalla lista

Come organizzatore voglio registrare rapidamente un importo diverso dal saldo completo senza aprire la scheda della prenotazione.

- Quando seleziono «Altro importo», allora si apre una modale con persona, causale, saldo totale, eventuale residuo per confermare, importo vuoto, canale attivo, data odierna Europe/Rome e nota facoltativa.
- Quando salvo un importo positivo valido, allora viene registrato un solo pagamento in centesimi, la riga mostra saldo e stato aggiornati e la modale si chiude.
- Quando l'importo è zero, negativo o non valido, allora viene mostrato un errore e non viene registrato alcun pagamento.
- Quando il pagamento copre la soglia di conferma ma non tutti gli extra, allora il posto risulta confermato e il saldo degli extra resta visibile nella lista.
- Quando il totale già versato supera l'importo dovuto, allora il credito è conservato e mostrato secondo le regole esistenti.

## US-22.2 · Gestire aggiornamenti e ritentativi

- Quando un altro admin modifica lo stato o gli importi mentre la modale è aperta, allora il salvataggio restituisce conflitto senza scritture; la modale mostra i dati aggiornati e richiede conferma esplicita mantenendo l'importo inserito.
- Quando la prenotazione non è più esigibile, allora la modale impedisce l'invio e offre i dati aggiornati.
- Quando il client ritenta lo stesso invio per una risposta di rete persa, allora il server restituisce lo stesso pagamento invece di registrarne un secondo o riavviare il periodo di annullo.
- Quando l'admin annulla entro dieci secondi, allora il pagamento resta nel registro come annullato, i saldi e lo stato sono ricalcolati e l'email differita non parte.
- Quando il pagamento conferma la prenotazione e non viene annullato, allora l'email parte dopo trenta secondi o dal successivo job orario, una sola volta.
- Quando annullo, chiudo con Escape o cambio lingua prima di salvare, allora nessun pagamento viene creato e il focus torna al comando che ha aperto la modale.
