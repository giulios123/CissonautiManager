# C · Design proposto

## Flussi e dati

C1 riusa `Activity`, `ActivityOffer` e `ActivityView`, ampliando i contenuti visibili a titolo/descrizione IT/EN richiesti per nuovi salvataggi. La migrazione conserva i vecchi testi monolingui, leggibili con indicazione di completamento, senza inventare traduzioni. Date/orari mantengono UTC/Europe/Rome e fallback legacy MVP 16.

C3 propone un campo nullable separato per le note interne di `Activity`, già legata a `edition_id`, e migrazione additiva. Serializzazioni partecipante con whitelist; note negli endpoint e nei **CSV admin attività**, come confermato, mai in payload o export per partecipanti. Non usare descrizione o CSS per nasconderle. I CSV riservati devono mantenere il controllo `require_admin` anche tramite URL diretto.

C2 distingue **esterno senza account** da **iscritto con esenzione**. L'admin inserisce un'identità esterna minima per edizione e le adesioni a pasti/attività; niente `Participant` fittizi, email o slot coworking obbligatori. Le esenzioni dell'iscritto indicano quota e/o singole voci e non cambiano implicitamente gli altri importi. Categoria per edizione e dettaglio per adesione sono la proposta da finalizzare in Q-C2/C3; integrità dell'edizione e deduplicazione esplicite.

Le funzioni logistiche sommano iscritti e adesioni esterne, una persona per adesione, con la stessa capienza e override esplicito. L'eccezione alla presenza coworking per gli esterni è confermata; non estenderla automaticamente agli iscritti ordinari. Gli incassi esterni organizzazione hanno riferimenti propri a edizione/identità/adesione, senza booking: report e registro li distinguono dalle quote, ma li sommano al totale incassato dell'evento. I pagamenti al fornitore restano fuori dal conto. Una stessa somma non compare sia nel booking sia nell'incasso esterno.

Cambio categoria/esenzione durante l'evento: anteprima delle differenze, ricalcolo delle sole voci interessate, incassi invariati e eventuale credito. Il rimborso è amministrativo e tracciato, non un bonifico automatico o una cancellazione del pagamento; per iscrizioni ancora attive servirà un percorso distinto dal rimborso che oggi chiude soltanto una disdetta. Tale estensione va specificata nel pacchetto 25 senza cambiare in silenzio lo stato del posto.

C4: form admin → copia dei campi utili → scelta manuale del programma → creazione attività. Relazione **una proposta, più attività**; il contributo resta modificabile. La modifica non propaga sovrascritture alle attività già create. Distinguere un nuovo comando intenzionale dalla ripetizione dello stesso salvataggio per rete/doppio clic; il secondo non duplica. Cancellazione del contributo senza cascata sulle attività, dettaglio del riferimento residuo Q-C4. Validazioni ordinarie su date/orari/capienza sempre applicate.

C5 riusa il catalogo minimo dei benefit B4 con `edition_id` ed etichetta IT/EN; aggiunge consegne/correzioni per persona+edizione+benefit, preservate quando il catalogo è ritirato. Ammissibilità: quota **base** pagata oppure interno non pagante; non riusare senza distinzione lo stato «confermato» basato su base+giorni. Non legare lo storico a un booking cancellabile. Quantità multiple e restituzioni dopo cambio categoria restano Q-C3; il cambio di diritto non elimina la consegna passata.

## API e pagine interessate

- Attività admin/partecipante: estendere solo i dati mancanti del dettaglio, senza esporre note private negli schemi condivisi.
- Pasti/Attività e viste admin: gestione C2 e conteggi, CSV e report coerenti; percorsi di scrittura definitivi dopo risposte sulle categorie.
- Contributi admin: comando C4 apre la scheda attività precompilata; protezione server contro fonti di un'altra edizione o non accessibili.
- Impostazioni e pagina consegne: nuove letture/scritture admin per catalogo e consegne; nomi mai pubblici. Guide IT/EN pertinenti.

## Impatto e Modifiche a domain.md

Modifiche di prodotto recepite, non ancora operative: esterni senza account con capienza e incassi organizzazione separati; esenzioni mirate degli iscritti; testi attività IT/EN e note nei CSV admin; conversione uno-a-molti modificabile; benefit con soglia quota base/interni non paganti. F resta una valutazione con scelta architetturale confermata: i nuovi dati nascono associabili all'edizione, senza implementare qui il selettore archivio.

Test futuri: contenuti IT/EN e migrazione legacy; note in CSV admin ma assenti ai partecipanti; conteggi/capienze senza coworking, incassi esterni riconciliati e distinti dai booking, esenzioni mirate/crediti/rimborsi; conversioni multiple intenzionali versus doppio invio; ammissibilità e storia delle consegne. Verifica manuale IT/EN e telefono.
