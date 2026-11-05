# MVP 2 · Pagina personale

## Cosa c'è
Il partecipante, dalla sua pagina, cambia gli slot (con anteprima della nuova quota), vede saldo o credito e istruzioni di pagamento, e può disdire. Le email partono davvero (Azure Communication Services) e due promemoria di pagamento escono da soli, ognuno una volta sola.

## Da provare a mano (per gli organizzatori)

**Email vere** (dopo il deploy)
- [ ] Iscriviti con un tuo indirizzo: l'email arriva in pochi minuti e **non finisce nella posta indesiderata** (controlla anche lo spam).
- [ ] Il link dell'email apre la pagina personale in una finestra normale.
- [ ] Registra un pagamento che copre la quota dal pannello: arriva l'email di conferma.

**Cambio slot** (dalla pagina personale)
- [ ] Premi «Cambia i tuoi slot»: vedi i giorni con i tuoi slot già spuntati.
- [ ] Aggiungi un giorno: vedi «Nuova quota» e la differenza prima di salvare; dopo il salvataggio quota e saldo sono aggiornati.
- [ ] Togli un giorno: la quota scende e il posto si libera (controlla i posti liberi in `/iscrizione`).
- [ ] Togli tutti gli slot e salva: ti dice di usare la disdetta.
- [ ] Con uno slot pieno: non puoi aggiungerlo, ma puoi tenere il tuo.
- [ ] I giorni già passati non sono modificabili; oggi sì.
- [ ] La scadenza del blocco non cambia dopo la modifica.
- [ ] Su una prenotazione già pagata e confermata aggiungi un giorno: resta «Confermata» e compare la differenza da versare con le istruzioni.
- [ ] Su una prenotazione in attesa con un pagamento parziale togli un giorno fino a coprire il pagato: diventa «Confermata» e arriva l'email.

**Disdetta**
- [ ] «Richiedi disdetta» apre una finestra di conferma; «No, torno indietro» e il tasto Esc la chiudono senza cambiare nulla.
- [ ] Senza pagamenti: confermando, l'iscrizione sparisce, i posti sono liberi, arriva l'email e puoi iscriverti di nuovo con la stessa email.
- [ ] Con un pagamento registrato: lo stato diventa «Disdetta richiesta», i posti sono liberi, la finestra ha avvertito che ti scriveranno per il rimborso e l'email lo ripete.
- [ ] Dalla tastiera: apri la finestra, Tab resta dentro la finestra, il focus torna sul pulsante alla chiusura.

**Promemoria**
- [ ] Con 3 giorni di blocco, a 36 ore dall'iscrizione arriva il primo promemoria e a 24 ore dalla scadenza il secondo (per provare prima, imposta 1 giorno di blocco: il promemoria a metà arriva dopo 12 ore e non ne arriva un secondo).
- [ ] Il promemoria indica quanto resta da versare, la causale, la scadenza e come pagare.
- [ ] Non arriva nessun promemoria a chi ha già pagato o ha disdetto.
- [ ] Dal portale Azure, nella risorsa del job `<app>-reminders`, la cronologia mostra un'esecuzione all'ora.

## Note per chi fa la revisione
- La migrazione 0003 aggiunge colonne a `booking`; `hold_started_at` si riempie da `created_at`.
- L'infrastruttura (task 9) non è stata validata contro Azure: `az bicep build` e `what-if` prima del deploy.
- Decisioni D-014 a D-019 in `memory-bank/decisions.md`; modifiche a `domain.md` già approvate.
