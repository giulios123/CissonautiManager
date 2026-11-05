# MVP 4 · Lista d'attesa

## Cosa c'è
Chi trova uno slot pieno può mettersi in lista d'attesa, dal modulo di iscrizione o dalla pagina personale. Appena un posto si libera (una disdetta, uno slot tolto, una capienza aumentata o una prenotazione scaduta) il primo in lista lo riceve in automatico, con un'email che dice quanto versare. Nel pannello si vede la coda di ogni slot e si può togliere qualcuno a mano.

## Da provare a mano (per gli organizzatori)

**Prepara una prova**
- [ ] Nelle **Impostazioni** trovi «Lista d'attesa (% dei posti)», di base 20. Per provare in fretta metti la capienza a 1 e la lista a 100.

**Dal modulo di iscrizione** (meglio dentro la pagina di Google Sites)
- [ ] Con un primo indirizzo email prendi l'ultimo posto di uno slot.
- [ ] Con un secondo indirizzo riapri il modulo: lo slot pieno dice «completo, spunta per entrare in lista d'attesa» e si può spuntare.
- [ ] Spunta solo quello: sotto c'è scritto che per ora non devi pagare nulla. Invia: la pagina dice «Sei in lista d'attesa» con la posizione, e arriva un'email con il link personale.
- [ ] Prova anche uno slot libero più uno pieno: la quota conta solo quello libero, e il riepilogo mostra sia gli slot prenotati sia quelli in lista.
- [ ] Quando la lista di uno slot è piena, il modulo dice «completo, anche la lista d'attesa» e non lo fa spuntare.

**Dalla pagina personale**
- [ ] Chi è in lista vede «Lista d'attesa» con la sua posizione e il pulsante «Esci dalla lista».
- [ ] Chi ha già un'iscrizione vede gli slot pieni con «Mettiti in lista».

**Quando si libera un posto**
- [ ] Con il primo indirizzo disdici: al secondo arriva «Si è liberato un posto» con slot, quota, causale e scadenza del blocco. Nella sua pagina personale compare l'iscrizione in attesa di pagamento.
- [ ] Se chi riceve il posto aveva già pagato tutto, la sua iscrizione resta confermata e compare in «Da verificare» con la differenza da versare.
- [ ] Chi disdice esce anche dalle liste in cui era, e l'email di disdetta lo dice.
- [ ] Una prenotazione che scade passa il posto al primo in lista entro un'ora (serve il job orario attivo su Azure).

**Nel pannello**
- [ ] **Giorni e slot**: ogni slot pieno ha la colonna «Lista d'attesa» con l'ordine. «Togli» rimuove una persona senza mandarle email (avvisala tu) e lo scrive nella cronologia.
- [ ] Il CSV di «Giorni e slot» ha anche le persone in lista, con la posizione.
- [ ] **Persone**: chi è solo in lista compare con lo stato «Solo in lista d'attesa» (senza scheda); il filtro per stato ha anche questa voce. La colonna «In lista» dice per quanti slot aspetta ciascuno.
- [ ] Nella scheda di un'iscrizione, se la persona aspetta anche altri slot, li vedi con la posizione.

## Note tecniche
- Migrazione 0005: `edition.waitlist_percent` e tabella `waitlist_entry`.
- Decisioni D-026, D-027, D-028.
