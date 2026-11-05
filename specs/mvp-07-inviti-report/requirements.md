# MVP 7 · Inviti e report · Requisiti

Riferimento: `memory-bank/domain.md`. In caso di conflitto vince `domain.md`. Dipende dagli MVP 4 (lista d'attesa), 5 (pasti) e 6 (attività), ancora in lavorazione: le ipotesi su di loro sono in `design.md`, sezione «Ipotesi sugli MVP 4-6».

Decisione del maintainer (2026-11-05): la priorità va a **chi è stato invitato** (il +1), non a chi invita. Il legame resta il campo testuale «chi ti ha invitato?» (D-008); l'admin lo conferma con una spunta. Nessun posto riservato.

## US-1 · Segnare un +1 verificato

Come admin voglio confermare che una persona è davvero l'invitato di un partecipante, così la sua priorità in lista d'attesa è affidabile.

- Quando apro la scheda di una persona che ha compilato «chi ti ha invitato?», allora vedo il testo e la spunta «+1 verificato».
- Quando spunto «+1 verificato», allora la scheda mostra chi l'ha verificato e quando (ora di Roma).
- Quando tolgo la spunta, allora la persona torna senza priorità.
- Quando «chi ti ha invitato?» è vuoto, allora la spunta non è disponibile e l'API rifiuta la verifica.
- Ogni verifica e ogni rimozione compare nella cronologia della scheda (chi, quando, cosa).
- Quando un partecipante prova a chiamare l'azione, allora riceve 403.

## US-2 · Priorità in lista d'attesa

Come +1 verificato voglio passare davanti in lista d'attesa, così chi è stato invitato da un partecipante trova posto prima.

- Quando si libera un posto in uno slot, allora viene promosso il primo +1 verificato in lista per quello slot; se non ce ne sono, il primo in ordine di ingresso.
- Quando ci sono più +1 verificati, allora tra loro vale l'ordine di ingresso in lista.
- Quando l'admin verifica un +1 già in lista, allora la priorità vale dalla promozione successiva, senza che la persona debba rientrare.
- Quando l'admin toglie la verifica, allora la persona torna al suo posto in ordine di ingresso.
- Il limite di dimensione della lista (20% della capienza, configurabile) non cambia: la priorità cambia l'ordine, non quante persone entrano in lista.
- Quando la lista è piena, allora anche un +1 verificato non può entrare (confermato dal maintainer il 2026-11-05).
- La promozione segue le regole dell'MVP 4 (email e blocco di N giorni): cambia solo chi viene scelto.

## US-3 · Lista d'attesa con la priorità visibile

- Quando apro la vista della lista d'attesa, allora per ogni slot vedo le persone nell'ordine effettivo di promozione, con la posizione e un'etichetta «+1» per i verificati.
- Quando una persona ha compilato «chi ti ha invitato?» ma non è verificata, allora vedo il testo e un'indicazione «da verificare», così so chi controllare.
- Quando premo «Scarica CSV», allora ottengo le stesse righe con posizione, +1 verificato e «invitato da».

## US-4 · Report di riepilogo dell'edizione

Come organizzatore voglio, a fine edizione, i numeri in una pagina sola, da guardare, stampare o scaricare.

- Quando apro «Report», allora vedo le sezioni: Iscrizioni, Presenze, Pasti, Attività, Lista d'attesa, Incassi.
- **Iscrizioni**: quando apro la sezione, allora vedo il numero di prenotazioni per stato e il numero di persone distinte iscritte.
- Quando una sezione conta presenze, pasti o attività, allora mostra due colonne, «confermate» e «in attesa di pagamento», più il totale (confermato dal maintainer il 2026-11-05).
- **Presenze**: per ogni giorno e slot il numero di presenti (sera derivata D-009 inclusa e indicata); il picco di presenti contemporanei, la media per slot di giorno e i giorni-persona totali.
- **Pasti**: pranzi e cene per giorno e i totali; il numero di persone con esigenze alimentari per pasto, senza nomi né dettagli (dati sanitari).
- **Attività**: per ogni attività aderenti, capienza (se c'è) e incasso.
- **Lista d'attesa**: persone entrate in lista, promosse, e quante di queste erano +1 verificati.
- **Incassi**: totale dovuto, versato (esclusi i pagamenti annullati), versato per canale, rimborsato, netto (versato meno rimborsato), ancora da incassare e crediti da restituire.
- Quando una prenotazione è `scaduta`, `disdetta_richiesta` o `rimborsata`, allora non conta tra i presenti né nei pasti (stesse regole delle viste dell'MVP 3); i suoi pagamenti e rimborsi contano negli incassi.
- Quando premo «Scarica CSV», allora ottengo il report in righe «sezione; voce; valore», apribile in Excel italiano (D-020).
- Quando stampo la pagina dal browser, allora escono solo le sezioni del report, senza navigazione né bottoni.
- Quando l'edizione non ha ancora dati di una sezione (es. nessuna attività), allora la sezione compare con zero e non con un errore.

## Modifiche a domain.md

Proposte, **non applicate**: si riportano in `domain.md` solo dopo l'approvazione del maintainer, alla chiusura dell'MVP.

1. **Lista d'attesa**, nuova regola: «Chi è stato invitato da un partecipante (+1), con il legame verificato dall'admin, ha la precedenza in lista d'attesa; a parità vale l'ordine di ingresso. La priorità non cambia il limite della lista.»
2. **Pannello admin**, nelle viste: aggiungere «report di riepilogo dell'edizione (iscrizioni, presenze, pasti, attività, lista d'attesa, incassi)» con export CSV.
3. **Questioni aperte**: togliere «gestione esplicita del +1».

## Fuori scope (Backlog)

- Priorità per chi ha già partecipato alle edizioni precedenti (prelazione).
- Collegare il +1 a un partecipante vero (relazione invece del testo libero).
- Report che confronta più edizioni.
