# MVP 1 · Iscrizione base · Requisiti

Riferimento: `memory-bank/domain.md`. In caso di conflitto vince `domain.md`.

## US-1 · Primo admin da variabile d'ambiente

Come organizzatore voglio che il primo admin esista già all'avvio, per poter configurare l'edizione.

- Quando l'app parte con `ADMIN_EMAIL` impostata e nessun utente con quell'email esiste, allora viene creato un utente con ruolo `admin`.
- Quando è impostata anche `ADMIN_PASSWORD`, allora il primo admin può entrare subito con email e password.
- Quando l'utente esiste già, allora gli viene assegnato il ruolo `admin` senza duplicarlo.
- Quando `ADMIN_EMAIL` non è impostata, allora l'app parte e scrive un avviso nei log.

## US-2 · Accesso con magic link

Come admin o partecipante voglio entrare senza password usando la mia email.

- Quando inserisco un'email nella pagina `/accedi`, allora vedo sempre lo stesso messaggio ("Se l'email è registrata riceverai un link"), che l'email esista o no.
- Quando l'email esiste, allora ricevo (in console nell'MVP 1) un link con un token monouso valido 30 minuti.
- Quando apro il link entro 30 minuti e premo «Entra», allora entro e ricevo un cookie di sessione httpOnly, Secure, SameSite=Lax valido 14 giorni.
- Quando riapro lo stesso link o lo apro dopo 30 minuti, allora vedo un errore e la possibilità di richiedere un nuovo link.
- Quando l'admin entra, allora arriva al pannello admin; quando entra un partecipante, allora arriva alla sua pagina personale.

## US-2b · Accesso con password (opzionale)

Come admin o partecipante voglio poter entrare anche con email e password.

- Quando sono dentro con una sessione valida e imposto una password di almeno 10 caratteri, allora viene salvata solo come hash e da quel momento posso entrare con email e password.
- Quando inserisco email e password corrette in `/accedi`, allora ricevo lo stesso cookie di sessione del magic link (14 giorni).
- Quando email o password sono sbagliate, o l'utente non ha una password, allora vedo sempre lo stesso errore generico.
- Quando ho dimenticato la password, allora posso usare il magic link per entrare e impostarne una nuova.

## US-3 · Impostazioni essenziali dell'edizione

Come admin voglio configurare l'edizione senza toccare il codice.

- Quando salvo nome, data di inizio e data di fine, allora per ogni giorno vengono creati gli slot mattina e pomeriggio con gli orari di default (9-13 e 14-18) e la capienza di default (25).
- Quando modifico orari o capienza, allora i valori si applicano agli slot dell'edizione.
- Quando provo a togliere dalle date un giorno con slot già prenotati, allora ricevo un errore e niente viene cancellato.
- Quando imposto giorni di blocco, quota base e quota per giorno, allora i nuovi valori valgono per le iscrizioni successive.
- Quando configuro i canali di pagamento (Revolut, Satispay, PayPal, IBAN), allora per ciascuno posso attivarlo e scriverne le istruzioni.
- Quando modifico il testo dell'informativa privacy o dello scarico di responsabilità, allora viene creata una nuova versione e le versioni precedenti restano salvate.

## US-4 · Iscrizione pubblica incorporabile

Come persona invitata voglio iscrivermi da una pagina pubblica, anche dentro Google Sites.

- Quando apro `/iscrizione`, allora vedo i giorni dell'edizione con gli slot mattina e pomeriggio e i posti liberi di ciascuno; gli slot pieni non sono selezionabili.
- Quando la pagina è dentro un iframe di `https://sites.google.com` o `https://*.googleusercontent.com`, allora viene mostrata; da altri domini il browser la blocca.
- Quando invio il modulo senza nome, cognome, email valida, "cosa puoi portare al camp?", almeno uno slot o una delle due checkbox obbligatorie, allora vedo l'errore accanto al campo.
- Quando invio un modulo valido, allora viene creata una prenotazione `in_attesa_pagamento` che occupa i posti scelti, e vedo riepilogo degli slot, importo, causale con il mio codice personale (es. `CSC-7K3P`), istruzioni dei canali attivi e data di scadenza.
- Quando invio il modulo, allora viene salvata la versione dei testi legali accettati con data e ora.
- Quando invio il modulo, allora parte un'email (in console) con riepilogo e magic link; il link si apre in una finestra normale, fuori dall'iframe.
- Quando uno slot scelto si riempie mentre compilo, allora ricevo un errore che indica lo slot e posso cambiare la scelta.
- Quando l'email ha già una prenotazione attiva, allora non ne viene creata un'altra e mi viene inviato il magic link.
- Quando l'email ha solo prenotazioni scadute e c'è posto negli slot scelti, allora viene creata una nuova prenotazione; se non c'è posto, allora l'iscrizione viene rifiutata con l'indicazione degli slot pieni.

## US-5 · Calcolo dell'importo

- Quando scelgo slot su K giorni distinti, allora l'importo è quota base + K x quota per giorno (default 10 € + 1 €/giorno).
- Quando scelgo mattina e pomeriggio dello stesso giorno, allora quel giorno conta una volta sola.

## US-6 · Scadenza del blocco

- Quando creo una prenotazione, allora la scadenza è esattamente N x 24 ore dopo la creazione (N = giorni di blocco).
- Quando una prenotazione `in_attesa_pagamento` supera la scadenza senza essere coperta dai pagamenti, allora alla lettura risulta `scaduta` e i suoi posti tornano disponibili.
- Quando la scadenza non è ancora passata, allora i posti restano occupati.

## US-7 · Elenco e scheda delle iscrizioni

Come admin voglio vedere tutte le iscrizioni.

- Quando apro il pannello admin, allora vedo l'elenco con nome, email, codice, giorni, stato, dovuto, pagato, saldo e scadenza.
- Quando filtro per stato o cerco per nome, email o codice, allora l'elenco si restringe.
- Quando apro una scheda, allora vedo dati di iscrizione, slot, pagamenti registrati e saldo.

## US-8 · Registrazione dei pagamenti

- Quando dalla scheda registro un pagamento con importo, canale, data e nota, allora compare nell'elenco dei pagamenti e il saldo si aggiorna.
- Quando i pagamenti coprono l'importo dovuto, allora la prenotazione diventa `confermata` e parte un'email (in console) di conferma.
- Quando i pagamenti non coprono l'importo, allora la prenotazione resta `in_attesa_pagamento`.
- Quando registro un pagamento su una prenotazione `scaduta` e gli slot hanno ancora posto, allora la prenotazione viene riattivata e, se il pagamento copre l'importo, confermata.
- Quando registro un pagamento su una prenotazione `scaduta` e uno slot è pieno, allora il pagamento viene registrato, la prenotazione resta `scaduta` e la scheda mostra un avviso all'admin.

## US-9 · Pagina personale minima

- Quando entro con il magic link da partecipante, allora vedo in sola lettura slot, stato, importo, saldo, causale, istruzioni di pagamento e scadenza.
- Quando non ho una sessione valida, allora vengo mandato a `/accedi`.

## US-10 · Deploy su Azure

- Quando viene fatto un push su `main`, allora la CI esegue lint e test e, se verdi, pubblica l'immagine e aggiorna la Container App.
- Quando l'app è deployata, allora `GET /api/health` risponde 200 e la pagina di iscrizione funziona dentro Google Sites.

## Modifiche a domain.md

Nessuna.
