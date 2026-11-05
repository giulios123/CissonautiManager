# Da incassare: controllo del conto in un clic

Nuova pagina «Da incassare» nel pannello: elenca chi deve ancora pagare e permette di segnare i pagamenti in fila, cercando la causale del bonifico.

## Cosa cambia per gli organizzatori

- Voce di menu «Da incassare» con le iscrizioni in attesa, poi le confermate con una differenza da versare, poi le scadute.
- Ricerca per nome, email o causale (es. CSC-GGSU), canale scelto una volta e ricordato.
- «Segna pagato» registra il saldo intero con la data di oggi. «Altro importo» porta alla scheda.
- Dopo il clic hai 10 secondi per «Annulla». L'email di conferma parte dopo 30 secondi, quindi un annullo tempestivo non la fa partire.
- «Da verificare» non cambia.

## Note tecniche

Migrazione 0010 (due colonne su `payment`). La scadenza dell'email è nel database: la esegue un timer, e il job orario recupera quelle perse. Decisione D-040.

## Test manuali (per gli organizzatori)

- [ ] Apri «Da incassare»: vedi le iscrizioni in attesa, la più vicina alla scadenza per prima.
- [ ] Scrivi la causale di una persona: resta solo la sua riga.
- [ ] Scegli il canale, premi «Segna pagato»: compare «Pagato … · Annulla», poi la riga esce.
- [ ] Dopo circa 30 secondi la persona riceve l'email di conferma; in «Persone» risulta confermata e saldata.
- [ ] Segna un'altra persona e premi «Annulla» subito: torna in attesa e nessuna email arriva.
- [ ] Da telefono: la pagina si usa senza scorrere di lato e i tasti sono comodi da toccare.
- [ ] «Altro importo» apre la scheda e lì l'email di conferma parte subito.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
