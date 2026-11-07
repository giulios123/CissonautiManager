# MVP 17 · Consensi separati e riservatezza · Requisiti

**Stato:** spec esecutiva proposta il 7 novembre 2026; nessun codice implementato. Richiesta corrente: preparare insieme le spec 17 e 18. Fonti: [gruppo A](../revisione-2026-11-07/a-iscrizione-privacy/requirements.md), decisioni D-051/D-052/D-076/D-082/D-104 in `memory-bank/decisions.md`. Le scelte già confermate non vengono riaperte.

## Controllo B0 e confini

L'MVP 16 risulta implementato e ha tutti i task spuntati. Il maintainer conferma superate le prove SQL; resta documentata la prova visiva. Questo è B1: la preparazione congiunta delle due spec è stata richiesta esplicitamente; il 18 viene sviluppato sullo schema del 17.

Dentro: A1–A3, due finalità facoltative, prove versionate per persona/edizione, revisione autenticata, testi legali IT/EN della stessa versione e conservazione dei dati legacy. Fuori: campi A4, riaccettazione/privacy email A5 (MVP 20), storico cancellazioni A6 (21), proposte altrui E3 (27), vetrine/elenco partecipanti, foto/video o loro pubblicazione, supporto operativo delle edizioni F e calendario accantonato. Job title/LinkedIn saranno usati solo quando disponibili, senza aggiungere quei campi in anticipo.

## US-17-1 · Scelte comprensibili e indipendenti

Come partecipante voglio scegliere separatamente la visibilità della mia presenza e il trattamento foto/video.

- Quando apro la registrazione, allora privacy e scarico restano obbligatori e distinti dalle caselle facoltative «Visibilità della presenza nell'area riservata» e «Foto e video», entrambe inizialmente vuote.
- Quando rifiuto una o entrambe le finalità facoltative, allora posso iscrivermi o entrare soltanto in lista d'attesa, senza condizioni diverse su posto, quota o pagamento.
- Quando un testo facoltativo non è ancora pubblicato in IT/EN, allora quella scelta è indisponibile con spiegazione, non viene raccolto un sì e il resto dell'iscrizione continua secondo le regole attuali.
- Quando cambio lingua, allora leggo il corpo IT/EN della stessa versione e conservo dati e giorni selezionati; la prova registra la lingua effettivamente mostrata, non quella dedotta in seguito dal profilo.
- Quando invio una versione superata o un documento di un'altra edizione/finalità, allora ricevo un errore senza iscrizione o prove parziali; posso rivedere il testo mantenendo il resto del modulo. Un cambiamento del testo non seleziona automaticamente la casella.

## US-17-2 · Salvare una prova senza dipendere dal booking

- Quando una persona nuova conclude una registrazione valida, allora viene salvato un evento per ogni scelta facoltativa presentata, con finalità, scelta, documento/versione, lingua, persona, edizione e istante UTC del server.
- Quando entra soltanto in lista, o in più liste, allora valgono le stesse prove una volta per finalità, non una volta per slot; la promozione non inventa o copia un nuovo consenso.
- Quando il modulo fallisce per capienza, versione o concorrenza, allora non resta alcun evento riferito a una registrazione fallita.
- Quando manca una scelta storica, allora risulta **non espresso**, distinto da un rifiuto; la migrazione non crea sì, no o date fittizie.
- Quando una prenotazione è rimossa dal flusso esistente, allora gli eventi facoltativi non vengono cancellati insieme a essa. Questo non implementa la nuova cronologia A6 né un archivio eterno: la conservazione rimane soggetta alla policy F.

## US-17-3 · Gestire le proprie scelte dopo login

