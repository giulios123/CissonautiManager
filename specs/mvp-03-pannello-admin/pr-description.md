# MVP 3 · Pannello admin completo

## Cosa c'è
Le viste «come un Excel navigabile» per gli organizzatori, con download CSV, e le azioni per correggere a mano qualsiasi iscrizione: gestione degli admin, rimborsi, modifica di dati, slot e scadenza, annullamento dei pagamenti sbagliati. Ogni modifica a mano finisce in una cronologia sulla scheda.

## Da provare a mano (per gli organizzatori)

**Viste e CSV** (provale con qualche iscrizione vera)
- [ ] Nel menu trovi: Persone, Giorni e slot, Settimana, Da verificare, Admin, Impostazioni.
- [ ] **Persone**: vedi telefono, giorni e sere di ognuno. Filtra per stato o cerca per nome: «Scarica CSV» scarica solo le righe filtrate.
- [ ] **Giorni e slot**: per ogni giorno e slot vedi quante persone ci sono, quanti posti restano e chi sono. Chi ha prenotato mattina e pomeriggio compare anche nella sera, con la scritta «sera dell'intero giorno». Chi è scaduto, ha disdetto o è stato rimborsato non compare.
- [ ] **Settimana**: per ogni giorno trovi mattina, pomeriggio, sera e persone; in fondo le persone diverse in tutta la settimana.
- [ ] **Da verificare**: elenca chi ha pagato in più o in meno, chi è scaduto avendo già pagato, le disdette ancora da rimborsare. Una riga sparisce da sola quando la sistemi.
- [ ] Apri i quattro CSV con **Excel** (e con Numbers o Google Fogli se li usate): accenti, importi con la virgola, date e orari italiani sono giusti e il telefono resta «+39 ...» senza apici.

**Admin**
- [ ] In «Admin» aggiungi una persona già iscritta (basta l'email): ora entra nel pannello con il suo link.
- [ ] Aggiungi una persona nuova (servono nome e cognome): può entrare da «Accedi» con il link via email.
- [ ] Rimuovi un admin: serve la conferma, perde subito l'accesso (anche se era già dentro) e la sua iscrizione, se c'è, resta.
- [ ] Non puoi rimuovere te stesso né l'admin iniziale (quello della configurazione): accanto trovi la spiegazione.

**Correggere un'iscrizione** (dalla scheda di una persona)
- [ ] «Modifica i dati»: cambia nome, telefono, «invitato da». Con un'email già usata da un altro ti dice di no. Nella cronologia compare cosa è cambiato.
- [ ] «Proroga il blocco» (solo se è in attesa): scegli una data in orario italiano; non accetta date precedenti a quella attuale.
- [ ] «Cambia gli slot»: puoi scegliere anche giorni passati. Uno slot pieno è bloccato finché non spunti «Forza oltre la capienza»; dopo il salvataggio compare l'avviso che la capienza è superata e la nuova quota.
- [ ] «Disdici a nome della persona»: senza pagamenti l'iscrizione sparisce, con pagamenti resta «Disdetta richiesta»; alla persona arriva l'email.
- [ ] Su una iscrizione scaduta, «Riattiva la prenotazione»: torna in attesa con un nuovo blocco se c'è posto, altrimenti ti dice quali slot sono pieni.

**Soldi**
- [ ] Su una disdetta richiesta compare «Segna come rimborsata»: l'importo parte da quanto versato, non puoi superarlo, e **non parte nessuna email** (scrivi tu alla persona).
- [ ] «Annulla» accanto a un pagamento: serve un motivo, il pagamento resta in elenco barrato e non conta più. Se l'iscrizione era confermata e non è più coperta, torna «In attesa di pagamento» con un nuovo blocco.
- [ ] Dopo l'annullamento puoi registrare il pagamento giusto e l'iscrizione torna confermata.
- [ ] In fondo alla scheda la «Cronologia» elenca ogni modifica a mano con chi l'ha fatta e quando.

## Note per chi fa la revisione
- La migrazione 0004 aggiunge colonne a `booking` e `payment` e la tabella `audit_log` (nessun dato esistente cambia).
- Una modifica degli slot da parte dell'admin non manda email alla persona (voce nel Backlog).
- L'infrastruttura Azure dell'MVP 2 (task 9) e la CI su SQL Server vanno validate prima del passaggio su `main`.
- Decisioni D-020 a D-024 in `memory-bank/decisions.md`; modifiche a `domain.md` già approvate e applicate.
