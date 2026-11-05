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
- Senza pagamento entro la scadenza diventa `scaduta` e i posti si liberano. La scadenza si valuta al momento della lettura; il passaggio del posto liberato al primo in lista d'attesa avviene con il job orario, quindi entro un'ora.
- Diventa `confermata` quando l'admin registra pagamenti che coprono l'importo dovuto.
- Rimborso: l'admin segna come `rimborsata` una disdetta richiesta registrando importo (mai oltre quanto versato), data e nota. Non parte nessuna email: scrive lui alla persona.
- Disdetta: il partecipante la richiede dalla pagina personale, i posti si liberano subito, l'admin rimborsa fuori dal sistema, la segna come `rimborsata` e scrive al partecipante. Se non c'è alcun pagamento registrato la prenotazione viene semplicemente rimossa, senza passaggio dall'admin.
- Modifica degli slot: il partecipante può aggiungere e togliere slot finché la prenotazione è `in_attesa_pagamento` o `confermata` (almeno uno slot resta). L'importo si ricalcola e la scadenza del blocco non cambia. Una prenotazione `confermata` resta tale: il saldo mostra la differenza da versare o il credito. Una `in_attesa_pagamento` il cui nuovo importo è già coperto dai pagamenti diventa `confermata`. Gli slot di giorni già trascorsi (Europe/Rome) non si aggiungono né si tolgono dalla pagina personale: solo l'admin può cambiarli.

## Lista d'attesa

- Quando uno slot è pieno si entra in lista d'attesa per quello slot, dal modulo pubblico o dalla pagina personale. Dal modulo ci si può iscrivere anche con soli slot pieni: la persona è registrata senza prenotazione e i testi legali accettati restano salvati sulla voce in lista.
- Dimensione massima: capienza × percentuale (default 20%, configurabile), arrotondato per difetto. La sera, senza limite di posti, non ha lista.
- Quando si libera un posto (disdetta, slot tolto, aumento di capienza, scadenza), il primo +1 verificato in lista, poi gli altri per ordine di arrivo, riceve lo slot e un'email:
  - prenotazione `in_attesa_pagamento`: lo slot si aggiunge, l'importo si ricalcola e la scadenza diventa la più lontana tra quella attuale e N giorni da ora;
  - prenotazione `confermata`: lo slot si aggiunge e resta confermata, con la differenza nel saldo (come per il cambio degli slot);
  - nessuna prenotazione attiva: ne nasce una nuova `in_attesa_pagamento` con blocco di N giorni.
- Il +1 è chi ha indicato chi l'ha invitato («chi ti ha invitato?») e ha il legame confermato da un admin con una spunta, dalla scheda o da «Giorni e slot». La priorità cambia l'ordine, non il limite della lista: con la lista piena nemmeno un +1 entra. Tra +1 vale l'ordine di arrivo. Se «chi ti ha invitato?» viene svuotato, la verifica cade. Chi scende di posizione non riceve avvisi.
- Chi disdice esce anche dalle liste d'attesa. Chi prenota da sé uno slot per cui aspettava esce da quella lista. I giorni passati non promuovono nessuno.

## Importi

- Quota di partecipazione: quota base + importo per ogni giorno con almeno uno slot prenotato, sera compresa (un giorno con la sola sera conta, per ora). Default 10 € + 1 €/giorno, configurabili.
- Pranzi e cene: adesione per singolo giorno, due prezzi flat configurabili (uno per il pranzo, uno per la cena). Per il pranzo serve almeno uno slot di giorno (mattina o pomeriggio); per la cena la presenza serale, e chi prenota l'intero giorno (mattina e pomeriggio) conta anche per la sera. L'adesione ai pasti non avviene all'iscrizione: si fa dopo, dalla pagina personale, e si può cambiare con le stesse regole degli slot (giorni passati solo l'admin). Togliere uno slot fa cadere i pasti a cui non si ha più titolo, con ricalcolo dell'importo.
- Totale dovuto = quota di partecipazione + pranzi e cene + attività a pagamento, ai prezzi correnti.
- Attività: create dall'admin, gratuite o a pagamento, capienza opzionale. Ogni attività ha un giorno e una fascia (mattina, pomeriggio, sera): può aderire solo chi è presente in quella fascia, sera derivata compresa. Con persone già iscritte non cambiano prezzo, giorno e fascia, la capienza non scende sotto gli iscritti e l'attività non si elimina. Togliere uno slot fa cadere le attività a cui non si ha più titolo; alla riattivazione di una prenotazione scaduta cadono quelle nel frattempo piene. L'admin può superare la capienza con una conferma esplicita.
- Contributi: dalla pagina personale si propongono talk, temi per l'unconference e competenze, più di uno per persona; sono legati all'iscrizione dell'edizione.
- Saldo del partecipante = totale dovuto meno pagamenti registrati.

## Pagamenti

