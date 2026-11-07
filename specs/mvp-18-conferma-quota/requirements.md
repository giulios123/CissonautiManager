# MVP 18 · Conferma con la sola quota · Requisiti

**Stato:** spec esecutiva proposta il 7 novembre 2026; nessun codice implementato. Fonti: [gruppo B](../revisione-2026-11-07/b-pagamenti-quote/requirements.md), decisioni D-057/D-058/D-083/D-084 e risposta diretta «Ricalcolo con anteprima» ricevuta preparando questa spec. Migrazione prevista dopo il 17; il dominio pagamenti resta indipendente dai consensi.

## Controllo B0, scelte e confini

Il maintainer conferma superate tutte le prove SQL di MVP 16; la prova visiva di MVP 16 resta aperta. Il 17 è in implementazione sul branch `feat/mvp-17-consensi-riservatezza`; le verifiche SQL Server e visive delle nuove modifiche restano da eseguire prima di considerare chiusa la sua validazione. Il 18 va sviluppato sullo schema aggiornato del 17.

**Confermato:** quota per il posto = base + importo per i giorni scelti; pasti/attività esclusi; transizione con anteprima e applicazione admin; incassi invariati, confermate stabili, nessuna riattivazione di scadute/chiuse in massa. L'anteprima ricalcola quota e totale con i prezzi correnti: il **saldo/credito può quindi variare**, ed è mostrato prima dell'applicazione; i movimenti di pagamento restano identici.

**Proposte tecniche definite nel design:** due importi persistiti coerenti; pagamenti aggregati confrontati con la quota senza dividerli contabilmente; quota zero confermata automaticamente; mantenimento della regola D-017 sui prezzi ai successivi ricalcoli. Sono parte della spec da rivedere, non modifiche già applicate al prodotto.

Dentro: B1/B2 e adeguamento dei promemoria D5, tutti i percorsi che confermano/annullano/ricalcolano, transizione legacy protetta, dati/etichette IT/EN coerenti. Fuori: modale B3 (22), pasti compresi/benefit B4 e revisione globale B5 (23), esenzioni/esterni/rimborsi nuovi (25a–c), consegne (30), nuovi mezzi di pagamento o solleciti per gli extra, nuovo motore prezzi, edizioni F. La quota base per i benefit è una soglia diversa e non viene implementata qui.

## US-18-1 · Distinguere conferma e saldo

- Quando un booking ha slot su K date distinte, allora la quota è `base_fee + K × per_day_fee`, sera compresa e stesso giorno contato una sola volta; non conto slot in sola lista d'attesa.
- Quando aggiungo pasti/attività riscossi dall'organizzazione, allora aumentano il totale dovuto ma non la quota necessaria al posto; costi `provider` restano fuori da entrambi.
- Quando registro pagamenti non annullati almeno pari alla quota, allora un'iscrizione ancora in attesa valida diventa confermata anche se resta saldo extra; nessuna divisione fittizia dei vecchi versamenti è necessaria.
- Quando il versato è sotto la quota, allora il blocco/scadenza dell'attesa resta applicato come oggi; quote e importi sono centesimi interi, mai float.
- Quando la nuova politica è attiva, la quota è zero e ci sono slot effettivamente assegnati, allora il posto viene confermato senza un pagamento da zero; chi è soltanto in lista resta senza booking e senza quota. La sola distribuzione della migrazione non cambia il comportamento legacy.

## US-18-2 · Mostrare che cosa serve adesso (B2)

- Quando apro la pagina personale di un booking in attesa, allora leggo «Dovuto per confermare la prenotazione: X €», con X pari al residuo della quota; vedo anche quota totale, versato e saldo complessivo separati.
- Quando ho versato solo parte della quota, allora X è il residuo, non il totale comprensivo degli extra.
- Quando il posto è già confermato, allora l'interfaccia non richiede una seconda conferma né mostra una scadenza di perdita del posto per gli extra; il residuo operativo per confermare è zero e l'eventuale saldo/credito resta visibile.
- Quando leggo ricevuta, scheda admin o email, allora sono coerenti su stato, quota, saldo e frase «Pranzi, cene e attività possono essere pagati dopo», con versione IT/EN.
- Quando l'edizione non ha ancora attivato la nuova politica, allora il comportamento attuale resta esplicito: non mostrare la nuova promessa su un backend che conferma ancora sul totale.

## US-18-3 · Coprire ogni transizione

