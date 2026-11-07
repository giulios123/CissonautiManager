# C · Attività, pasti e logistica · Requisiti

**Stato:** aggiornata con le risposte, non implementata. P2: C1–C3; P3: C4–C5. Decisioni D-062–D-066 e precisazioni D-087–D-091. [Risposte e dettagli residui](../domande-aperte.md).

## US-C1 · Conoscere l'attività (C1)

- Quando apro un'attività disponibile o già scelta, allora vedo titolo, descrizione completa, giorno, fascia/orari, costo, destinatario/istruzioni e capienza/posti disponibili se prevista.
- Quando vedo il riepilogo, allora il titolo è leggibile anche su telefono e non sostituito da un identificativo numerico; un conteggio può aprire il dettaglio ma non sostituisce il nome di un'attività specifica.
- Quando un dato facoltativo manca su una vecchia attività, allora la scheda lo gestisce senza errori e non inventa un orario; nuove attività e modifiche ai contenuti visibili richiedono **testi IT/EN**, compresi titolo e descrizione. I dati legacy monolingui restano leggibili e sono segnalati da completare, senza traduzioni inventate.

## US-C2 · Contare tutte le presenze logistiche (C2)

- Quando l'admin aggiunge un esterno pagante o non pagante, allora usa un'identità minima **senza creare account o iscrizione ordinaria**; l'esterno può aderire al solo pasto/attività senza slot coworking e occupa la capienza pertinente.
- Quando l'esterno è pagante e paga l'organizzazione, allora si registra un **incasso separato dalle quote degli iscritti**, riferito alla sua partecipazione e all'edizione; compare nei conti dell'evento come voce distinta. I costi pagati al fornitore restano esclusi dagli incassi dell'evento.
- Quando un iscritto è non pagante, allora è esente dalla quota e/o dalle sole voci esplicitamente esentate dall'admin; le altre restano dovute. Le esenzioni non azzerano indiscriminatamente il suo conto.
- Quando confronto conteggio e dettaglio, allora una persona per lo stesso pasto/attività conta una volta anche se ha account o più ruoli; le categorie sono distinguibili senza gonfiare incassi o iscrizioni ordinarie.
- Quando modifico o annullo una partecipazione logistica, allora dettaglio e totali si aggiornano e l'azione è tracciata; incassi ordinari ed esterni restano distinguibili, senza cancellare movimenti già registrati. Cambi categoria sono consentiti durante l'evento e possono produrre credito o rimborso amministrativo tracciato.
- Quando chi non è admin tenta di modificare categorie/esenzioni, allora l'operazione è negata; nessun elenco pubblico viene creato.

Identità degli esterni, incasso separato, assenza di coworking e occupazione della capienza sono confermati. Restano livello di categoria/esenzione e dettagli di rettifica Q-C2/C3. L'incasso separato aggiorna il precedente vincolo C2 sull'esclusione economica: gli esterni non pagano una quota di iscrizione, ma i loro incassi organizzazione devono essere conteggiati separatamente nel totale evento.

## US-C3 · Annotare informazioni interne (C3)

- Quando un admin scrive una nota interna sull'attività, allora può rileggerla e modificarla dall'area admin con cronologia.
- Quando un partecipante o visitatore legge una risposta API, email, guida o export destinato ai partecipanti, allora la nota non è presente nel payload; nasconderla nel componente non basta.
- Quando l'attività non ha note, allora la compatibilità con schede precedenti è mantenuta. La descrizione visibile ai partecipanti resta un campo diverso.
- Quando l'admin esporta il CSV attività, allora trova anche le note interne; il CSV e il relativo endpoint rimangono riservati agli admin, senza rendere quei dati disponibili al partecipante.

## US-C4 · Trasformare un contributo in attività (C4)

- Quando un admin sceglie «Crea attività» da un contributo, allora si apre una scheda precompilata con titolo e descrizione e un riferimento alla fonte.
- Quando la scheda si apre, allora non è ancora creata un'attività: l'organizzazione sceglie data, fascia, orari, costo, destinatario e capienza e conferma il salvataggio.
- Quando annullo, allora non cambia nulla; quando salvo, allora valgono i controlli dell'attività ordinaria e resta un collegamento alla proposta d'origine.
- Quando il contributo ha già attività collegate, allora ne vedo l'elenco e posso creare intenzionalmente un'altra attività: **un contributo può generarne più di una** e resta modificabile. Il doppio salvataggio accidentale della stessa operazione non crea duplicati.
- Quando modifico il contributo, allora non cambiano automaticamente le attività già organizzate, che conservano la propria scheda e il riferimento alla fonte.
- Nessuna generazione automatica di calendario o iscrizione automatica dell'autore.

## US-C5 · Registrare le consegne dei benefit (C5)

- Quando l'admin definisce un benefit nelle impostazioni dell'edizione, allora una pagina consegne lo mostra accanto alle persone ammesse.
- Quando segno una consegna, allora si registrano persona, benefit, edizione, autore e data/ora; un doppio clic non equivale a due consegne.
- Quando correggo un errore, allora posso annullare la consegna con una traccia, senza cancellare la storia; le persone senza consegna restano distinguibili.
- Quando il benefit non era definito per una vecchia edizione, allora non compare una consegna fittizia; catalogo e consegne non si copiano automaticamente alla nuova edizione.
- Ha diritto ai benefit chi ha pagato la **quota base**, oppure è un **interno non pagante** (es. speaker). Questa soglia è distinta dalla quota base+giorni richiesta per confermare il posto. Esterni e persone solo in lista non acquisiscono diritto per il solo conteggio logistico.
- La categoria può cambiare durante l'evento con eventuale rimborso amministrativo; la consegna già avvenuta resta tracciata, senza cancellazione automatica. Quantità multiple e gestione di una perdita del diritto dopo consegna sono i dettagli residui Q-C3. Non si aggiungono scorte o acquisti in questo MVP.
