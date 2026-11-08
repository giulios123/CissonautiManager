# MVP 21 · Storico delle cancellazioni

**Stato:** spec esecutiva per revisione. Dipende dalla chiusura di MVP 20, confermata dal maintainer l'8 novembre 2026. Il registro inizia con le cancellazioni successive al rilascio.

## US-21.1 · Consultare le cancellazioni dell'edizione

Come organizzatore voglio trovare le disdette anche dopo la rimozione della prenotazione.

- Quando apro «Storico cancellazioni», allora vedo le disdette dell'edizione attiva dalla più recente alla più vecchia.
- Quando cerco nome o email, allora l'elenco si restringe alle corrispondenze senza richiedere che la persona abbia una prenotazione corrente.
- Quando consulto una voce, allora vedo persona, edizione, data e ora mostrate in Europe/Rome, autore e tipo di esito.
- Quando un utente non amministratore richiede l'elenco, allora l'API nega l'accesso senza restituire dati personali.

## US-21.2 · Registrare una disdetta

- Quando un partecipante disdice una prenotazione senza pagamenti, allora la prenotazione viene rimossa, i posti si liberano e una voce attribuita al partecipante resta consultabile.
- Quando un partecipante disdice una prenotazione con pagamenti, allora la prenotazione passa a `disdetta_richiesta`, i pagamenti restano intatti e la voce riporta l'esito corrispondente.
- Quando un admin disdice a nome della persona, allora la stessa voce riporta l'admin effettivo come autore ed è mostrata nella cronologia della prenotazione finché questa esiste.
- Quando la stessa richiesta viene ripetuta o fallisce prima del commit, allora non si crea una seconda voce e dati/cronologia restano coerenti con l'esito della disdetta.
- Quando la persona si reiscrive dopo una prenotazione rimossa, allora la vecchia voce rimane riferita alla disdetta e non viene associata alla nuova prenotazione.

## Limiti e accettazione

Si registra solo ciò che serve per persona, edizione, autore, data ed esito. Le voci pregresse restano nelle cronologie già esistenti e non vengono importate nel nuovo elenco. Le nuove voci si conservano per un anno dalla cancellazione e il job orario rimuove quelle che hanno raggiunto tale data. A6 si accetta esclusivamente tramite la procedura manuale del maintainer.
