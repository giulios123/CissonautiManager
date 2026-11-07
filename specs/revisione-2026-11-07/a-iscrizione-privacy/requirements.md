# A · Iscrizione, consensi e privacy · Requisiti

**Stato:** specifica aggiornata con le risposte del maintainer, non implementata. P1: A1–A3; P2: A4–A6; P3/to-be: A7. Decisioni iniziali D-051–D-056/D-074 e precisazioni D-076–D-082/D-104. Solo i dettagli residui sono in [Risposte e domande](../domande-aperte.md).

## US-A1 · Scegliere separatamente i consensi (A1, A2)

Come partecipante voglio distinguere gli usi dei miei dati prima di iscrivermi.

- Quando compilo il modulo, allora vedo caselle distinte per privacy, scarico già esistente, pubblicazione della presenza (nome, cognome, job title, LinkedIn) e foto/video; il consenso sanitario mantiene il proprio flusso separato.
- Quando non concedo presenza o foto/video, allora posso iscrivermi; nessuna casella facoltativa è preselezionata o ricavata dall'accettazione privacy. L'obbligatorietà riguarda la risposta ai campi A4, non un consenso promozionale.
- Quando salvo una scelta, allora finalità, documento/versione e istante UTC sono verificati dal server e conservati, anche per una persona solo in lista d'attesa.
- Quando esiste una vecchia iscrizione senza quelle scelte, allora lo stato è «non espresso», senza inventare un'accettazione o retrodatare il consenso.
- Quando cambio una scelta o revoco, allora resta traccia della scelta precedente e le letture successive applicano la scelta vigente; la revoca della presenza rimuove il nome dall'esposizione E3, mantenendo la proposta anonima. I consensi sono facoltativi e separatamente revocabili, senza promettere rimozione automatica di materiale da servizi esterni; i testi foto/video effettivi restano da fornire.

## US-A2 · Proteggere i dati degli iscritti (A3)

- Quando apro l'iscrizione senza autenticazione, allora non posso ottenere elenchi di nomi, ricerche nominali, suggerimenti o tendine degli invitanti; «chi ti ha mandato» resta testo libero con verifica admin.
- Quando richiamo le API senza sessione, allora nessuna lettura restituisce dati di altri iscritti; gli endpoint partecipante applicano anche il controllo della proprietà del dato.
- Quando invio una nuova iscrizione, allora la ricevuta non espone dati personali preesistenti sull'account; per email già attiva si mantiene il comportamento esplicito `already_registered` e l'invio del link come oggi, confermato dal maintainer. L'esistenza dell'iscrizione resta l'eccezione già accettata in D-005, non un'autorizzazione a leggere la scheda senza login.
- Quando concedo presenza, allora il nome può comparire soltanto nelle viste autenticate previste, inclusa E3; non è prevista una vetrina nominale pubblica. Il consenso non autorizza accesso anonimo.

## US-A3 · Completare il profilo senza perdere l'iscrizione (A4)

- Quando una nuova persona invia il modulo dopo l'attivazione di A4, allora sono richiesti telefono, Telegram, LinkedIn, provenienza, job title e company, aspettative e risposta sì/no alla partecipazione all'edizione precedente; il valore «no» è una risposta valida.
- Quando un iscritto precedente accede con campi mancanti, allora vede una richiesta di completamento con campi già noti precompilati; stato, slot, liste d'attesa, pagamenti, crediti e scadenza restano validi.
- Quando un vecchio iscritto non completa subito, allora vede un promemoria persistente **non bloccante**; può consultare istruzioni, versamenti, consensi e disdire, e non sono bloccati i pagamenti registrati dall'admin.
- Quando una migrazione incontra dati mancanti, allora conserva `null`/«da completare», senza valori fittizi né vincoli retroattivi che impediscano l'apertura della scheda.
- Quando compilo la provenienza, allora scelgo la **città da elenco**; paese e regione sono derivabili dal dato geografico selezionato, senza chiedere un indirizzo. Elenco, omonimie, città estere/mancanti e significato della provenienza sono i dettagli residui Q-A4. I dati storici sconosciuti non sono convertiti arbitrariamente.
- Quando non possiedo LinkedIn o Telegram, allora una dichiarazione esplicita come «non possiedo» o equivalente è una risposta valida, distinta dal campo lasciato vuoto. Altrimenti Telegram usa `@username` e LinkedIn l'URL del profilo; la validazione non rifiuta la dichiarazione di assenza.
- Quando lo storico consente di conoscere la partecipazione all'edizione precedente, allora il dato viene derivato; l'assenza di storico non diventa un falso «no», e il fallback è Q-A6. Job title e company restano risposte obbligatorie.
- Quando cambiano lingua o selezione giorni, allora i valori inseriti restano; giorni, slot, pasti e flusso successivo non vengono riprogettati.

