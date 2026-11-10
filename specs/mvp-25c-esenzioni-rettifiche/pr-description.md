# MVP 25c · Esenzioni e rettifiche degli iscritti

## Descrizione

Ogni iscrizione ha una **categoria** («ordinaria» o «interno non pagante», per esempio uno speaker): è solo un'etichetta, visibile agli organizzatori nella scheda, nell'elenco Persone (con filtro) e nel CSV; non cambia nessun importo e il partecipante non la vede.

Gli organizzatori possono **esentare** la quota di partecipazione e/o singoli pasti e attività incassati dall'organizzazione. Una voce esentata vale zero, le altre restano dovute. Si applicano con **anteprima** (quota, totale, versato, saldo e stato prima/dopo) e conferma; se la prenotazione cambia dopo l'anteprima, va rifatta. I pagamenti non si toccano. Una prenotazione in attesa che risulta coperta diventa confermata senza inventare un pagamento e riceve la normale email; una confermata resta confermata. Il pasto compreso nella quota (MVP 23) non viene sprecato su un pasto esente.

Se una persona ha versato più del dovuto, l'organizzatore registra un **rimborso del credito**: mai oltre il credito, annullabile con un motivo, senza cambiare il posto né mandare email. Il «versato» usato per saldo, conferma, report e pagina personale è il **netto** dei rimborsi; un pagamento su cui si appoggia un rimborso si annulla dopo aver annullato il rimborso. Il partecipante vede le voci «Esente» e i rimborsi nei pagamenti registrati.

Migrazione additiva `0026_exemptions_refunds` (colonne con valori di default e una tabella nuova; le iscrizioni esistenti restano ordinarie e senza esenzioni). Testi e guida in italiano e inglese. Le modifiche proposte a `domain.md` non sono applicate. Nessun deploy. Il codice è indipendente da 25a/25b; la migrazione segue la 0025 nella catena.

## Verifiche automatiche

- Backend: 1328 test passati; Ruff e formattazione passati.
- Frontend: 451 test passati; lint, TypeScript e build passati.
- Migrazione da zero e downgrade a `0025` provati su SQLite; CI SQL Server da verificare sulla PR.

## Collaudo per gli organizzatori

La checklist è in [`test-manuali.md`](test-manuali.md). Verificare almeno:

- categoria «interno non pagante»: nessun importo cambia;
- esenzione della quota su una prenotazione in attesa senza versamenti: anteprima, conferma senza pagamento inventato, una sola email; ripetere l'applicazione non duplica nulla;
- esenzione di un pasto e di un'attività: le altre voci restano dovute; il primo pasto compreso passa al successivo non esente;
- anteprima obsoleta: l'app chiede di rifarla;
- rimborso fino al credito, non oltre; doppio clic registra una volta; annullo con motivo;
- annullare un pagamento sotto un rimborso: bloccato finché il rimborso non è annullato;
- pagina del partecipante: voci «Esente», rimborsi nell'elenco, nessuna categoria;
- report e CSV Persone: interni non paganti, valore esentato e rimborsi su iscrizioni attive separati da quelli per disdetta.
