# Risposte recepite e domande residue

Le risposte del maintainer del 7 novembre 2026, inclusa la precisazione sugli incassi degli esterni, sono recepite nelle spec e nelle decisioni D-076–D-104; D-105 aggiunge il ricalcolo di attivazione confermato preparando le spec 17/18. **Le scelte di prodotto qui chiuse non vanno richieste di nuovo.** La fase rimane documentale; i singoli MVP non sono stati avviati.

## Risposte chiuse

| Riferimento | Esito recepito |
|---|---|
| Q-A1/A2 | Presenza soltanto in viste autenticate; comportamento per email già iscritta invariato, inclusa risposta esplicita attuale. Nessuna nuova lista pubblica. |
| Q-A3 | Completamento persistente e non bloccante; campi richiesti obbligatori. Per Telegram/LinkedIn è valida una dichiarazione di assenza come «non possiedo», da distinguere da un dato mancante. Gli altri campi già obbligatori restano tali. |
| Q-A4 | Preferita la città scelta da elenco; regione derivata per la mappa. Restano i dettagli geografici sotto. |
| Q-A5 | Soglia minima pubblicabile **5 persone**. Non riaprire la soglia; restano insieme contato e trattamento degli aggregati sotto soglia. |
| Q-A6 | Precedente partecipazione derivata quando possibile; Telegram `@username` e LinkedIn URL del profilo, ammettendo la dichiarazione di assenza richiesta in A3. |
| Q-A7 | Confermata la proposta di accesso non penalizzante durante riaccettazione e richiesta al prossimo accesso; aggiungere anche email di richiesta. |
| Q-A8/A9 | Consensi facoltativi revocabili separatamente, senza promessa di rimozione automatica da servizi esterni; una versione legale con corpi IT/EN equivalenti e lingua della prova. Testi concreti ancora da fornire. |
| Q-B1 | Quota di conferma = quota base + giorni scelti; pranzi, cene e attività esclusi. |
| Q-B2 | Confermato anche il ricalcolo con anteprima dei due importi ai prezzi correnti, applicato dall'admin sulle sole attive; incassi invariati, variazioni di saldo/credito mostrate, nessuna riattivazione indiscriminata. D-105 e spec 18. |
| Q-B3 | Primo pasto selezionato; i pasti al fornitore non entrano nell'economia dell'evento e sono soltanto promemoria di costo/istruzioni per il partecipante. |
| Q-B4 | Oltre alla composizione pasti già richiesta, per ora soltanto benefit; nessun catalogo di attività/servizi coperti. Non è interpretato come cancellazione del default primo pasto. |
| Q-B5/B6 | Confermate etichette proposte e revisione esplicita dell'importo se il saldo cambia; sovraversamenti trattati come credito, senza ritentativi automatici. |
| Q-C1/C2 | Esterni senza registrazione/account, inseriti dall'admin con identità minima, ammessi a pasti/attività senza coworking e occupanti capienza; non pagante registrato esente dalla quota e/o singole voci. Gli esterni paganti hanno **incassi separati dell'organizzazione**, come precisato nella risposta successiva. |
| Q-C2 | Esterni paganti con dovuto calcolato; categoria + esenzioni di quota e voci; rimborso tracciato su iscrizione attiva; allergie degli esterni solo con consenso dichiarato dall'admin. Spec 25a/25b/25c e D-113–D-116. |
| Q-C3 | Benefit per chi ha pagato la quota base oppure per interni non paganti, come speaker. Categoria modificabile durante l'evento con eventuale rimborso amministrativo. |
| Q-C4 | Un contributo può generare più attività e resta modificabile; attività indipendenti con riferimento alla fonte e collocazione manuale. |
| Q-C5 | Titolo/descrizione visibili delle attività in due testi IT/EN richiesti; note interne anche nei CSV riservati agli admin. |
| Q-C3/Q-C4 (2026-11-11) | Benefit: una consegna attiva per persona e benefit, diritto con quota esentata incluso, nessuna restituzione tracciata (D-120, D-121; [spec 30](../mvp-30-consegne-benefit/requirements.md)). Proposta→attività: la fonte rimossa lascia il titolo d'origine, solo admin (D-119; [spec 29](../mvp-29-proposta-attivita/requirements.md)). |
| Q-D1/D2 | Dettagli per i numeri, inclusi totali/fasce come proposto; ordine aggiornato al ritorno/ricaricamento senza saltare durante l'interazione. A evento finito ordine cronologico. Rilascio fuori dai giorni di demo. |
| D3, Q-D3/D4 | Vista calendario accantonata, mockup ritirato dal dossier. Comunicazioni di gruppo e relativa integrazione rinviate. |
| Q-E1/E2 | Proposte senza consenso al nome mostrate anonime, solo ad autenticati; soltanto contributi di prenotazioni attive. Chiuso il 2026-11-10: avviso all\'autore e admin che può nascondere (D-117); consultazione per iscritti attivi e admin (D-118). [Spec 27](../mvp-27-proposte-partecipanti/requirements.md). |
| Q-F1 | Stesso database e una sola edizione aperta per volta. |
| Q-F2 | Riuso account con nuova iscrizione e nuovi consensi; il dettaglio dei campi da riproporre non è ancora deciso («non so»). |
| Q-F3/F4 | Archivio soltanto per admin attuali e precedenti; chiusura mediante **CHIUDI EDIZIONE** nelle Impostazioni, non alla sola data di fine. |
| Q-F5 | Richiesto di esplicitare i termini normativi: [riscontro sulle durate](conservazione-normativa.md). Non esiste un termine unico di legge per tutti i dati. |
| Q-F6/F7 | Confermate copie selettive proposte; obiettivo edizioni prima del prossimo evento, se fattibile. Non è una data di rilascio già fissata. |

