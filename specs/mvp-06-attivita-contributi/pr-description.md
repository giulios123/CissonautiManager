# MVP 6 · Attività e contributi

## Cosa c'è
Gli organizzatori creano le attività del camp (gratuite o a pagamento, con o senza limite di posti), ognuna in un giorno e in una fascia. Dalla pagina personale ognuno aderisce alle attività dei momenti in cui c'è, e la quota si aggiorna. Ognuno può anche proporre talk, temi per l'unconference e competenze da condividere; gli organizzatori li vedono in una vista dedicata.

## Da provare a mano (per gli organizzatori)

**Creare le attività** (menu «Attività»)
- [ ] Crea un'attività a pagamento con 2 posti: titolo, giorno, fascia (mattina, pomeriggio, sera), orario indicativo, prezzo e posti. Compare in elenco con «0 / 2».
- [ ] Crea anche un'attività gratuita senza limite (posti vuoti).
- [ ] Modifica titolo e descrizione: funziona sempre. Quando c'è già qualcuno iscritto, prezzo, giorno e fascia non si possono più cambiare, e i posti non possono scendere sotto gli iscritti: la pagina spiega perché.
- [ ] «Elimina» funziona solo per un'attività senza iscritti.

**Pagina personale** (da telefono, con due o tre persone di prova)
- [ ] In «Attività» premi «Scegli le attività»: vedi solo quelle dei momenti in cui sei iscritto. Per la sera conta anche chi ha mattina e pomeriggio dello stesso giorno.
- [ ] Spuntando un'attività a pagamento vedi la nuova quota; dopo il salvataggio quota e saldo sono aggiornati.
- [ ] Quando i posti finiscono, per gli altri l'attività risulta «completo» e non si può spuntare.
- [ ] Se togli lo slot di quel momento, l'attività sparisce e il messaggio lo dice; il posto torna libero.
- [ ] In «Cosa porti al camp» aggiungi un talk, un tema o una competenza; puoi modificarli e toglierli. Sopra vedi cosa avevi scritto all'iscrizione.

**Nel pannello**
- [ ] Dall'elenco apri un'attività: vedi gli iscritti con telefono e stato, quanti posti restano e scarichi il CSV. Dall'elenco scarichi anche il CSV di tutte le attività.
- [ ] Chi è scaduto, ha disdetto o è stato rimborsato non compare tra gli iscritti e non occupa posti.
- [ ] Nella scheda di una persona, «Cambia le attività» permette anche di superare i posti con «Forza oltre la capienza»: la scheda avvisa.
- [ ] Se riattivi una prenotazione scaduta e una sua attività nel frattempo si è riempita, la prenotazione torna senza quell'attività e la scheda lo dice (anche quando la riattivazione arriva da un pagamento).
- [ ] **Contributi**: elenco di tutte le proposte, filtrabile per tipo, con CSV; quelle di iscrizioni scadute o disdette restano, segnate.
- [ ] **Settimana**: c'è la colonna «Attività» con le adesioni per giorno e il totale, anche nel CSV.

## Note tecniche
- Migrazione 0007: tabelle `activity`, `booking_activity`, `contribution`.
- Decisioni D-032, D-033, D-034.