- Nessuna integrazione: Revolut, Satispay, PayPal, IBAN. Istruzioni per canale configurabili dall'admin.
- Causale generata dal sistema con un codice personale (es. `CSC-7K3P`). Il codice serve solo come causale, mai per accedere.
- L'admin registra un pagamento (importo, canale, data, nota) con un clic dalla scheda del partecipante.
- Dalla vista «da incassare» l'admin registra in un clic il saldo intero, sul canale scelto e con la data di oggi; l'importo diverso si registra dalla scheda. Per 10 secondi può annullare subito, e in questo caso l'email di conferma parte dopo 30 secondi (dalla scheda parte subito): un annullo entro i 10 secondi non la fa partire, dopo i 30 secondi non si ritira.
- Un pagamento registrato per errore non si cancella: si annulla scrivendo un motivo. Resta in elenco, barrato, e non conta più nel saldo. Se la prenotazione era `confermata` e non è più coperta, torna `in_attesa_pagamento` con un nuovo blocco.

## Accesso

- Pagina pubblica di iscrizione senza login, incorporabile in Google Sites tramite iframe: header CSP `frame-ancestors` che autorizza `https://sites.google.com` e `https://*.googleusercontent.com`. Dopo l'invio mostra riepilogo, importo, istruzioni di pagamento e scadenza, e invia un'email con il magic link.
- Magic link: token monouso valido 30 minuti, apre la pagina personale in una finestra normale (fuori dall'iframe). Dopo il login un cookie di sessione httpOnly, Secure, SameSite=Lax dura 14 giorni. Chi non ha un cookie valido può richiedere un nuovo link inserendo l'email.
- Password (opzionale): oltre al magic link si può accedere con email e password. La password si imposta dalla pagina personale dopo un accesso con magic link; il magic link resta sempre disponibile come recupero.
- Lingue: l'app è in italiano e in inglese. La lingua si sceglie con il selettore IT/EN (o con `?lang=`), altrimenti è quella del browser; si salva sul partecipante alla registrazione e a ogni cambio da loggato. Gli indirizzi sono in inglese (`/register`, `/login`, `/me`...): gli indirizzi italiani scritti a mano reindirizzano.
- Pagina personale: modifica degli slot, adesione a pranzi, cene e attività, esigenze alimentari, contributi offerti (talk, temi per l'unconference, competenze), saldo e istruzioni di pagamento, richiesta di disdetta.
- Admin: stessa app, ruolo `admin`. Gli admin si aggiungono e rimuovono dal pannello, senza limite di numero. Il primo admin viene creato da variabile d'ambiente e non si rimuove dal pannello (si cambia da lì); non si può rimuovere se stessi né l'ultimo admin.

## Dati e privacy

- Campi di iscrizione: nome, cognome, email, telefono (opzionale), "chi ti ha invitato?" (testo libero, opzionale), "cosa puoi portare al camp?" (testo libero).
- Checkbox obbligatorie: informativa privacy e accettazione dello scarico di responsabilità. Entrambi i testi sono configurabili dall'admin e la versione accettata viene salvata con data e ora.
- Esigenze alimentari: il regime (onnivoro, vegetariano, vegano) si salva senza consenso. Allergie e intolleranze sono dati sanitari: si salvano solo con un consenso specifico, il cui testo è configurabile dall'admin e versionato (si salvano versione, data e ora); togliere il consenso le cancella. Le vedono solo la persona e gli admin, mai nelle email. Stanno sulla prenotazione e spariscono con essa.

## Pannello admin

- Impostazioni: date, slot e orari, capienze, giorni di blocco, percentuale della lista d'attesa, quote, prezzi di pranzo e cena, canali e istruzioni di pagamento, testi legali (compreso il consenso per i dati sanitari), gestione degli admin.
- Viste: per persona, per giorno e slot, per attività, settimana aggregata (coworking, pranzi, cene, attività), esigenze alimentari per pasto, pagamenti da incassare (iscrizioni in attesa o con un saldo da versare, con ricerca per causale), pagamenti da verificare, report di riepilogo dell'edizione (iscrizioni, presenze, pasti, attività, contributi, lista d'attesa, incassi, con confermate e in attesa di pagamento separate; le allergie solo come numero; anche in stampa). Export CSV per ogni vista. La presenza serale di chi ha prenotato l'intero giorno è derivata (D-009) e nelle viste è indicata come tale.
- L'admin può modificare a mano qualsiasi iscrizione, comprese le disdette che il partecipante non riesce a fare. Può superare la capienza di uno slot solo con una conferma esplicita.
- Ogni modifica manuale dell'admin è registrata (chi, quando, cosa) e compare nella cronologia della scheda.

## Email

Ogni email parte nella lingua del partecipante (italiano o inglese).

Conferma iscrizione con magic link (o di ingresso in lista d'attesa) · conferma pagamento · due promemoria di pagamento (a metà del blocco e 24 ore prima della scadenza, ciascuno una sola volta per blocco; con un blocco sotto le 48 ore parte solo quello a metà; ripartono se la prenotazione viene riattivata) · posto liberato dalla lista d'attesa · conferma disdetta. Nessun altro sollecito.

## Fuori scope

Pagamenti integrati, app native, menu personalizzati, più edizioni contemporanee (il modello prevede comunque l'entità `Edition`).

## Questioni aperte

Importi definitivi, aspetti legali (in attesa di parere), meccanismo dell'unconference, eventuali prelazioni per chi ha già partecipato.