- Quando cambio slot, pasti o attività, o l'admin ne cambia costo/destinatario, allora quota e totale sono ricalcolati insieme; una in attesa coperta diventa confermata e una già confermata resta tale, come D-017.
- Quando una modifica aumenta anche la parte base/giorni di una già confermata, allora non perdo il posto: il saldo mostra la differenza, senza minaccia di scadenza. Un successivo annullo di pagamento viene invece verificato rispetto alla quota allora salvata.
- Quando annullo un pagamento e il versato residuo copre ancora la quota, allora la conferma resta; quando non la copre più, allora ritorna in attesa con nuovo blocco e promemoria, mantenendo la riga annullata e il motivo.
- Quando viene riattivata una scaduta con pagamento o azione admin, allora prima si verificano posto disponibile e assenza di un'altra iscrizione attiva e si ricalcolano entrambi gli importi; solo dopo si valuta la quota. I pagamenti restano registrati anche se la riattivazione non è possibile, come oggi.
- Quando viene assegnato uno slot dalla lista, allora vale lo stesso calcolo; una confermata resta confermata, una nuova prenotazione a quota zero è già confermata e una sola lista non genera debito.

## US-18-4 · Promemoria e conferme coerenti

- Quando scatta un promemoria del posto, allora il filtro e l'importo usano il residuo quota di una iscrizione ancora in attesa valida, non gli extra; le soglie metà blocco/24 ore, il job orario e la lingua restano quelle esistenti.
- Quando una confermata ha soltanto extra da pagare, allora non riceve email che minacciano di liberarne il posto; resta invece visibile in Da incassare secondo il saldo totale.
- Quando un pagamento rapido conferma, allora restano annullo 10 secondi e email differita 30 secondi con recupero orario; nessun doppio invio se timer/job si sovrappongono o il pagamento è annullato.
- Quando la conferma nasce dal cambio di regola o da un ricalcolo senza un nuovo pagamento, allora l'email comunica «prenotazione confermata» senza inventare un nuovo incasso; ogni passaggio effettivo a confermata ha al massimo un tentativo automatico di notifica, con gli eventuali fallimenti registrati come già previsto da D-016.
- Quando la registrazione a quota zero è già confermata, allora la normale email di iscrizione basta e non viene simulata una ricevuta di pagamento.

## US-18-5 · Passare dalla vecchia regola senza modifiche silenziose

- Quando applico la migrazione, allora non cambiano da soli stato, importi, pagamenti, scadenze o email: la politica corrente resta «totale» finché l'admin non applica l'anteprima.
- Quando apro l'anteprima admin, allora vedo per ciascun booking attivo quota/totale/saldo e stato prima/dopo, variazioni di credito e numero di email previste; dati di sole liste/scadute/chiuse non sono ricalcolati o riattivati.
- Quando qualcuno cambia prezzi, adesioni, versamenti, stato o scadenza mentre l'anteprima è aperta, allora l'applicazione rifiuta un'anteprima non più valida e chiede di rileggerla, senza applicazione parziale.
- Quando applico l'anteprima valida, allora l'intero passaggio dell'edizione è atomico: quote e totali attivi ricalcolati ai valori mostrati, stati già confermati conservati, nuove conferme solo tra attese ancora valide e pagamenti intatti.
- Quando ripeto la stessa applicazione per doppio clic o risposta persa, allora non ricalcolo una seconda volta, non aggiungo pagamenti e non duplico notifiche; un annullo del browser prima di applicare non cambia niente.
- Quando le notifiche successive falliscono, allora non sono annullati gli importi o gli stati già salvati; la mancata consegna è osservabile e non si dichiarano email consegnate sulla sola base della coda.

## US-18-6 · Compatibilità amministrativa

- Quando l'admin cambia le impostazioni tariffarie, allora mantengo il comportamento corrente D-017: valgono per nuove iscrizioni e ricalcoli successivi, non una modifica in massa nascosta; i due importi dello stesso booking rimangono quelli dello stesso ricalcolo.
- Quando apro report/CSV, allora il totale contabile e il saldo restano sul dovuto complessivo; la quota salvata spiega la conferma senza azzerare gli extra, e i provider non entrano negli incassi.
- Quando confronto prima/dopo la transizione, allora la somma dei pagamenti validi e degli annullati, rimborsi registrati e collegamenti personali è invariata; le differenze di dovuto/saldo sono tutte nell'anteprima e nell'audit.
- Quando considero edizioni non attive o booking chiusi, allora non ricostruisco prezzi storici che il database non conserva e non li aggiorno con le tariffe correnti.

## Domande aperte e revisione

Non resta una domanda sulla formula o sul ricalcolo di attivazione: entrambi sono confermati. Le proposte su quota zero, residuo operativo e prezzi ai ricalcoli sono rese concrete nel [design](design.md), per la revisione complessiva della spec. Gli aspetti di inclusioni, esenzioni e archivio appartengono ai rispettivi MVP e non bloccano il 18.
