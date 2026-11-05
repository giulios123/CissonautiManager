# MVP 4 · Lista d'attesa · Requisiti

Riferimento: `memory-bank/domain.md`. In caso di conflitto vince `domain.md`. Dipende dagli MVP 1-3 (posti, blocco, cambio slot, disdetta, pannello admin).

Scelte del maintainer (2026-11-05): ci si mette in lista anche dal modulo pubblico, anche senza nessuno slot libero; una prenotazione `confermata` che riceve uno slot dalla lista resta `confermata`, con il saldo che mostra la differenza.

## US-1 · Lista d'attesa dal modulo pubblico

Come persona che trova pieni uno o più slot voglio mettermi in lista, così non perdo il posto se si libera.

- Quando uno slot è pieno e la sua lista non ha raggiunto il limite, allora nel modulo lo vedo come «pieno, puoi metterti in lista» e posso spuntarlo.
- Quando la lista di uno slot pieno ha raggiunto il limite, allora lo slot non si può spuntare e il modulo lo dice («pieno, lista completa»).
- Quando invio il modulo con slot liberi e slot in lista, allora ottengo la prenotazione per gli slot liberi (come oggi, con importo, istruzioni e scadenza) e resto in lista per gli altri; il riepilogo e l'email elencano entrambi.
- Quando invio il modulo con soli slot in lista, allora vengo registrato senza prenotazione: il riepilogo dice che sono in lista, per quali slot e in che posizione, che non devo pagare nulla finché non si libera un posto, e ricevo l'email con il magic link.
- Quando invio il modulo, allora i testi legali accettati (versione, data e ora) sono salvati anche per chi resta solo in lista.
- Quando nel frattempo uno slot spuntato «in lista» si è liberato o la lista si è riempita, allora il modulo me lo segnala e non salva nulla (come oggi con gli slot pieni).
- Quando l'email ha già un'iscrizione attiva, allora vale D-005 (magic link, nessuna modifica): la lista si gestisce dalla pagina personale.

## US-2 · Lista d'attesa dalla pagina personale

- Quando apro la pagina personale, allora vedo gli slot in cui sono in lista con la mia posizione («2° in lista»).
- Quando uno slot che non ho è pieno e la lista ha spazio, allora posso mettermi in lista; se la lista è completa, non posso.
- Quando esco dalla lista di uno slot, allora la mia voce sparisce e chi era dopo di me sale di una posizione.
- Quando ho solo voci in lista e nessuna prenotazione, allora la pagina personale mi mostra la lista e mi dice che non c'è nulla da pagare.
- Quando lo slot è di un giorno già passato (Europe/Rome), allora non posso entrare in lista.
- Quando lo slot è la sera (senza limite), allora non esiste lista: lo prenoto e basta.

## US-3 · Limite della lista

- Quando lo slot ha capienza C e la percentuale è P, allora la lista accoglie al massimo C × P / 100 persone, arrotondato per difetto (25 posti al 20% fanno 5).
- Quando il limite calcolato è zero, allora la lista per quello slot non è disponibile.
- Quando l'admin cambia la percentuale, allora il nuovo limite vale per le iscrizioni successive; chi è già in lista resta.

## US-4 · Promozione del primo in lista

- Quando si libera un posto in uno slot con persone in lista, allora il primo in lista (per ordine di arrivo) riceve lo slot e un'email «si è liberato un posto».
- Quando il promosso ha una prenotazione `in_attesa_pagamento`, allora lo slot si aggiunge, l'importo si ricalcola e la scadenza del blocco diventa la più lontana tra quella attuale e N giorni da ora; i promemoria si ricalcolano come dopo una proroga (D-024).
- Quando il promosso ha una prenotazione `confermata`, allora lo slot si aggiunge, l'importo si ricalcola e la prenotazione resta `confermata`; il saldo mostra la differenza da versare e la prenotazione compare in «Da verificare» (saldo positivo).
- Quando il promosso non ha una prenotazione attiva, allora ne nasce una nuova `in_attesa_pagamento` con quel solo slot, blocco di N giorni e i testi legali accettati quando è entrato in lista; l'email contiene importo, istruzioni, scadenza e magic link.
- Quando si liberano più posti nello stesso slot, allora vengono promosse altrettante persone, in ordine.
- Quando il promosso è in lista per altri slot, allora resta in lista per quelli.
- Quando lo slot è di un giorno già passato, allora nessuno viene promosso.

## US-5 · Quando si libera un posto

Un posto si libera, e parte la promozione, quando:

- un partecipante o un admin disdice una prenotazione;
- un partecipante o un admin toglie lo slot da una prenotazione;
- una prenotazione scade: la promozione parte al più entro un'ora, con il job orario che già invia i promemoria;
- l'admin aumenta la capienza dalle Impostazioni.

- Quando due posti si liberano nello stesso istante in modo concorrente, allora lo stesso slot non viene assegnato a più persone di quanti sono i posti.

## US-6 · Uscita automatica dalla lista

- Quando una persona prenota lo slot per cui era in lista (perché si è liberato e lo prende da sé, o glielo aggiunge l'admin), allora la sua voce in lista si chiude.
- Quando una persona disdice la sua prenotazione, allora si chiudono anche le sue voci in lista, e l'email di conferma della disdetta lo dice.
- Quando una persona solo in lista vuole uscire da tutto, allora esce dalla lista slot per slot dalla pagina personale.

## US-7 · Pannello admin

- Quando apro «Giorni e slot», allora per ogni slot pieno vedo anche la lista d'attesa in ordine, con nomi e data di ingresso; il CSV della vista ha una riga per ogni persona in lista con la posizione.
- Quando rimuovo una persona dalla lista, allora la voce si chiude, la cronologia lo registra e non parte nessuna email.
- Quando apro la scheda di una persona, allora vedo le sue voci in lista; se non ha prenotazione, la persona compare comunque in «Persone» con lo stato «in lista».
- Quando aggiungo uno slot a mano con «forza oltre la capienza», allora non cambia nulla per la lista.

## US-8 · Impostazioni

- Quando apro le Impostazioni, allora trovo la percentuale della lista d'attesa (default 20, tra 0 e 100).

## Modifiche a domain.md

Proposte, da approvare prima di applicarle alla chiusura dell'MVP:

1. **Ingresso in lista**: anche dal modulo pubblico, anche senza nessuno slot libero; chi è solo in lista è registrato senza prenotazione, con i testi legali accettati salvati.
2. **Limite**: capienza × percentuale, arrotondato per difetto.
3. **Promozione su `confermata`**: lo slot si aggiunge e la prenotazione resta confermata, con la differenza nel saldo, senza blocco (come D-017).
4. **Promozione su `in_attesa_pagamento`**: la scadenza diventa la più lontana tra quella attuale e N giorni da ora.
5. **Scadenze e lista**: la scadenza resta valutata alla lettura; il passaggio del posto al primo in lista dopo una scadenza avviene con il job orario, quindi entro un'ora.
6. **Disdetta**: chiude anche le voci in lista della persona.

## Fuori scope (Backlog)

- Priorità in lista a chi porta un +1 (MVP 7).
- Lista d'attesa per le attività (MVP 6 non la prevede).
- Avviso a chi è in lista quando la sua posizione cambia.
