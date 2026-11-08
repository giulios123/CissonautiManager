# MVP 21 · Design

## Dati e transazione

Estendere `AuditLog` con riferimenti nullable a partecipante ed edizione e campi strutturati per origine della richiesta ed esito. La voce non dipende da una foreign key alla prenotazione. Mantenere l'azione di audit già usata per le disdette admin, arricchendola con i campi strutturati, così la cronologia della scheda continua a mostrare lo stesso evento senza duplicarlo.

Migrazione Alembic `0020`, successiva a `0019`, additiva e senza importazione delle cancellazioni pregresse. Ogni percorso di disdetta usa la stessa scrittura di dominio e salva evento, mutazione della prenotazione e liberazione dei posti nella transazione corrente. Per una rimozione, la voce viene scollegata dalla prenotazione. Autore nullo indica una disdetta autonoma, non un amministratore fittizio. Non copiare email, allergie, note o profili nella descrizione libera dell'audit.

Conservazione: una voce di cancellazione è consultabile per un anno dalla propria data UTC; il job orario rimuove le sole voci di cancellazione che hanno raggiunto il rispettivo anniversario. Il processo non cancella altre voci di audit.

## API e interfaccia

- `GET /api/admin/registrations/cancellations` restituisce le voci dell'edizione attiva, paginate per cursore stabile ordinato per timestamp e ID decrescenti. Parametro `q` filtra nome ed email conservati nel record della persona. La risposta espone ID voce, nome, email, edizione, timestamp UTC, tipo di autore e risultato.
- La vista React è raggiungibile da «Persone» e da una rotta inglese definita in `routes.ts`. L'API admin protegge l'elenco con `require_admin`.
- Ricerca con invio o debounce, stato di caricamento, errore e lista vuota. Le date sono mostrate in `Europe/Rome`. Tutte le etichette sono in italiano e inglese.
- Aggiornare la cronologia nella scheda admin per leggere autore e descrizione strutturati quando presenti, mantenendo la presentazione delle voci esistenti.

## Modifiche a domain.md

Applicare la regola già approvata in D-056: le disdette, autonome o fatte dall'admin, lasciano una traccia amministrativa consultabile dopo la rimozione della prenotazione. Il nuovo storico parte dal rilascio e conserva le voci per un anno dalla cancellazione. Il job orario elimina le voci scadute.

## Verifiche

La policy di accettazione A6 resta esclusivamente manuale. La suite esistente e il lint verificano le regressioni del flusso e dell'API, senza aggiungere test automatici specifici di cancellazione. Una prova del job verifica che siano eliminate solo le voci di cancellazione all'anniversario. Upgrade da zero e da `0019` sono verificati su SQLite e SQL Server.
