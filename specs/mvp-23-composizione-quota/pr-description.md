# MVP 23 · Composizione della quota e destinatari

## Descrizione

Aggiunge la configurazione per edizione del primo pasto compreso, disattivata dalla migrazione e applicabile soltanto dopo l’attivazione esplicita della conferma con la quota dell’MVP 18. Il server riassegna il pasto incluso quando cambiano selezione o destinatario; l’admin vede anteprima e differenze prima dell’applicazione. Catalogo benefit e testi UI/guida sono disponibili in IT/EN. Report e CSV distinguono il pasto compreso e i costi a carico del fornitore.

Pubblicare il codice e attivare i pasti compresi per un’edizione sono passaggi distinti. Le modifiche proposte a `domain.md` non sono state applicate. Non è stato eseguito alcun deploy.

## Verifiche automatiche

- Backend: 1115 test passati.
- Frontend: 410 test passati.
- Ruff, formattazione, lint, TypeScript, build e controllo Guide: passati.
- Migrazione SQLite da zero e dalla revisione precedente: passata.
- SQL Server: da eseguire; il driver ODBC disponibile su macOS non carica OpenSSL e non consente la connessione al server temporaneo.

## Collaudo per gli organizzatori

La checklist dettagliata è in [`test-manuali.md`](test-manuali.md). Verificare almeno:

- prerequisito della conferma su quota dell’MVP 18 e anteprima prima/dopo;
- pranzo prima di cena nello stesso giorno, pasti gratuiti, pasti provider e riassegnazione dopo modifiche;
- conflitto su anteprima obsoleta e retry senza effetti o notifiche duplicate;
- concordanza tra scheda partecipante, scheda admin, report e CSV, con pagamenti e scadenze conservati;
- catalogo benefit IT/EN e ritiro senza cancellazione o assegnazione automatica.