- Quando entro nella mia pagina, anche se sono soltanto in lista o senza booking corrente, allora vedo le mie due scelte nell'edizione cui risulto associato e i testi pertinenti; gli iscritti precedenti possono rispondere senza perdere iscrizione o versamenti.
- Quando concedo, nego o revoco una finalità, allora si aggiunge una prova e l'altra finalità resta invariata; il sistema non sostituisce l'evento precedente.
- Quando revoco, allora non devo prima accettare una nuova versione: la revoca resta possibile anche se è stato pubblicato un testo nuovo. Non viene promesso il ritiro automatico di media da terzi.
- Quando ripeto lo stesso salvataggio sulla stessa scelta/versione, allora non ottengo eventi duplicati; una modifica concorrente diversa richiede di rileggere lo stato invece di sovrascriverlo silenziosamente.
- Quando viene pubblicata una nuova versione facoltativa, allora la prova precedente resta consultabile e non autorizza nuovi usi della versione cambiata; per concedere la nuova finalità/testo occorre un nuovo sì. Nessuna nuova accettazione della privacy generale o email viene avviata dal 17.

## US-17-4 · Proteggere identità e autorità della scelta

- Quando un visitatore cerca nomi, invitanti o profili nel modulo o nelle API pubbliche, allora non trova elenchi, autocomplete nominali o nuove letture dei dati degli iscritti; «chi ti ha invitato» resta testo libero verificato dall'admin.
- Quando reinvio il modulo con un'email già attiva o in lista, allora resta l'esito attuale `already_registered` con link email, senza alterare dati o scelte esistenti.
- Quando un account esiste già ma può effettuare una nuova registrazione pubblica, allora i consensi facoltativi preesistenti non sono modificati neppure da un sì/no nel modulo anonimo: il proprietario li gestisce dopo login. La ricevuta non restituisce dati personali già memorizzati sull'account.
- Quando una sessione tenta di leggere o scrivere i consensi di un'altra persona, allora l'API nega l'operazione; un admin può leggere per la gestione dell'evento ma non concedere consensi in nome della persona.
- Quando una futura funzione usa il nome, allora deve verificare consenso vigente per persona, edizione e testo/finalità: nessun booleano globale, endpoint nominativo pubblico o autorizzazione cross-edizione viene introdotto dal 17.

## US-17-5 · Pubblicare testi IT/EN senza riscrivere lo storico

- Quando l'admin pubblica un nuovo testo legale, allora fornisce IT ed EN insieme e viene creata **una** versione; la pubblicazione concorrente è serializzata e non riusa un numero.
- Quando la versione era già stata accettata, allora i suoi corpi restano immutabili; una correzione richiede una nuova versione.
- Quando un documento legacy ha soltanto il corpo originale, allora lo mantengo e lo mostro come testo originale, senza dichiararlo tradotto o ricostruire la lingua delle vecchie accettazioni.
- Quando manca la traduzione di un vecchio testo, allora non vengono chiuse automaticamente le iscrizioni già aperte o invalidate le prove; nuovi testi/modifiche richiedono entrambi i corpi. I nuovi consensi facoltativi, privi di legacy, richiedono sempre IT/EN per essere disponibili.
- Quando le prove sono consultate, allora contengono solo dati necessari, senza allergie, fingerprint del dispositivo o copie del profilo nel registro.

## US-17-6 · Rilascio e verifiche

- Quando la migrazione è applicata a un database esistente, allora prenotazioni, slot, liste, pagamenti, prove obbligatorie e consensi sanitari rimangono invariati.
- Quando il 17 è rilasciato, allora interfaccia, errori e guida pertinente sono IT/EN e il form resta usabile su telefono, tastiera e iframe.
- Quando si valuta la prontezza prima dell'apertura, allora si distingue il meccanismo funzionante dai **testi definitivi ancora da pubblicare**; nessun testo di bozza viene pubblicato automaticamente.

## Domande e materiale aperto

1. Servono i corpi legali definitivi IT/EN per presenza e foto/video e il riferimento di chi li valida, compresi finalità/destinatari dei media. [copy.md](copy.md) contiene etichette e microtesti proposti, non un'informativa completa inventata.
2. Le proposte tecniche del [design](design.md) sono sottoposte alla revisione della spec; non sono nuove domande su visibilità autenticata, facoltatività o risposta per email nota, già confermate.

L'assenza dei testi definitivi non impedisce di sviluppare con dati di test, ma impedisce di considerarli pronti alla raccolta/pubblicazione in produzione. Per approvare lo sviluppo si rivede il perimetro sopra; non si aspetta la soluzione di tutte le questioni A–F.
