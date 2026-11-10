# MVP 27 · Collaudo per organizzatori

Da eseguire dopo il deploy, in italiano e in inglese, con almeno tre iscritti (A con consenso alla presenza, B senza, C in lista d'attesa o scaduto).

1. Come A e B aggiungere contributi dei quattro tipi, compreso «Competenze che cerco». Verificare l'avviso sul testo visibile agli altri.
2. Come un quarto iscritto aprire «Proposte degli altri»: la proposta di A mostra il nome, quella di B dice «Autore non mostrato»; le proprie non compaiono.
3. Filtrare per tipo: l'elenco si aggiorna.
4. Come A revocare il consenso alla presenza e riaprire la modale da un altro account: la proposta di A ora è anonima.
5. Come admin nascondere la proposta di B con un motivo: sparisce dalla modale degli altri, B la vede ancora, la cronologia riporta chi l'ha nascosta. Mostrarla di nuovo.
6. Come C (scaduto o solo in lista): il comando non c'è.
7. Da non autenticato aprire direttamente l'indirizzo dell'API: nessun dato.
8. Controllare che nella risposta non compaiano email, telefono o id dell'autore anonimo (strumenti del browser).
9. Vista admin e CSV dei contributi e report: quarto tipo e colonna «Nascosta» presenti; i totali coincidono.
10. Esc e Tab nella modale: il focus resta dentro e torna al comando.
