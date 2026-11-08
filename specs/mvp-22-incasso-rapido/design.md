# MVP 22 · Design

## Contratto e concorrenza

Riutilizzare `POST /api/admin/registrations/{id}/payments` e il servizio `record_payment`. Le chiamate esistenti restano compatibili. La richiesta della modale aggiunge uno snapshot di stato effettivo, policy, totale dovuto, totale versato e soglia di conferma, più una chiave UUID del tentativo. La risposta include il `payment_id` già restituito oggi e indica se è un replay.

Nel servizio, acquisire prima i lock esistenti di edizione e prenotazione e ricaricare prenotazione e pagamenti. Cercare la chiave idempotente prima del controllo snapshot: se appartiene alla stessa prenotazione e lo stesso admin, restituire il pagamento registrato senza modificare scadenze o invii email; la chiave riutilizzata con un payload differente risponde `409`. Un pagamento nuovo procede solo se snapshot e ammissibilità coincidono. Una modifica concorrente risponde `409` con snapshot corrente e senza scritture.

Aggiungere `Payment.request_key` nullable e un indice univoco filtrato/condizionale sui valori non nulli per mantenere compatibili i pagamenti esistenti e le chiamate precedenti. Migrazione Alembic `0021`, successiva a `0020`, con prova su SQLite e SQL Server. Il job email e l'annullo continuano a operare sul medesimo pagamento.

## Interfaccia

In `AdminCollect`, sostituire il link «Altro importo» con l'apertura della modale. Il form riusa parser e validazione monetaria in centesimi. Data e canale sono precompilati; la nota è facoltativa. Richiedere il dettaglio della prenotazione per mostrare quota, extra e saldo; il backend resta autoritativo per stato e importi.

Un `409` aggiorna la fotografia visualizzata, preserva l'importo digitato e richiede una nuova azione esplicita. La chiave del tentativo resta invariata per i retry identici, ma cambia dopo ogni risposta `409` quando l'admin conferma nuovamente. Il pulsante d'invio è disabilitato durante la richiesta. In caso di esito di rete incerto si riusa la stessa chiave.

Riutilizzare il meccanismo di annullo dei dieci secondi e la conferma differita di trenta secondi, senza estenderli ai flussi della scheda. Per una risposta replay calcolare il tempo residuo dalla registrazione originale e non da un nuovo timer. Conservare l'eccezione di navigazione/lingua di «Da incassare» così l'annullo resta utilizzabile.

Aggiornare i dizionari UI e la guida admin IT/EN. Nessuna nuova email o modello di pagamento.

## Modifiche a domain.md

Applicare B3 già approvato in D-059 e D-086: importo diverso dalla lista, revisione esplicita se il saldo cambia, credito per sovraversamento e nessun retry automatico dopo conflitto. Resta invariata la compatibilità dei pagamenti registrati dalla scheda.

## Test e accettazione

Backend: payload obsoleto, chiave idempotente, riuso chiave con payload diverso, due admin concorrenti, stati non più esigibili, pagamento parziale, soglia confermata con extra residui, credito, annullo e invio differito una tantum. Migrazioni da zero e dalla revisione precedente su SQLite e SQL Server.

Frontend: importo invalido, doppio clic, conflitto con saldo aggiornato, rete incerta e replay, annullo, conferma email, Escape, focus, cambio lingua e layout mobile. Eseguire suite backend/frontend, lint, build e controllo Guide CI.
