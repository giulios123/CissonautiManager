# Regole di dominio

> **Fonte di verità.** Se una spec contraddice questo file, vince questo file finché non viene aggiornato con il consenso del maintainer. Le modifiche si propongono nella sezione "Modifiche a domain.md" della spec.

## Edizione, giorni e slot

- Un'edizione ha date configurabili dall'admin (non ancora definite).
- Ogni giorno ha tre slot: mattina, pomeriggio e sera, con orari configurabili (default 9-13, 14-18 e 19-24).
- Capienza per slot configurabile, default 25, per mattina e pomeriggio. Lo slot serale non ha limite di capienza.
- Il partecipante sceglie qualsiasi combinazione di slot, anche su giorni non contigui.

## Stati della prenotazione

`in_attesa_pagamento` → `confermata` · `scaduta` · `disdetta_richiesta` → `rimborsata`

- L'iscrizione crea una prenotazione `in_attesa_pagamento` che occupa i posti per N giorni (impostazione configurabile).
- Senza pagamento entro la scadenza diventa `scaduta` e i posti si liberano. La scadenza si valuta al momento della lettura: nessun job schedulato obbligatorio.
- Diventa `confermata` quando l'admin registra pagamenti che coprono l'importo dovuto.
- Disdetta: il partecipante la richiede dalla pagina personale, i posti si liberano subito, l'admin rimborsa fuori dal sistema, la segna come `rimborsata` e scrive al partecipante.

## Lista d'attesa

- Quando uno slot è pieno si entra in lista d'attesa per quello slot.
- Dimensione massima: 20% della capienza dello slot (percentuale configurabile).
- Quando si libera un posto, il primo in lista riceve un'email e un blocco di N giorni con le stesse regole di pagamento.

## Importi

- Quota di partecipazione: quota base + importo per ogni giorno con almeno uno slot prenotato, sera compresa (un giorno con la sola sera conta, per ora). Default 10 € + 1 €/giorno, configurabili.
- Pranzi e cene: adesione per singolo giorno, prezzo flat per pasto configurabile. La presenza di giorno permette di aderire al pranzo e la presenza serale alla cena; chi prenota l'intero giorno (mattina e pomeriggio) conta anche per la sera. L'adesione ai pasti non avviene all'iscrizione: si fa dopo, dalla pagina personale, e si può cambiare.
- Attività: create dall'admin, gratuite o a pagamento, capienza opzionale.
- Saldo del partecipante = totale dovuto meno pagamenti registrati.

## Pagamenti

- Nessuna integrazione: Revolut, Satispay, PayPal, IBAN. Istruzioni per canale configurabili dall'admin.
- Causale generata dal sistema con un codice personale (es. `CSC-7K3P`). Il codice serve solo come causale, mai per accedere.
- L'admin registra un pagamento (importo, canale, data, nota) con un clic dalla scheda del partecipante.

## Accesso

- Pagina pubblica di iscrizione senza login, incorporabile in Google Sites tramite iframe: header CSP `frame-ancestors` che autorizza `https://sites.google.com` e `https://*.googleusercontent.com`. Dopo l'invio mostra riepilogo, importo, istruzioni di pagamento e scadenza, e invia un'email con il magic link.
- Magic link: token monouso valido 30 minuti, apre la pagina personale in una finestra normale (fuori dall'iframe). Dopo il login un cookie di sessione httpOnly, Secure, SameSite=Lax dura 14 giorni. Chi non ha un cookie valido può richiedere un nuovo link inserendo l'email.
- Password (opzionale): oltre al magic link si può accedere con email e password. La password si imposta dalla pagina personale dopo un accesso con magic link; il magic link resta sempre disponibile come recupero.
- Pagina personale: modifica degli slot, adesione a pranzi, cene e attività, esigenze alimentari, contributi offerti (talk, temi per l'unconference, competenze), saldo e istruzioni di pagamento, richiesta di disdetta.
- Admin: stessa app, ruolo `admin`. Gli admin si aggiungono e rimuovono dal pannello, senza limite di numero. Il primo admin viene creato da variabile d'ambiente.

## Dati e privacy

- Campi di iscrizione: nome, cognome, email, telefono (opzionale), "chi ti ha invitato?" (testo libero, opzionale), "cosa puoi portare al camp?" (testo libero).
- Checkbox obbligatorie: informativa privacy e accettazione dello scarico di responsabilità. Entrambi i testi sono configurabili dall'admin e la versione accettata viene salvata con data e ora.
- Allergie e intolleranze sono dati sanitari: consenso specifico e visibilità solo agli admin.

## Pannello admin

- Impostazioni: date, slot e orari, capienze, giorni di blocco, percentuale della lista d'attesa, quote, prezzi dei pasti, canali e istruzioni di pagamento, testi legali, gestione degli admin.
- Viste: per persona, per giorno e slot, per attività, settimana aggregata (coworking, pranzi, cene, attività), esigenze alimentari per pasto, pagamenti da verificare. Export CSV per ogni vista.
- L'admin può modificare a mano qualsiasi iscrizione, comprese le disdette che il partecipante non riesce a fare.

## Email

Conferma iscrizione con magic link · conferma pagamento · due promemoria di pagamento (a metà del blocco e 24 ore prima della scadenza) · posto liberato dalla lista d'attesa · conferma disdetta. Nessun altro sollecito.

## Fuori scope

Pagamenti integrati, app native, menu personalizzati, più edizioni contemporanee (il modello prevede comunque l'entità `Edition`).

## Questioni aperte

Importi definitivi, aspetti legali (in attesa di parere), meccanismo dell'unconference, eventuali prelazioni per chi ha già partecipato, gestione esplicita del +1.
