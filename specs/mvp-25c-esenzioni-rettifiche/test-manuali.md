# MVP 25c · Collaudo per organizzatori

Non ancora eseguito. Dopo il deploy, in italiano e in inglese, con una conferma su quota già attiva (MVP 18):

1. Impostare «interno non pagante» su uno speaker: nessun importo cambia. Controllare la cronologia.
2. Esentare la quota di una prenotazione in attesa e senza versamenti: l'anteprima mostra quota 0, stato prima «in attesa» e dopo «confermata». Applicare: la prenotazione è confermata, non è stato creato nessun pagamento, parte una sola email di conferma. Ripetere l'applicazione: nessun effetto doppio.
3. Esentare un solo pasto e una sola attività: le altre voci restano dovute; il saldo mostra solo ciò che manca.
4. Con due schede aperte, cambiare un dato dopo aver fatto l'anteprima: l'applicazione chiede di rifare l'anteprima.
5. Con il «primo pasto compreso» attivo (MVP 23), esentare il primo pasto organizzativo: la copertura passa al pasto successivo non esentato.
6. Togliere un'esenzione da una prenotazione confermata: resta confermata e compare il saldo da versare.
7. Da partecipante, controllare la pagina personale: voci «Esente» con importo 0, nessuna categoria, saldo uguale a quello dell'admin.
8. Su una prenotazione con credito, registrare un rimborso inferiore al credito: stato invariato, nessuna email, saldo aggiornato. Provare un rimborso superiore al credito: rifiutato. Premere due volte: un solo rimborso. Annullarlo con un motivo.
9. Annullare un pagamento dopo un rimborso: il saldo usa il netto e, se non è più coperta la quota di conferma, la prenotazione torna in attesa.
10. Disdire una prenotazione con rimborsi attivi e rimborsare: il tetto è il versato netto.
11. Confrontare report, «Da incassare», «Da verificare» e CSV Persone: conteggio interni non paganti, valore esentato e rimborsi separati da quelli per disdetta; nessun saldo sulle voci esentate.
12. Da un account non admin: nessun accesso a categoria, esenzioni e rimborsi.
