# D · Design proposto

## Flussi e letture

D1: `AdminWeek.tsx` → comando sul conteggio → dettaglio admin per data/metrica → eventuale apertura scheda persona. Riutilizzare i caricatori delle viste slot/pasti/attività, con identici stati effettivi e regole di presenza serale derivata. Non ricostruire i conteggi nel browser con criteri diversi. Il conteggio attività è adesioni: il dettaglio presenta una riga per attività/persona, con titolo; l'eventuale raggruppamento per persona mantiene visibile il numero di adesioni.

Nuova lettura di dettaglio o estensione delle letture admin esistenti; path e formato definitivo da fissare nella spec esecutiva. Validare data dell'edizione, metrica ammessa e ruolo `require_admin`, non esporre note interne o allergie dove il conteggio non le richiede. C2 può aggiungere poi le categorie allo stesso caricatore; D1 deve funzionare anche prima di C2. Se C2 arriva prima, il dettaglio deve includere le nuove presenze per restare coerente.

Modale con titolo giorno/metrica, stato caricamento/errore/vuoto, chiusura esplicita, focus contenuto e ritorno al pulsante; nessun nuovo dato persistito. CSV settimanale conserva il significato delle date; l'ordine dell'export è Q-D2.

D2 è solo presentazione, nessuna migrazione. Calcolo `Europe/Rome` indipendente dal fuso del dispositivo/server. Confermato aggiornamento al ricaricamento/ritorno alla pagina, senza riordino improvviso durante l'interazione. Prima/dopo evento ordine cronologico; restano ordine CSV e finestra senza demo Q-D2. Rilascio separato.

## D3 · Accantonato

La vista calendario e il mockup sono ritirati dal piano su richiesta del maintainer; non esiste una proposta grafica corrente da approvare. D1/D2 si applicano alla tabella settimanale esistente. Nessun generatore di programma.

## D4 · Confini della bozza

Selezione gruppo → anteprima destinatari deduplicati → testo nelle lingue necessarie → revisione → futura conferma esplicita. Per ora solo concetto di MVP, nessuno schema tecnico di integrazione. Lo storico di invio dovrà essere attribuibile all'edizione e sottoposto a conservazione F, ma i campi saranno discussi quando il lavoro sarà autorizzato.

## Modifiche a domain.md

Recepiti come prodotto: dettaglio dai conteggi e ordine dei giorni utili; codice ancora invariato. D3 accantonato, D4 rinviato senza aggiungere invii. D5 documenta l'esistente; B1 aggiornerà importo/soglia dei promemoria, non la cadenza D-014/D-016. L'email di richiesta privacy A5 è distinta dalle comunicazioni di gruppo D4.

Test futuri D1: corrispondenza totali/dettagli, accessi e tastiera. D2: oggi, prima/dopo evento, cambio data di Roma e collegamenti corretti. Nessun test applicativo nuovo per le sole bozze D3/D4 o per il riscontro D5.