## Domande aperte residue

Sono soltanto dettagli non coperti dalle risposte, non richieste di riconferma delle decisioni sopra.

| ID stabile | Dettaglio ancora da chiudere | Serve per |
|---|---|---|
| Q-A4 | Come gestire estero, città omonime/non presenti e dati legacy? Per l'Italia si propone elenco ufficiale comuni ISTAT locale e versionato, con identificativo, paese e regione derivabile, senza indirizzo preciso. La provenienza è residenza attuale oppure città di partenza del viaggio? | Profilo 19 e futura mappa |
| Q-A5 | Quale insieme contare nella mappa (confermati, attivi, esterni)? Sotto 5 si sopprime o si raggruppa, senza totali/filtri sottraibili? Quale base/finalità dichiarare per l'aggregato? La soglia 5 è già decisa, ma non garantisce da sola l'anonimato. | Solo futura A7 |
| Q-A6 | Quando lo storico non permette di derivare la precedente partecipazione, raccogliamo una risposta dichiarata oppure manteniamo «non determinabile»? La possibilità di derivare non deve produrre falsi «no». | Profilo 19 |
| Q-A7 | Confermare quali eventuali nuove modifiche limitare prima della riaccettazione; letture, pagamenti già validi e disdetta restano disponibili. Proposta operativa della mail: una richiesta per persona/edizione/versione, con link al login, esclusi chi ha già accettato e le edizioni chiuse. | Privacy 20 |
| Q-A8/A9 | Servono i testi effettivi IT/EN e il riferimento di chi li valida, con destinazioni e trattamento foto/video fuori piattaforma. Le scelte facoltative e il modello bilingue sono già confermati. | Pubblicazione testi 17/20 |
| Q-B4 | Resta da dettagliare la combinazione tra quantità pranzo/cena e budget congiunto «primo pasto», senza doppia inclusione. Il passaggio iniziale B1/B2 con ricalcolo in anteprima è già deciso; i prezzi ai successivi ricalcoli restano D-017 come specificato nel 18. | Inclusioni 23 |
| Q-D2 | Solo la **data del rilascio** senza demo; ordine e CSV decisi in D-122 ([spec 31](../mvp-31-giorni-utili/requirements.md)). | Rilascio 31 |
| Q-F2 | Quali contatti possono essere riproposti dopo login e quali risposte vanno richieste per ogni edizione? Proposta da discutere: nome/contatti come suggerimenti da confermare; provenienza, lavoro, aspettative ed esigenze annuali nuove. | Profilo 19 e futura F |
| Q-F3 | Gli ex admin possono leggere soltanto le edizioni amministrate o tutti gli archivi? Come revocare una vecchia autorizzazione? Nessun accesso in scrittura all'edizione corrente deriva dal solo essere ex admin. | Permessi archivio F |
| Q-F4 | Dopo CHIUDI EDIZIONE, rettifiche/rimborsi tardivi richiedono riapertura tracciata o un percorso dedicato? La data di fine non chiude automaticamente e la chiusura non cancella i debiti. | Chiusura F |
| Q-F5 | Identificare soggetto che incassa e obblighi contabili effettivi; per i dati senza termine numerico di legge, dichiarare la durata o criteri verificabili nell'informativa. Dieci anni non è il default dell'intero archivio. | Conservazione F |
| Q-F7 | Qual è la data del prossimo evento per valutare il margine del lavoro F? Scelta architetturale e obiettivo sono già confermati, non l'implementazione. | Sequenza rilasci |

## Proposte esecutive da rivedere con le spec 17/18

- [MVP 17](../mvp-17-consensi-riservatezza/requirements.md): registro facoltativo indipendente dal booking, gestione degli account noti dopo login e nuovi testi bilingui con legacy preservato. Rimangono da fornire le informative effettive, non le scelte di visibilità/facoltatività già confermate.
- [MVP 18](../mvp-18-conferma-quota/requirements.md): quota persistita insieme al totale, pagamenti aggregati senza riallocazioni fittizie, residuo operativo per stato e quota zero confermata senza Payment zero. Prezzi ai ricalcoli successivi come D-017; preview/apply atomici e notifiche per ciclo. Questi dettagli sono ora proposte concrete nel design, non domande lasciate senza soluzione.

## Rinviato o ritirato

- **D3 calendario:** accantonato su richiesta; nessun mockup da approvare e nessun MVP previsto.
- **Q-D3/Q-D4:** gruppi, basi e coordinamento delle comunicazioni saranno discussi con il futuro D4; nessun lavoro tratto.email ora.
- I dettagli sopra non bloccano indiscriminatamente tutti i rilasci: ogni MVP richiede soltanto le risposte pertinenti.
