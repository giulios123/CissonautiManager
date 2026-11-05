# MVP 3 · Pannello admin completo · Requisiti

Riferimento: `memory-bank/domain.md`. In caso di conflitto vince `domain.md`. Dipende dall'MVP 2 (servizio `change_slots`, stato `disdetta_richiesta`).

## US-1 · Vista per persona

Come admin voglio l'elenco di tutti gli iscritti, "come un Excel navigabile".

- Quando apro «Persone», allora vedo nome, email, telefono, codice, giorni, presenza serale, stato, dovuto, pagato, saldo e scadenza.
- Quando filtro per stato o cerco per nome, email o codice, allora l'elenco si restringe (come oggi).
- Quando premo «Scarica CSV», allora scarico esattamente le righe filtrate.

## US-2 · Vista per giorno e slot

- Quando apro «Giorni e slot», allora per ogni giorno e slot vedo presenti, capienza, posti liberi e i nomi.
- Quando una persona ha mattina e pomeriggio dello stesso giorno, allora compare anche nella sera di quel giorno (D-009), con un'indicazione che la presenza è derivata.
- Quando uno slot ha prenotazioni `scaduta`, `disdetta_richiesta` o `rimborsata`, allora quelle persone non compaiono tra i presenti.
- Quando premo «Scarica CSV», allora ottengo una riga per giorno, slot e persona.

## US-3 · Settimana aggregata

- Quando apro «Settimana», allora vedo per ogni giorno il numero di presenti in mattina, pomeriggio e sera (sera derivata inclusa) e il totale delle persone distinte.
- Quando l'edizione ha giorni senza prenotazioni, allora compaiono con zero.
- Le colonne di pranzi, cene e attività si aggiungono negli MVP 5 e 6.
- Quando premo «Scarica CSV», allora ottengo la stessa tabella.

## US-4 · Pagamenti da verificare

- Quando apro «Pagamenti da verificare», allora vedo le prenotazioni che richiedono attenzione, ciascuna con il motivo:
  - `scaduta` con pagamenti registrati;
  - `confermata` con saldo positivo (importo salito dopo una modifica);
  - `confermata` con credito (importo sceso);
  - `disdetta_richiesta` con pagamenti da rimborsare;
  - `in_attesa_pagamento` con pagamenti parziali;
  - `disdetta_richiesta` senza pagamenti, ancora da chiudere (rimborso 0).
- Quando una prenotazione risolve il problema (saldo a zero, rimborso fatto), allora esce dalla vista.
- Quando premo «Scarica CSV», allora ottengo l'elenco con i motivi.

## US-5 · Gestione degli admin

- Quando apro «Admin», allora vedo gli admin con email e nome.
- Quando aggiungo un'email di una persona già iscritta, allora diventa admin.
- Quando aggiungo un'email sconosciuta con nome e cognome, allora viene creata una persona con ruolo admin e può entrare col magic link.
- Quando rimuovo un admin, allora torna partecipante (la sua prenotazione, se c'è, resta).
- Quando provo a rimuovere me stesso, o l'ultimo admin, o l'admin definito da `ADMIN_EMAIL`, allora ricevo un errore e non cambia nulla.
- Non c'è un limite al numero di admin.

## US-6 · Rimborso

- Quando una prenotazione è `disdetta_richiesta`, allora la scheda mostra «Segna come rimborsata».
- Quando la segno con importo, data e nota, allora passa a `rimborsata`, l'importo del rimborso è salvato e compare nella scheda.
- Quando l'importo del rimborso supera quanto pagato, allora ricevo un errore.
- Non parte nessuna email: l'admin scrive al partecipante fuori dal sistema (come in `domain.md`).
- Quando la prenotazione non è `disdetta_richiesta`, allora l'azione non è disponibile.

## US-7 · Modifica manuale di un'iscrizione

- Quando modifico nome, cognome, telefono, «invitato da» o «cosa porti» dalla scheda, allora i dati si aggiornano.
- Quando cambio l'email, allora deve restare unica; se è già usata ricevo un errore.
- Quando modifico gli slot dalla scheda, allora valgono le stesse regole del partecipante (posti, importo ricalcolato, scadenza invariata), ma posso scegliere anche giorni passati.
- Quando uno slot è pieno, allora ricevo l'errore; se spunto «Forza oltre la capienza» e confermo, allora lo slot viene aggiunto comunque e la scheda lo segnala.
- Quando prorogo la scadenza del blocco di una prenotazione `in_attesa_pagamento`, allora la nuova scadenza vale e i promemoria vengono ricalcolati.
- Quando disdico a nome del partecipante, allora valgono le regole della disdetta dell'MVP 2: con pagamenti passa a `disdetta_richiesta`, senza pagamenti viene rimossa; parte comunque la conferma.
- Quando riattivo a mano una prenotazione `scaduta` e c'è posto, allora torna `in_attesa_pagamento` con un nuovo blocco.
- Ogni modifica manuale lascia traccia: chi, quando, cosa.

## US-8 · Correzione dei pagamenti

- Quando annullo un pagamento registrato per errore, allora scrivo il motivo, il pagamento resta visibile ma barrato e non conta nel pagato.
- Quando l'annullamento fa scendere il pagato sotto il dovuto su una prenotazione `confermata`, allora torna `in_attesa_pagamento` con un nuovo blocco e il saldo è corretto.
- Quando il pagamento è già annullato, allora non si può annullare di nuovo.

## US-9 · Navigazione

- Quando entro nel pannello, allora trovo le voci: Persone, Giorni e slot, Settimana, Pagamenti da verificare, Admin, Impostazioni.
- Le tabelle sono accessibili (intestazioni, scorrimento orizzontale su telefono) e navigabili da tastiera.

## Modifiche a domain.md

Proposte (approvate dal maintainer il 2026-11-05, da riportare in `domain.md` alla chiusura dell'MVP):

1. **Capienza**: l'admin può superare la capienza di uno slot con conferma esplicita.
2. **Pagamenti**: non si cancellano, si annullano con motivo.
3. **Rimborso**: registra importo, data e nota, senza email automatica.
4. **Admin iniziale**: l'admin definito da `ADMIN_EMAIL` non si rimuove dal pannello; si cambia dalla variabile d'ambiente.
5. **Presenza serale** nelle viste: derivata come da D-009 e indicata come tale.
6. **Tracciamento**: ogni modifica manuale dell'admin è registrata (chi, quando, cosa).

## Fuori scope (Backlog)

- Modifica manuale dell'importo dovuto (sconti, organizzatori gratis).
- Viste per pasti e attività (MVP 5 e 6).
