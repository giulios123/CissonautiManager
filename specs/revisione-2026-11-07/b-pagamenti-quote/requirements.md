# B · Pagamenti e quote · Requisiti

**Stato:** aggiornata con le risposte, non implementata. P1: B1–B2; P2: B3–B5. Decisioni D-057–D-061 e precisazioni D-083–D-086. [Registro risposte e dettagli residui](../domande-aperte.md).

## US-B1 · Confermare pagando la quota (B1)

Come partecipante voglio confermare il posto pagando la sola quota di registrazione.

- Quando i pagamenti validi coprono la quota necessaria alla conferma, allora l'iscrizione in attesa diventa confermata anche con pranzi, cene o attività ancora dovuti; il saldo totale continua a comprendere quegli extra riscossi dall'organizzazione.
- Quando il versato è inferiore alla soglia, allora l'iscrizione resta in attesa con la propria scadenza. La soglia confermata è **quota base + importo per i giorni scelti**, senza pranzi, cene o attività; le esenzioni approvate in C2 riducono soltanto le componenti cui si applicano.
- Quando una persona confermata aggiunge un extra o viene ricalcolato il suo prezzo, allora resta confermata e vede il saldo aggiornato; i costi al fornitore restano fuori dal saldo dell'organizzazione.
- Quando un pagamento è annullato, allora il ritorno in attesa dipende dalla copertura della quota, non dal saldo extra; una quota ancora coperta conserva la conferma.
- Quando un vecchio iscritto ha già pagato, allora nessun versamento è perso, riscritto o duplicato; un saldo negativo resta credito. La transizione mostra un'anteprima all'admin e conferma solo le attive ammissibili secondo la proposta accettata; scadute/chiuse non si riattivano in massa.
- Quando si invia il promemoria automatico di conferma posto, allora riguarda solo la quota mancante delle iscrizioni ancora in attesa: nessuna minaccia di perdere il posto per soli extra. La cadenza esistente D5 non cambia.

## US-B2 · Capire cosa versare adesso (B2)

- Quando apro la pagina personale, allora leggo «Dovuto per confermare la prenotazione: X €», con importo ottenuto dal server in base alle impostazioni; sotto leggo che pranzi, cene e attività possono essere pagati dopo.
- Quando la quota è parzialmente versata, allora vedo distintamente quota richiesta, già versato e residuo per la conferma; non devo interpretare il totale comprensivo di extra come soglia. La frase X indica il residuo proposto; conferma in Q-B1.
- Quando il posto è confermato, allora lo stato è esplicito, il residuo per conferma è zero e gli extra ancora dovuti restano visibili.
- Versione inglese proposta: «Amount due to confirm your booking: €X» e «Lunches, dinners and activities can be paid later.» UI, email con importi/scadenze e guida devono concordare.

## US-B3 · Registrare un importo dalla lista (B3)

- Quando premo «Altro importo» in Da incassare, allora si apre una modale con persona, causale, saldo e importo modificabile, canale, data e nota, senza aprire la scheda completa.
- Quando salvo un importo positivo valido, anche parziale, allora viene registrato una sola volta e saldo/stato della riga si aggiornano; zero e importi negativi sono rifiutati senza scritture.
- Quando il pagamento copre la quota ma non tutti gli extra, allora il posto risulta confermato e l'eventuale residuo resta da incassare.
- Quando salvo dalla modale, allora vale l'annullo di 10 secondi e la conferma email differita di 30 secondi già presente nell'MVP 10; annullare conserva il registro e ricalcola con B1.
- Quando cambio lingua, premo Esc o chiudo senza salvare, allora non si registra un pagamento e il focus torna al comando iniziale; il doppio invio è impedito. Se il saldo cambia, l'admin deve rivedere e confermare l'importo corrente; sovraversamenti producono credito e non vengono registrati da un ritentativo automatico, come confermato in Q-B6.

## US-B4 · Configurare le voci comprese nella quota (B4)

- Quando l'admin configura la composizione della quota, allora può indicare le voci coperte e le quantità di pranzi/cene; il default per una nuova politica è **un solo pasto**, il primo pranzo oppure la prima cena in ordine cronologico del calendario del partecipante.
- Quando sono selezionati più pasti coperti da quella politica, allora solo quello individuato è compreso e gli altri restano addebitati al prezzo configurato; 5 e 6 € sono esempi, non valori imposti.
- Quando non è selezionato alcun pasto, allora non si crea un'adesione automaticamente. Il primo è il primo **selezionato**; i pasti pagati al fornitore restano integralmente fuori dal conto dell'evento, come promemoria di costo/istruzioni, e non consumano il pasto coperto dalla quota.
- Quando cambia la selezione o la politica, allora si mostra l'effetto economico, si ricalcola secondo la regola approvata e si mantengono versamenti e crediti; nessun doppio sconto e nessun rimborso automatico.
- Quando attivo B4 con iscritti precedenti, allora il default non modifica in silenzio il loro dovuto: occorre l'anteprima confermata in Q-B2; resta da formalizzare il dettaglio dei ricalcoli al cambio delle impostazioni.
- Quando configuro altre voci della quota oltre ai pasti previsti, allora per ora scelgo **soltanto benefit**; attività e servizi generici coperti sono fuori dal perimetro. Configurazione dell'inclusione e consegna effettiva del benefit sono due momenti distinti.

## US-B5 · Distinguere destinatario e composizione (B5)

- Quando vedo una voce a pagamento, allora distinguo le due modalità confermate: incasso dell'organizzazione oppure pagamento in loco direttamente al fornitore; costo reale, destinatario e istruzioni sono espliciti.
- Quando una voce usa la modalità organizzazione, allora non compare più la dicitura generica «incluso nella quota»: l'essere compresa dipende da B4, non dalla modalità d'incasso.
- Quando una voce è pagata al fornitore, allora conta nelle adesioni logistiche ma non negli incassi, versamenti o residuo dovuto all'organizzazione, come già nell'MVP 16.
- Quando compaiono etichette in UI, email, CSV o guida, allora non attribuiscono all'organizzazione un pagamento diretto. Le stringhe del design sono confermate in Q-B5; non si introduce un terzo tipo di pagamento. Gli incassi degli esterni di C2 sono un flusso organizzazione separato dalle quote degli iscritti, non una terza modalità di destinatario.
