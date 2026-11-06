# MVP 15 · Logo dell'edizione e accesso dalla pagina d'iscrizione

## US-1 · Logo gestito dagli organizzatori

Come admin voglio impostare il logo dell'edizione, controllarne l'anteprima e poter ripristinare quello iniziale.

- Quando carico un PNG, JPEG o WebP valido fino a 5 MB, allora l'app lo riduce se serve, lo normalizza in PNG e lo mostra nell'intestazione.
- Quando carico un'immagine trasparente, allora la trasparenza è mantenuta.
- Quando il file non è valido o supera il limite, allora l'app mostra l'errore senza sostituire il logo corrente.
- Quando ripristino il logo, allora l'intestazione torna a usare quello incluso nell'app.
- Quando non esiste un logo personalizzato, allora l'edizione e i nuovi database continuano a usare il logo incluso.

## US-2 · Logo e accesso personale

Come partecipante voglio cliccare sul logo per andare alla mia pagina.

- Quando un partecipante o un admin clicca il logo, allora arriva a `/me`.
- Quando il visitatore non ha una sessione, allora la rotta esistente lo porta a `/login`.
- Quando l'app è incorporata nel sito dell'evento, allora l'intestazione resta compatta e non mostra il logo.

## US-3 · Accesso dal modulo pubblico

Come persona già iscritta voglio trovare l'accesso dalla pagina d'iscrizione.

- Quando apro il modulo, allora vedo il link «Accedi» prima dei campi.
- Quando le iscrizioni sono chiuse, l'edizione non ha testi legali, la pagina è in caricamento o si verifica un errore, allora il link resta disponibile.
- Quando l'iscrizione è già presente, allora trovo il link nella pagina di risposta.
- Quando uso il modulo dentro l'iframe, allora il login si apre in una nuova scheda; fuori dall'iframe si apre nella stessa scheda. Il link conserva la lingua corrente.

Tutte le nuove etichette e le modifiche alla guida sono in italiano e inglese.
