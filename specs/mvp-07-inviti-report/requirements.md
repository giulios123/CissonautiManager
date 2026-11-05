# MVP 7 · Inviti e report · Requisiti

Riferimento: `memory-bank/domain.md`. In caso di conflitto vince `domain.md`. Dipende dagli MVP 4 (lista d'attesa), 5 (pasti) e 6 (attività), ora su `main`.

Decisione del maintainer (2026-11-05): la priorità va a **chi è stato invitato** (il +1), non a chi invita. Il legame resta il campo testuale «chi ti ha invitato?» (D-008); l'admin lo conferma con una spunta. Nessun posto riservato. Un +1 verificato non entra oltre il limite della lista. Il report distingue prenotazioni confermate e in attesa di pagamento.

## US-1 · Segnare un +1 verificato

Come admin voglio confermare che una persona è davvero l'invitato di un partecipante, così la sua priorità in lista d'attesa è affidabile.

- Quando apro la scheda di una persona che ha compilato «chi ti ha invitato?», allora vedo il testo e la spunta «+1 verificato».
- Quando spunto «+1 verificato», allora la scheda mostra chi l'ha verificato e quando (ora di Roma).
- Quando tolgo la spunta, allora la persona torna senza priorità.
- Quando «chi ti ha invitato?» è vuoto, allora la spunta non è disponibile e l'API rifiuta la verifica.
- Quando un admin svuota «chi ti ha invitato?» dalla modifica dei dati, allora l'eventuale verifica cade (senza invito non c'è un +1).
- Quando la persona è solo in lista d'attesa e non ha una scheda (D-028), allora la spunta compare accanto al suo nome in «Giorni e slot».
- Ogni verifica e ogni rimozione compare nella cronologia (chi, quando, cosa), anche per chi non ha una prenotazione.
- Quando un partecipante prova a chiamare l'azione, allora riceve 403.

## US-2 · Priorità in lista d'attesa

Come +1 verificato voglio passare davanti in lista d'attesa, così chi è stato invitato da un partecipante trova posto prima.

- Quando si libera un posto in uno slot, allora viene promosso il primo +1 verificato in lista per quello slot; se non ce ne sono, il primo per ordine di arrivo.
- Quando ci sono più +1 verificati, allora tra loro vale l'ordine di arrivo.
- Quando l'admin verifica un +1 già in lista, allora la priorità vale dalla promozione successiva, senza che la persona debba rientrare.
- Quando l'admin toglie la verifica, allora la persona torna al suo posto per ordine di arrivo.
- Il limite di dimensione della lista (capienza × percentuale) non cambia: la priorità cambia l'ordine, non chi può entrare. Quando la lista è piena, nemmeno un +1 verificato entra.
- La promozione segue le regole dell'MVP 4 (email, blocco o aggiunta alla prenotazione): cambia solo chi viene scelto.
- Quando una verifica fa scendere di posto altre persone, allora la posizione che vedono nella pagina personale si aggiorna da sola; non parte nessun avviso (già nel Backlog).

## US-3 · Lista d'attesa con la priorità visibile

- Quando apro «Giorni e slot», allora per ogni slot la lista è nell'ordine effettivo di promozione, con la posizione, l'etichetta «+1» per i verificati e «invitato da» per chi ha compilato il campo senza essere verificato.
- Quando premo «Scarica CSV», allora le righe della lista hanno posizione, +1 verificato e «invitato da».

## US-4 · Report di riepilogo dell'edizione

Come organizzatore voglio, a fine edizione, i numeri in una pagina sola, da guardare, stampare o scaricare.

- Quando apro «Report», allora vedo le sezioni: Iscrizioni, Presenze, Pasti, Attività, Contributi, Lista d'attesa, Incassi.
- Presenze, pasti e attività hanno le colonne «confermate» e «in attesa di pagamento», più il totale.
- **Iscrizioni**: prenotazioni per stato (stato effettivo, scadenza valutata a lettura) e persone distinte.
- **Presenze**: per giorno e slot il numero di presenti (sera derivata D-009 inclusa e indicata); il picco di presenti in uno slot, la media per slot di mattina e pomeriggio dei giorni dell'edizione e i giorni-persona (somma per persona dei giorni con almeno uno slot).
- **Pasti**: pranzi e cene per giorno e i totali; regimi (onnivoro, vegetariano, vegano, non indicato) per pasto; il numero di persone con allergie o intolleranze, **solo il numero**: nomi e testi restano nella vista «Pasti», dati sanitari.
- **Attività**: per attività aderenti, capienza (se c'è), prezzo e incasso atteso (prezzo × aderenti).
- **Contributi**: numero di talk, temi e competenze.
- **Lista d'attesa**: voci ancora in lista, promosse (di cui +1 verificati), uscite, tolte dall'admin, annullate per disdetta.
- **Incassi**: totale dovuto, scomposto in quota, pasti e attività; versato (esclusi i pagamenti annullati) e versato per canale; rimborsato; netto (versato meno rimborsato); ancora da incassare e crediti da restituire.
- Quando una prenotazione è `scaduta`, `disdetta_richiesta` o `rimborsata`, allora non conta tra presenze, pasti e attività (stesse regole delle viste dell'MVP 3, 5 e 6); i suoi pagamenti e rimborsi contano negli incassi.
- Quando premo «Scarica CSV», allora ottengo il report in righe «sezione;voce;confermate;in attesa;totale», apribile in Excel italiano (D-020).
- Quando stampo la pagina dal browser, allora escono solo le sezioni del report, senza navigazione né bottoni.
- Quando l'edizione non ha ancora dati di una sezione, allora la sezione compare con zero e non con un errore.
- Quando un partecipante prova a chiamare il report, allora riceve 403.

## Modifiche a domain.md

Proposte, **non applicate**: si riportano in `domain.md` solo dopo l'approvazione del maintainer, alla chiusura dell'MVP.

1. **Lista d'attesa**: nella regola della promozione, «il primo in lista per ordine di arrivo» diventa «il primo +1 verificato in lista, poi gli altri per ordine di arrivo». Aggiungere: «Il +1 è chi ha indicato chi l'ha invitato e ha il legame confermato da un admin. La priorità cambia l'ordine, non il limite della lista.»
2. **Pannello admin**, nelle viste: aggiungere «report di riepilogo dell'edizione» con export CSV e stampa.
3. **Questioni aperte**: togliere «gestione esplicita del +1».

## Fuori scope (Backlog)

- Priorità per chi ha già partecipato alle edizioni precedenti (prelazione).
- Collegare il +1 a un partecipante vero (relazione invece del testo libero).
- Report che confronta più edizioni; la verifica del +1 sta sul partecipante e con più edizioni andrà spostata.
- Avviso a chi scende di posizione (già nel Backlog, MVP 4).
