# MVP 30 · Collaudo per organizzatori

Da eseguire dopo il deploy, in italiano e in inglese, con un benefit nel catalogo (es. «Borraccia») e queste persone: A ha pagato la sola quota base, B non ha pagato, C è uno speaker «interno non pagante», D è ordinario con la quota esentata, E è solo in lista d'attesa, F è un esterno.

1. Senza benefit nel catalogo la pagina «Consegne» lo spiega e rimanda alle Impostazioni.
2. Con il benefit: in elenco compaiono A, C e D; non B (finché non versa la base), non E né F. Dopo il versamento della base B compare.
3. Cambiare la quota base nelle Impostazioni: l'elenco si adegua alla lettura successiva senza perdere consegne.
4. Premere «Consegna» su A, rapidamente due volte: una sola consegna, con data e autore.
5. Da un secondo admin tentare di consegnare ad A: la riga mostra la consegna esistente, nessun duplicato.
6. Annullare la consegna di A senza motivo: rifiutato; con motivo: A torna «Da consegnare» e lo storico mostra la consegna annullata con motivo. Riconsegnare.
7. Consegnare a C, poi spostarlo a «ordinario» senza esenzione: C resta in elenco, «Senza diritto attuale», consegna intatta.
8. Disdire (con pagamento) la prenotazione di A: la consegna resta visibile, «Senza diritto attuale».
9. Ritirare il benefit dal catalogo: niente nuove consegne, storico leggibile.
10. Come partecipante aprire pagina personale, email e guida: nessuna traccia di benefit o consegne; l'API risponde 403.
11. Nell'elenco non compaiono email, telefono, allergie o importi. Scaricare il CSV: stesse righe dell'elenco.
12. Telefono: pulsanti raggiungibili, stato leggibile senza colore, Esc chiude il dialogo di annullo e il focus ritorna sulla riga.
