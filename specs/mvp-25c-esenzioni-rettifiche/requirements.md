# MVP 25c · Esenzioni e rettifiche degli iscritti

**Stato:** implementata sul branch `feat/mvp-25c-esenzioni-rettifiche` (sopra il 25b per la catena delle migrazioni, ma indipendente nel codice); restano CI SQL Server e collaudo organizzatori. P2, C2/C3. Decisioni di riferimento D-087, D-089 e D-113–D-116. Dipende dalla conferma su quota dell'MVP 18 e dalla composizione dell'MVP 23; **non dipende da 25a e 25b** e si può rilasciare prima o dopo. Il diritto ai benefit per categoria è l'MVP 30: qui si registra soltanto la categoria.

## US-25c.1 · Categoria dell'iscrizione

- Quando una prenotazione viene creata, allora la categoria è «ordinaria».
- Quando l'admin imposta «interno non pagante» (es. uno speaker), allora la categoria è registrata sulla prenotazione e visibile in scheda, elenco «Persone» e CSV Persone, con filtro.
- Quando cambio la sola categoria, allora nessun importo cambia: la categoria è un'etichetta. Il modulo propone di esentare la quota, ma conta solo ciò che l'admin salva (US-25c.2).
- Quando la categoria cambia durante l'evento, allora la modifica è tracciata nella cronologia con autore, data, valore precedente e nuovo.
- Quando un partecipante legge la sua pagina personale, allora la categoria non compare.

## US-25c.2 · Esenzioni mirate

- Quando l'admin prepara le esenzioni di una prenotazione attiva (in attesa o confermata), allora può esentare la quota e/o singoli pasti e singole attività della prenotazione.
- Quando una voce è esentata, allora il suo importo dovuto vale zero; le voci non esentate restano dovute. Nessuna esenzione azzera il conto in modo implicito.
- Quando la quota è esentata, allora la quota di conferma (MVP 18) vale zero e la prenotazione in attesa si conferma senza versamenti, senza creare un pagamento fittizio.
- Quando il pasto compreso nella quota (MVP 23) sarebbe un pasto esentato, allora l'inclusione passa al primo pasto idoneo non esentato, così la copertura non è sprecata.
- Quando l'admin vuole salvare, allora vede prima un'anteprima per quella prenotazione con quota, totale, versato, saldo o credito e stato prima/dopo. Solo dopo la conferma si applica.
- Quando i dati cambiano dopo l'anteprima, allora l'applicazione risponde con conflitto e non scrive nulla; basta rifare l'anteprima.
- Quando la stessa applicazione si ripete, allora non si duplicano effetti, cronologia o notifiche.
- Quando una prenotazione in attesa risulta coperta dopo l'applicazione, allora si conferma e parte la notifica di conferma prevista dall'MVP 18; una prenotazione confermata resta confermata anche se togliere un'esenzione crea un saldo da versare.
- Quando un'esenzione riguarda una voce che il partecipante toglie e poi rimette, allora l'esenzione non si ripristina da sola: la scheda admin lo segnala.
- Quando cambia la categoria, la quota esentata o una voce, allora nessun pagamento registrato viene modificato, annullato o riallocato.
- Quando la prenotazione è scaduta, chiusa (disdetta, rimborsata) o è solo in lista d'attesa, allora le esenzioni non si applicano.
- Quando chi non è admin tenta di impostare categoria o esenzioni, allora è negato.

## US-25c.3 · Rimborso su iscrizione attiva

- Quando una prenotazione attiva ha un credito (versato netto superiore al totale dovuto), allora l'admin può registrare un rimborso con importo, canale, data e nota.
- Quando l'importo supera il credito disponibile, allora è rifiutato.
- Quando il rimborso è registrato, allora lo stato del posto non cambia, non parte nessuna email e nessun pagamento viene cancellato: il versato netto è la somma dei pagamenti attivi meno i rimborsi attivi.
- Quando il rimborso è stato registrato per errore, allora l'admin lo annulla con un motivo; resta in elenco, barrato.
- Quando lo stesso invio arriva due volte, allora il rimborso è registrato una sola volta.
- Quando un pagamento viene poi annullato, allora la copertura si valuta sul versato netto e vale la regola esistente: se non è più coperta la quota di conferma, la prenotazione torna in attesa con un nuovo blocco.
- Quando si registra un rimborso per disdetta (flusso esistente), allora il tetto è il versato netto, così lo stesso denaro non si restituisce due volte.

## US-25c.4 · Conti, pagina personale e report

- Quando consulto la scheda admin, allora le voci esentate sono marcate, il registro mostra pagamenti e rimborsi e il saldo usa il versato netto.
- Quando il partecipante consulta la sua pagina personale, allora vede le voci esentate come «Esente» con importo zero e i rimborsi nell'elenco dei movimenti; il saldo coincide con quello dell'admin.
- Quando consulto il report, allora trovo il numero di iscrizioni «interno non pagante», il valore esentato e i rimborsi su iscrizioni attive, distinti da quelli per disdetta. Il totale dovuto non conta le voci esentate.
- Quando consulto «Da incassare» e «Da verificare», allora i saldi usano il versato netto e le voci esentate non generano saldi.
- Quando scarico i CSV Persone, report e pagamenti, allora categoria, esenzioni e rimborsi sono colonne tradotte.

## US-25c.5 · Lingue e guida

- Quando uso l'italiano o l'inglese, allora pagine, errori, CSV e guide (admin e partecipante) sono disponibili in entrambe le lingue.

## Modifiche a domain.md

Proposta da approvare, non applicata:

- In «Importi»: la prenotazione ha una categoria (`ordinaria`, `interno non pagante`) e può avere esenzioni esplicite della quota e di singoli pasti e attività; una voce esentata vale zero, le altre restano dovute. Il pasto compreso (MVP 23) non consuma una voce esentata.
- In «Pagamenti»: oltre al rimborso per disdetta esiste un rimborso su prenotazione attiva, al massimo pari al credito, tracciato e annullabile, senza cambio di stato né email. Il versato usato per saldo e conferma è il netto dei rimborsi attivi.
- Le esenzioni si applicano solo con anteprima e conferma dell'admin e non toccano i pagamenti.

## Fuori perimetro

Diritto e consegna dei benefit (MVP 30); esenzioni in massa per più prenotazioni; esenzioni dell'esterno (25b: il non pagante ha dovuto zero); rimborsi automatici o bonifici; riattivazione di scadute o chiuse; chiusura dell'edizione e rettifiche tardive (F).