## US-A4 · Accettare una nuova versione della privacy (A5)

- Quando l'admin pubblica una nuova privacy, allora la vecchia versione resta consultabile e la prossima sessione autenticata richiede la nuova accettazione senza attribuirla automaticamente.
- Quando accetto, allora si aggiunge una prova con versione, finalità, persona, edizione e data, preservando le prove precedenti; l'API rifiuta una versione nel frattempo superata e ripresenta quella corrente.
- Quando non ho ancora accettato la nuova versione, allora non cambiano pagamenti o stato della prenotazione; le operazioni eventualmente limitate sono da approvare in Q-A7, mantenendo accesso a informativa, scelte privacy e disdetta.
- Quando cambia solo una finalità facoltativa, allora non vengono revocate o riaccettate altre finalità implicitamente; i testi sanitari continuano a usare il flusso specifico già esistente.
- Quando viene pubblicata una nuova privacy, allora è prevista anche una **email di richiesta di nuova accettazione** IT/EN con accesso autenticato, oltre al richiamo al successivo accesso. Proposta esecutiva: una richiesta per persona/edizione/versione, senza solleciti ripetuti; dettagli residui Q-A7.
- Quando pubblico i testi legali, allora privacy e singole finalità hanno una versione con corpi IT/EN equivalenti; il semplice cambio lingua non crea una nuova versione o una nuova accettazione.

## US-A5 · Consultare le cancellazioni (A6)

L'esito richiesto è una cancellazione consultabile nello storico amministrativo, anche quando l'iscrizione non ha pagamenti. Per questo requisito la verifica richiesta dal maintainer è **esclusivamente la procedura manuale** in [test-manuali.md](test-manuali.md#manuale-a6--storico-della-cancellazione). Non sono previsti casi di test automatici A6 in questa spec.

## US-A6 · Mappa aggregata delle provenienze (A7, sola bozza)

- Quando la futura mappa sarà pubblicata, allora mostrerà conteggi o classi regionali aggregati, con intensità crescente, legenda e data di aggiornamento; niente nomi, link, tooltip personali o dettaglio comunale.
- Quando un insieme contiene meno di **5 persone**, allora non viene pubblicato il suo conteggio individualizzante; soglia minima confermata. Insieme contato, soppressione/raggruppamento e base della pubblicazione restano Q-A5; API, totali, filtri e aggiornamenti devono evitare inferenze anche oltre la sola soglia.
- Quando una persona è all'estero o ha provenienza mancante, allora non viene collocata arbitrariamente su una regione; la presentazione di quei gruppi dipende dalle stesse regole.
- Quando la mappa non è utilizzabile, allora una tabella equivalente accessibile conserva le stesse limitazioni e non espone conteggi più precisi.

La [proposta grafica](proposta-mappa.svg) usa dati inventati e una sagoma schematica; palette e classi sono esempi, la soglia minima 5 è ora confermata. Geometrie regionali reali e loro licenza saranno scelte solo nel futuro MVP, senza servizi di tracciamento esterni. Nessuna mappa applicativa in questa fase.
