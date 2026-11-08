# MVP 22 · Collaudo manuale

Usare un'edizione di prova, pagamenti non reali e provider email in console.

- [ ] Da «Da incassare», aprire «Altro importo» e verificare persona, causale, saldo e residuo di conferma.
- [ ] Provare Escape, chiusura, cambio lingua, tastiera e ritorno del focus al pulsante iniziale.
- [ ] Tentare campo vuoto, zero, valore negativo e importo con oltre due decimali: nessun pagamento deve essere creato.
- [ ] Registrare un pagamento parziale e verificare saldo aggiornato; ripetere fino a coprire la quota, lasciando extra dovuti, e verificare che il posto risulti confermato.
- [ ] Provare un importo superiore al saldo e verificare il credito.
- [ ] Tenere aperta la modale mentre un secondo admin registra o annulla un pagamento; il primo admin deve ricevere il saldo aggiornato e confermare esplicitamente l'importo.
- [ ] Simulare una risposta di rete persa e ripetere l'invio: un solo pagamento deve apparire e la finestra di annullo deve mantenere il tempo originario.
- [ ] Annullare entro 10 secondi e verificare stato, saldo e assenza dell'email; ripetere senza annullare e verificare una sola email entro 30 secondi o al job.
- [ ] Ripetere su telefono e desktop in italiano e inglese.
