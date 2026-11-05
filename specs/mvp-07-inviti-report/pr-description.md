# MVP 7 · Inviti e report

## Cosa c'è
Chi è stato invitato da un partecipante (il +1) passa avanti nelle liste d'attesa, dopo che un organizzatore ha confermato il legame con una spunta. A fine edizione c'è il report di riepilogo con i numeri di iscrizioni, presenze, pasti, attività, lista d'attesa e incassi, da guardare, stampare o scaricare in CSV. Nessun posto è riservato ai +1 e la lista non si allunga per loro.

## Da provare a mano (per gli organizzatori)

**+1 e lista d'attesa** (con uno slot pieno e due persone in lista; una delle due ha scritto «chi ti ha invitato?»)
- [ ] In «Giorni e slot», nella lista d'attesa, la persona che ha indicato chi l'ha invitata ha scritto «invitato da ... , da verificare» e la spunta «+1 verificato».
- [ ] Spuntando «+1 verificato» compare l'etichetta «+1» e la persona passa al primo posto della lista.
- [ ] Nella pagina personale dell'altra persona la posizione scende (da 1° a 2°), senza che le arrivi nessun avviso.
- [ ] Liberando un posto (per esempio disdicendo un iscritto) l'email del posto va al +1 e non a chi era in lista da prima.
- [ ] Togliendo la spunta la persona torna al suo posto per ordine di arrivo.
- [ ] Chi non ha scritto «chi ti ha invitato?» non ha la spunta.
- [ ] Un +1 verificato non entra se la lista è già piena.
- [ ] Anche nella scheda di un iscritto c'è «+1 verificato», con chi l'ha verificato e quando; la cronologia lo registra.
- [ ] Svuotando «Invitato da» dalla modifica dei dati, la verifica cade.
- [ ] Il CSV di «Giorni e slot» ha le colonne «+1 verificato» e «Invitato da» per chi è in lista.

**Report** (menu «Report»; provalo con qualche iscrizione vera)
- [ ] Vedi le sezioni Iscrizioni, Presenze, Pasti, Attività, Contributi, Lista d'attesa, Incassi.
- [ ] Presenze, pasti e attività hanno le colonne «Confermate», «In attesa di pagamento» e «Totale». I numeri coincidono con «Settimana», «Pasti» e «Attività».
- [ ] Le allergie compaiono solo come numero di persone, senza nomi.
- [ ] In «Incassi» dovuto, versato (senza i pagamenti annullati), rimborsato, netto, ancora da incassare e crediti tornano con «Persone» e «Da verificare».
- [ ] «Stampa» dal browser (anche in PDF): escono solo le sezioni, senza menu né pulsanti.
- [ ] «Scarica CSV» e aprilo con Excel (e con Numbers o Google Fogli): accenti, importi con la virgola, nessun nome di persona.
- [ ] Da telefono la pagina non scorre di lato; le tabelle larghe scorrono da sole.

## Note tecniche
- Migrazione 0008: due colonne su `participant`.
- Decisione D-037 in `memory-bank/decisions.md`; modifiche a `domain.md` applicate (priorità +1, vista Report).
