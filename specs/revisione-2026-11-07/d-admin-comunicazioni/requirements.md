# D · Admin e comunicazioni · Requisiti

**Stato:** aggiornata con le risposte. P2: D1; P3: D2; **D3 accantonato**; futuro D4; verifica documentale D5. Decisioni D-067–D-070 e precisazioni D-092–D-094. [Risposte e dettagli residui](../domande-aperte.md).

## US-D1 · Aprire il dettaglio dai numeri (D1)

- Quando attivo un numero nella vista settimanale (coworking, pranzi, cene, attività), allora si apre una modale admin con giorno, metrica e persone/adesioni che spiegano esattamente il conteggio.
- Quando una persona compare in più attività, allora il dettaglio distingue adesioni da persone uniche e mostra i titoli delle attività; il totale non viene presentato come persone diverse se conta adesioni.
- Quando un numero è zero, allora il comando mostra uno stato vuoto comprensibile; il dettaglio comprende anche totali e singole fasce come confermato, con persone e link alla scheda, oppure una riga per adesione con titolo sulle attività.
- Quando chiudo la modale con Esc o comando, allora il focus torna al numero; da tastiera i numeri sono veri pulsanti con nome accessibile, focus visibile e titolo contestuale. Il dato è protetto da ruolo admin, non solo dalla pagina.
- Quando lo stato cambia mentre apro la modale, allora aggregato e dettaglio vengono aggiornati insieme o la variazione è segnalata, senza far sembrare errato il totale.

## US-D2 · Mettere prima i giorni utili (D2)

- Quando la data corrente in Europe/Rome è compresa nell'edizione, allora la settimana mostra oggi, poi i giorni futuri in ordine, poi quelli passati in ordine.
- Quando l'evento non è iniziato, allora i giorni restano cronologici; quando è terminato, allora l'ordine torna interamente cronologico, come proposto e accettato.
- Quando la data cambia, allora l'ordine si aggiorna al ritorno alla pagina o al ricaricamento senza saltare mentre l'admin interagisce; numeri, selezioni e titoli restano associati alla loro data reale. Ordine dei CSV e data senza demo sono dettagli residui Q-D2.
- Il rilascio si pianifica in una giornata senza demo; la data va concordata, senza spostare questo requisito dentro un rilascio urgente P1.

## D3 · Vista calendario accantonata

Il maintainer ha chiesto di abbandonare per ora la vista calendario mockuppata. Mockup e relative anteprime sono rimossi dal dossier; nessun lavoro grafico, API, pagina o MVP calendario è pianificato. Questa scelta non elimina D1/D2 sulla vista settimanale esistente.

## US-D4 · Comunicazioni per gruppi (D4, sola bozza MVP)

Come admin vorrei selezionare un gruppo per stato, controllare destinatari e testo prima di inviare una comunicazione tramite tratto.email in un secondo momento.

Bozza di accettazione da discutere, senza dettagli d'integrazione:

- Quando scelgo «da pagare» o «da confermare», allora un'anteprima autenticata spiega il criterio del gruppo e il numero di destinatari distinti, nella sola edizione scelta.
- Quando preparo un messaggio, allora posso rivedere testo IT/EN e destinatari prima della futura conferma esplicita d'invio.
- Quando lo stato di una persona cambia tra anteprima e invio, allora la composizione del gruppo viene ricontrollata; nessuna campagna parte per il semplice fatto di aprire un elenco.
- Quando esistono invii manuali e promemoria automatici D5, allora dovrà essere chiaro quale flusso ha scritto alla persona; regole di esclusione e duplicati saranno decise nel futuro MVP.

Non scegliere API, credenziali, sincronizzazione, webhook o provider di fallback. Nessuna connessione o comunicazione reale autorizzata da questa bozza. Definizione dei gruppi, base per contattare e storico richiedono Q-D3/D4 e F.

## US-D5 · Conoscere i promemoria già presenti (D5)

Esito: **automatismo presente nel codice e nella configurazione infrastrutturale**. Il [riscontro](promemoria-esistenti.md) riporta orario, filtri, testi e limiti. L'effettiva esecuzione/consegna nella produzione corrente non è stata verificata in questa sessione. Non è necessaria una nuova implementazione di promemoria; B1 deve adeguare il residuo usato da quello esistente.
