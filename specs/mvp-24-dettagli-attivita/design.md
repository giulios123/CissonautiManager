# MVP 24 · Design

## Dati e migrazione

Estendere `Activity` con titolo e descrizione IT/EN nullable per mantenere leggibili i record esistenti e con una relazione di note revisionate. La migrazione copia titolo/descrizione monolingui esistenti come fallback effettivo, senza inventare traduzioni. Le nuove scritture richiedono titolo in entrambe le lingue; la descrizione può essere vuota in entrambe, ma non in una sola. Un aggiornamento dei testi legacy può lasciare esplicitamente incompleta la traduzione, mentre un nuovo contenuto o la modifica di titolo/descrizione richiede entrambe.

Separare nota corrente da storico. Ogni salvataggio valido della nota aggiorna il valore corrente e aggiunge una revisione con autore e timestamp nella stessa transazione. Il dettaglio storico è disponibile solo a `require_admin`. Le cancellazioni attività mantengono il comportamento e le regole FK già vigenti, senza aggiungere un nuovo flusso di eliminazione.

## API e pagine

- Schemi attività IT/EN e indicatore di traduzioni mancanti per l’admin.
- Endpoint di dettaglio attività per partecipante e admin con whitelist esplicita; endpoint/CSV admin con nota e storico.
- CSV admin include la nota una volta anche per attività senza partecipanti, mantenendo le colonne partecipante vuote per la relativa riga attività.
- Rendere titolo e descrizione localizzati in lista admin, picker, scheda partecipante e riepiloghi che già citano l’attività.
- Scheda mobile accessibile da tastiera, con costo, destinatario e posti liberi; non modifica la logica di adesione.
- Guide, interfaccia, messaggi API ed email pertinenti in italiano e inglese.

## Sicurezza e compatibilità

La serializzazione partecipante costruisce una risposta dedicata che non contiene la nota o la cronologia. L’endpoint CSV conserva `require_admin`, anche su accesso diretto. I vecchi testi restano leggibili dopo l’upgrade; nessuna traduzione automatica o cancellazione dei contenuti legacy.

## Verifiche

Test unitari per fallback/locale e validazione IT/EN. Test API per accesso admin, partecipante e anonimo, isolamento della nota, ordine dello storico e atomicità. Test CSV con attività senza iscritti e con più iscritti. Test migrazione SQLite da zero e da revisione precedente, più SQL Server CI. Verifica manuale IT/EN, tastiera e telefono.

## Modifiche a domain.md

Vedere la proposta in [requirements.md](requirements.md#modifiche-a-domainmd). Applicarla solo dopo approvazione del maintainer.
