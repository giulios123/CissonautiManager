# MVP 23 · Design

## Dati e regole

Aggiungere alla policy di edizione la scelta `none` / `first_organizer_meal`, con default applicativo `first_organizer_meal` per la configurazione iniziale e valore persistito `none` nella migrazione. La policy resta inattiva fino alla conferma su quota dell’MVP 18. Migrazione additiva, senza modificare importi memorizzati.

Il calcolo condiviso server determina il primo pasto selezionato per data e tipo (pranzo prima di cena), ignorando quelli con `payment_mode=provider`. Considerare incluso anche un pasto organizzativo a prezzo zero. Persistire l’identificativo del pasto incluso nel record dell’adesione, aggiornandolo atomicamente con gli importi, così letture, report ed export concordano con il dovuto salvato. Il calcolo puro riceve edizione, adesioni e regola e restituisce identificativo incluso, quota di conferma e totale organizzazione. Non cambiare la formula di conferma dell’MVP 18.

Il catalogo minimo `Benefit` appartiene all’edizione, con nome IT/EN, stato ritirato e ordine di visualizzazione. L’identità del benefit resta stabile anche se ritirato; la consegna non fa parte di questo MVP.

## Anteprima e concorrenza

Riutilizzare il flusso preview/apply dell’MVP 18. Il fingerprint include policy proposta, revisioni di edizione, adesioni e termini economici, stato/scadenze, pagamenti e annulli rilevanti. L’apply prende lock edizione e prenotazioni in ordine stabile, rilegge i dati e confronta il fingerprint prima di scrivere. Un retry della stessa operazione è idempotente. Modifiche ai pasti e agli importi acquisiscono il lock edizione prima dei lock booking, in coerenza con D-049. La preview non scrive né invia email.

## API e interfaccia

- Endpoint admin autenticati per preview/apply della composizione e CRUD minimo del catalogo benefit.
- Impostazioni mostrano la policy, il prerequisito della conferma su quota e il riepilogo del catalogo.
- Estendere viste pasti e riepiloghi con indicatore «compreso nella quota» e importo zero dovuto per il pasto coperto, lasciando visibili eventuale prezzo provider e istruzioni.
- Il cambio dei pasti usa un’anteprima del server, con la stessa risposta aggiornata usata dalla pagina personale e dalla scheda admin.
- Aggiornare report, CSV, email coinvolte, cataloghi i18n IT/EN e guide in entrambe le lingue.

## Verifiche

Test di dominio per nessun pasto, un pasto, pranzo e cena nello stesso giorno, provider prima del pasto coperto, prezzo zero e riassegnazione dopo modifiche. Test API per anteprima non mutante, attivazione vincolata alla policy 18, conflitto, retry e transazione atomica. Verificare importi e adesioni in scheda, report e CSV. Coprire migrazione da zero e da revisione precedente su SQLite e SQL Server. Checklist manuale per admin e partecipante, IT/EN, telefono e tastiera.

## Modifiche a domain.md

Vedere la proposta in [requirements.md](requirements.md#modifiche-a-domainmd). Applicarla solo dopo approvazione del maintainer.
