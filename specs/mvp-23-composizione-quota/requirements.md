# MVP 23 · Composizione della quota e destinatari

**Stato:** spec proposta per revisione, non implementata. P2, B4–B5. Dipende dall’attivazione esplicita della policy di conferma su quota introdotta dall’MVP 18. L’attivazione delle inclusioni è un’operazione separata. Decisioni di riferimento D-049, D-057–D-061, D-083–D-086 e D-105.

## US-23.1 · Configurare un pasto compreso

- Quando un admin configura la composizione della quota, allora può scegliere «nessun pasto» o «primo pasto selezionato»; non può impostare quantità multiple in questo MVP.
- Quando la policy di composizione non è mai stata configurata, allora il valore proposto è «primo pasto selezionato»; la migrazione lascia la composizione disattivata e non cambia dovuti esistenti.
- Quando la conferma su quota dell’MVP 18 non è attiva, allora l’inclusione non è attivabile e l’interfaccia indica il prerequisito.
- Quando la composizione è salvata, allora riguarda solo l’edizione corrente e non si copia implicitamente ad altre edizioni.

## US-23.2 · Determinare il pasto incluso

- Quando un’iscrizione contiene pasti scelti, allora è compreso il primo per data e, nella stessa data, pranzo prima di cena, tra quelli con incasso dell’organizzazione.
- Quando il primo pasto cronologico è pagato direttamente al fornitore, allora non consuma l’inclusione e resta visibile come costo e istruzioni al partecipante; il calcolo prosegue al pasto successivo idoneo.
- Quando il pasto organizzativo selezionato ha prezzo zero, allora può essere il pasto incluso senza alterare il totale.
- Quando non esistono pasti idonei, allora nessun pasto è compreso e non si crea un’adesione automatica.
- Quando cambiano presenza, pasti, prezzi o destinatari, allora la regola individua di nuovo il primo pasto idoneo. La soglia di conferma resta quota base più giorni; il totale organizzazione include pasti non coperti e attività a carico dell’organizzazione.

## US-23.3 · Valutare e applicare la composizione

- Quando l’admin valuta un cambio della policy, allora un’anteprima mostra per ciascuna iscrizione attiva pasto incluso, quota, totale, versato, saldo o credito e stato prima/dopo.
- Quando l’admin applica un’anteprima valida, allora il server ricalcola importi e transizioni per le sole prenotazioni attive in un’unica transazione, preservando versamenti, scadenze e conferme esistenti.
- Quando dati rilevanti cambiano dopo l’anteprima, allora l’applicazione restituisce conflitto e non scrive nulla; l’admin deve ricaricare l’anteprima.
- Quando si ripete la stessa applicazione, allora non si duplicano aggiornamenti o notifiche. Nessun rimborso o pagamento è generato automaticamente.
- Quando la policy di conferma su quota non è attiva, allora non è possibile applicare la composizione.

## US-23.4 · Mostrare il calcolo coerentemente

- Quando un partecipante o un admin modifica i pasti, allora l’anteprima del totale viene dal calcolo server e identifica il pasto incluso secondo la policy corrente.
- Quando sono mostrati riepiloghi, report o CSV, allora il pasto incluso resta contato come presenza/adesione ma ha importo dovuto zero; i pagamenti diretti ai fornitori restano fuori dagli incassi e dai saldi dell’organizzazione.
- Quando un prezzo o destinatario viene modificato con iscrizioni attive, allora il ricalcolo rispetta le regole di D-049 e D-017, mantenendo crediti, versamenti e scadenze.

## US-23.5 · Definire benefit e destinatari

- Quando un admin gestisce i benefit dell’edizione, allora può creare, rinominare in italiano e inglese e ritirare un elemento del catalogo; non può cancellare uno usato. Le consegne e i criteri di ammissibilità sono rinviati all’MVP 30.
- Quando un pasto o un’attività è presentato, allora UI, email pertinenti, CSV e guida distinguono incasso dell’organizzazione, pagamento in loco al fornitore e copertura tramite quota.
- Quando il contenuto è rivolto a partecipanti, allora testi e istruzioni sono comprensibili in IT e EN e non presentano un costo provider come incasso organizzativo.

## Modifiche a domain.md

Proposta da approvare: la composizione può includere un solo pasto, il primo selezionato tra quelli a carico dell’organizzazione per data e tipo. Un pasto provider non consuma l’inclusione. La regola non modifica la soglia di conferma della quota base più giorni e non crea pasti. Le inclusioni si attivano con preview e applicazione admin dopo l’attivazione della policy dell’MVP 18. Il catalogo dei benefit non attribuisce diritto alla consegna, che sarà disciplinato dall’MVP 30.

## Fuori perimetro

Quantità indipendenti o cumulabili pranzo/cena, attività o servizi inclusi, consegna/ammissibilità benefit, incassi esterni, esenzioni e modifiche alle altre policy dell’MVP 18.
