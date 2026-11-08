# Regole di dominio

> **Fonte di verità.** Se una spec contraddice questo file, vince questo file finché non viene aggiornato con il consenso del maintainer. Le modifiche si propongono nella sezione "Modifiche a domain.md" della spec.

> **Revisione del 7 novembre 2026:** decisioni iniziali D-050–D-075 e risposte prevalenti D-076–D-104 sono in [decisions.md](decisions.md); le [spec aggiornate](../specs/revisione-2026-11-07/README.md) indicano dove cambieranno queste regole. La regola approvata dell'MVP 18 è riportata in fondo a questo file; si applica solo alle edizioni per cui l'admin completa l'attivazione esplicita.

## Edizione, giorni e slot

- Un'edizione ha date configurabili dall'admin (non ancora definite).
- Ogni giorno ha tre slot: mattina, pomeriggio e sera, con orari configurabili (default 9-13, 14-18 e 19-24).
- Capienza per slot configurabile, default 25, per mattina e pomeriggio. Lo slot serale non ha limite di capienza.
- Il partecipante sceglie qualsiasi combinazione di slot, anche su giorni non contigui.

## Stati della prenotazione

`in_attesa_pagamento` → `confermata` · `scaduta` · `disdetta_richiesta` → `rimborsata`

- L'iscrizione crea una prenotazione `in_attesa_pagamento` che occupa i posti per N giorni (impostazione configurabile).
- Senza copertura della soglia di conferma entro la scadenza diventa `scaduta` e i posti si liberano. La scadenza si valuta al momento della lettura; il passaggio del posto liberato al primo in lista d'attesa avviene con il job orario, quindi entro un'ora.
- Diventa `confermata` quando i pagamenti attivi coprono la soglia della policy: totale dovuto con `legacy_total`, quota di partecipazione con `registration_fee`.
- Rimborso: l'admin segna come `rimborsata` una disdetta richiesta registrando importo (mai oltre quanto versato), data e nota. Non parte nessuna email: scrive lui alla persona.
- Disdetta: il partecipante la richiede dalla pagina personale, i posti si liberano subito, l'admin rimborsa fuori dal sistema, la segna come `rimborsata` e scrive al partecipante. Se non c'è alcun pagamento registrato la prenotazione viene semplicemente rimossa, senza passaggio dall'admin. Ogni nuova disdetta lascia una traccia consultabile dagli admin anche dopo la rimozione, con persona, edizione, data, autore effettivo ed esito. Lo storico dedicato parte dal rilascio della funzione; il criterio di conservazione va definito prima del rilascio in produzione.
- Modifica degli slot: il partecipante può aggiungere e togliere slot finché la prenotazione è `in_attesa_pagamento` o `confermata` (almeno uno slot resta). L'importo si ricalcola e la scadenza del blocco non cambia. Una prenotazione `confermata` resta tale: il saldo mostra la differenza da versare o il credito. Una `in_attesa_pagamento` diventa confermata se i pagamenti coprono la soglia prevista dalla policy attiva. Gli slot di giorni già trascorsi (Europe/Rome) non si aggiungono né si tolgono dalla pagina personale: solo l'admin può cambiarli.

## Lista d'attesa

- Quando uno slot è pieno si entra in lista d'attesa per quello slot, dal modulo pubblico o dalla pagina personale. Dal modulo ci si può iscrivere anche con soli slot pieni: la persona è registrata senza prenotazione e i testi legali accettati restano salvati sulla voce in lista.
- Dimensione massima: capienza × percentuale (default 20%, configurabile), arrotondato per difetto. La sera, senza limite di posti, non ha lista.
- Quando si libera un posto (disdetta, slot tolto, aumento di capienza, scadenza), il primo +1 verificato in lista, poi gli altri per ordine di arrivo, riceve lo slot e un'email:
  - prenotazione `in_attesa_pagamento`: lo slot si aggiunge, l'importo si ricalcola e la scadenza diventa la più lontana tra quella attuale e N giorni da ora;
  - prenotazione `confermata`: lo slot si aggiunge e resta confermata, con la differenza nel saldo (come per il cambio degli slot);
  - nessuna prenotazione attiva: ne nasce una nuova `in_attesa_pagamento` con blocco di N giorni.
- Il +1 è chi ha indicato chi l'ha invitato («chi ti ha invitato?») e ha il legame confermato da un admin con una spunta, dalla scheda o da «Giorni e slot». La priorità cambia l'ordine, non il limite della lista: con la lista piena nemmeno un +1 entra. Tra +1 vale l'ordine di arrivo. Se «chi ti ha invitato?» viene svuotato, la verifica cade. Chi scende di posizione non riceve avvisi.
- Chi disdice esce anche dalle liste d'attesa. Chi prenota da sé uno slot per cui aspettava esce da quella lista. I giorni passati non promuovono nessuno.

## Importi

- Quota di partecipazione: quota base + importo per ogni giorno con almeno uno slot prenotato, sera compresa (un giorno con la sola sera conta, per ora). Default 10 € + 1 €/giorno, configurabili.
- Pranzi e cene: adesione per singolo giorno, due prezzi flat configurabili (uno per il pranzo, uno per la cena). Per il pranzo serve almeno uno slot di giorno (mattina o pomeriggio); per la cena la presenza serale, e chi prenota l'intero giorno (mattina e pomeriggio) conta anche per la sera. L'adesione ai pasti non avviene all'iscrizione: si fa dopo, dalla pagina personale, e si può cambiare con le stesse regole degli slot (giorni passati solo l'admin). Togliere uno slot fa cadere i pasti a cui non si ha più titolo, con ricalcolo dell'importo.
- Totale dovuto = quota di partecipazione + pasti e attività incassati dagli organizzatori, ai prezzi correnti. I costi pagati direttamente all’erogatore restano visibili con istruzioni e destinatario ma non contano nel saldo, nei solleciti e negli incassi.
- Attività: create dall'admin, gratuite o a pagamento, capienza opzionale. Ogni attività ha un giorno e una fascia (mattina, pomeriggio, sera): può aderire solo chi è presente in quella fascia, sera derivata compresa. Con persone già iscritte non cambiano giorno e fascia, la capienza non scende sotto gli iscritti e l'attività non si elimina. Togliere uno slot fa cadere le attività a cui non si ha più titolo; alla riattivazione di una prenotazione scaduta cadono quelle nel frattempo piene. L'admin può superare la capienza con una conferma esplicita.
- Contributi: dalla pagina personale si propongono talk, temi per l'unconference e competenze, più di uno per persona; sono legati all'iscrizione dell'edizione.
- Saldo del partecipante = totale dovuto meno pagamenti registrati.

## Pagamenti

- Nessuna integrazione: Revolut, Satispay, PayPal, IBAN. Istruzioni per canale configurabili dall'admin.
- Causale generata dal sistema con un codice personale (es. `CSC-7K3P`). Il codice serve solo come causale, mai per accedere.
- L'admin registra un pagamento (importo, canale, data, nota) con un clic dalla scheda del partecipante.
- Dalla vista «da incassare» l'admin registra in un clic il saldo intero, sul canale scelto e con la data di oggi; l'importo diverso si registra dalla scheda. Per 10 secondi può annullare subito, e in questo caso l'email di conferma parte dopo 30 secondi (dalla scheda parte subito): un annullo entro i 10 secondi non la fa partire, dopo i 30 secondi non si ritira.
- Un pagamento registrato per errore non si cancella: si annulla scrivendo un motivo. Resta in elenco, barrato, e non conta più nel saldo. Se la prenotazione era `confermata` e non è più coperta la soglia della policy attiva, torna `in_attesa_pagamento` con un nuovo blocco.

## Accesso

- Pagina pubblica di iscrizione senza login, incorporabile in Google Sites tramite iframe: header CSP `frame-ancestors` che autorizza `https://sites.google.com` e `https://*.googleusercontent.com`. Dopo l'invio mostra il riepilogo economico secondo la policy e invia un'email con il magic link; istruzioni di pagamento e scadenza compaiono quando la prenotazione è in attesa.
- Magic link: token valido 10 minuti e riusabile in quel tempo (gli scanner di posta che aprono il link prima della persona non lo bruciano); aprendolo si entra subito, senza altri clic, nella pagina personale in una finestra normale (fuori dall'iframe). Dopo il login tutti, admin compresi, arrivano alla propria pagina personale; gli admin hanno lì il link al pannello. Dopo il login un cookie di sessione httpOnly, Secure, SameSite=Lax dura 14 giorni. Chi non ha un cookie valido può richiedere un nuovo link inserendo l'email.
- Password (opzionale): oltre al magic link si può accedere con email e password. La password si imposta dalla pagina personale dopo un accesso con magic link; il magic link resta sempre disponibile come recupero.
- Lingue: l'app è in italiano e in inglese. La lingua si sceglie con il selettore IT/EN (o con `?lang=`), altrimenti è quella del browser; si salva sul partecipante alla registrazione e a ogni cambio da loggato. Gli indirizzi sono in inglese (`/register`, `/login`, `/me`...): gli indirizzi italiani scritti a mano reindirizzano.
- Pagina personale: modifica degli slot, adesione a pranzi, cene e attività, esigenze alimentari, contributi offerti (talk, temi per l'unconference, competenze), saldo e istruzioni di pagamento, richiesta di disdetta.
- Admin: stessa app, ruolo `admin`. Gli admin si aggiungono e rimuovono dal pannello, senza limite di numero. Il primo admin viene creato da variabile d'ambiente e non si rimuove dal pannello (si cambia da lì); non si può rimuovere se stessi né l'ultimo admin.

## Dati e privacy

- Contatti riutilizzabili: nome, cognome, email, telefono (obbligatorio nei nuovi invii, anche solo in lista d’attesa), Telegram e LinkedIn. Un profilo social assente si dichiara esplicitamente; il vuoto indica dato mancante.
- Per ogni nuova iscrizione, anche solo in lista d’attesa, si raccolgono città/paese, professione, azienda (si può rispondere «Nessuna azienda»), aspettative e partecipazione all’edizione precedente. Le risposte appartengono alla persona e all’edizione; i profili legacy restano mancanti fino a risposta esplicita.
- Quando una prenotazione confermata dimostra la partecipazione all’edizione cronologicamente precedente, il sistema registra «sì» come dato derivato. Senza questa prova chiede la dichiarazione sì/no; l'assenza di storico non è un «no».
- Comune italiano, provincia e codice ISTAT sono scelti da un catalogo locale. Per estero o comune non censito la città è libera; il fallback italiano richiede provincia dichiarata e non assegna automaticamente la regione.
- Account esistenti non si aggiornano da invii anonimi. Dopo login, il richiamo persistente consente di completare i dati senza bloccare consultazione o modifiche di prenotazioni, lista d'attesa, pagamenti, consensi e disdetta. Il completamento non trasferisce né modifica consensi.
- Campi aggiuntivi del modulo pubblico: "chi ti ha invitato?" (testo libero, opzionale), "cosa puoi portare al camp?" (testo libero).
- Checkbox obbligatorie in iscrizione: informativa privacy e accettazione dello scarico di responsabilità. Entrambi i testi sono configurabili dall'admin e la versione accettata viene salvata con data e ora. La prova privacy è riferita a persona, edizione e documento; resta consultabile anche senza una prenotazione attiva. Una nuova versione richiede una scelta esplicita autenticata. La reiscrizione pubblica di un account già esistente non vale come nuova accettazione.
- Se la nuova informativa è pendente, la persona può leggere, pagare importi già dovuti, gestire e revocare consensi facoltativi, aggiornare i dati alimentari, lasciare la lista d'attesa, cambiare password o lingua e disdire. Non può modificare presenze, aggiungere un'iscrizione in lista d'attesa, cambiare pasti o attività né modificare i contributi offerti. Le azioni admin restano disponibili e non registrano accettazioni per conto della persona.
- Esigenze alimentari: il regime (onnivoro, vegetariano, vegano) si salva senza consenso. Allergie e intolleranze sono dati sanitari: si salvano solo con un consenso specifico, il cui testo è configurabile dall'admin e versionato (si salvano versione, data e ora); togliere il consenso le cancella. Le vedono solo la persona e gli admin, mai nelle email. Stanno sulla prenotazione e spariscono con essa.

## Pannello admin

- Impostazioni: date, slot e orari, testo e immagine della email di iscrizione (con anteprima e invio di prova), capienze, giorni di blocco, percentuale della lista d'attesa, quote, prezzi di pranzo e cena, canali e istruzioni di pagamento, testo sopra il modulo di iscrizione e testo delle altre email (per lingua), testi legali (compreso il consenso per i dati sanitari), gestione degli admin.
- Lingue del pannello: tutto il pannello è in italiano e inglese. I CSV escono nella lingua dell'app al momento del download, con lo stesso formato (separatore `;`, virgola decimale, date `gg/mm/aaaa`, ora di Roma). Le voci della cronologia restano nella lingua in cui furono scritte.
- Viste: per persona, per giorno e slot, per attività, settimana aggregata (coworking, pranzi, cene, attività), esigenze alimentari per pasto, pagamenti da incassare (iscrizioni in attesa o con un saldo da versare, con ricerca per causale), pagamenti da verificare, report di riepilogo dell'edizione (iscrizioni, presenze, pasti, attività, contributi, lista d'attesa, incassi, con confermate e in attesa di pagamento separate; le allergie solo come numero; anche in stampa). Export CSV per ogni vista. La presenza serale di chi ha prenotato l'intero giorno è derivata (D-009) e nelle viste è indicata come tale.
- L'admin può modificare a mano qualsiasi iscrizione, comprese le disdette che il partecipante non riesce a fare. Può superare la capienza di uno slot solo con una conferma esplicita.
- Ogni modifica manuale dell'admin è registrata (chi, quando, cosa) e compare nella cronologia della scheda.

## Email

Ogni email parte nella lingua del partecipante (italiano o inglese). La conferma di iscrizione ha oggetto e testo iniziale modificabili dall'admin per ciascuna lingua (segnaposto: nome, cognome, evento, data di inizio e di fine); riepilogo economico, slot, eventuale causale, eventuali istruzioni e scadenza, link personale e frasi finali sono costruiti in base allo stato e alla policy e non si modificano dall'editor. Se l'admin ha caricato uno sfondo, la email contiene un'immagine con la frase «Sono nome cognome e sarò a evento dal … al …» (in inglese «I'm … and I'll be at … from … to …»), modificabile per lingua con colore e posizione; non la riceve chi è solo in lista d'attesa.

Quando la privacy corrente è pendente per una prenotazione attiva o una lista d'attesa aperta, il job orario invia un solo link al login per persona, edizione e versione. Il tentativo si registra prima dell'invio e non viene ripetuto automaticamente; aprire il link non costituisce accettazione.

Il nome dell'edizione compare nell'intestazione, nel titolo delle pagine e negli oggetti delle email. Anche delle altre email (lista d'attesa, già iscritto, link di accesso, pagamento ricevuto, i due promemoria, posto liberato, disdetta) l'admin modifica oggetto e testo iniziale per ciascuna lingua, con gli stessi segnaposto; la parte con i dati (slot, quota, causale, scadenza, istruzioni di pagamento, link e frasi finali) è sempre automatica. Vuoto = testo standard. Il paragrafo sopra il modulo di iscrizione si modifica allo stesso modo, per lingua.

Conferma iscrizione con magic link (o di ingresso in lista d'attesa) · conferma pagamento · due promemoria per le prenotazioni in attesa (a metà del blocco e 24 ore prima della scadenza, ciascuno una sola volta per blocco; con un blocco sotto le 48 ore parte solo quello a metà; ripartono se la prenotazione viene riattivata) · posto liberato dalla lista d'attesa · conferma disdetta. Nessun altro sollecito. Con `registration_fee`, i promemoria riguardano il residuo necessario a coprire la quota e non gli extra di una prenotazione confermata.

## Fuori scope

Pagamenti integrati, app native, menu personalizzati, più edizioni contemporanee (il modello prevede comunque l'entità `Edition`).

## Questioni aperte

Importi definitivi, aspetti legali (in attesa di parere), meccanismo dell'unconference, eventuali prelazioni per chi ha già partecipato.

## Pagamenti diretti e orari (MVP 16, approvato)

- Attività con inizio e fine selezionabili nella fascia scelta, interpretati in Europe/Rome e salvati in UTC; mezzanotte chiude il giorno. I testi orari precedenti restano leggibili fino alla conversione.
- Singoli pranzi e cene delegabili per data, con costo specifico e istruzioni; gli altri usano i prezzi generali. Le adesioni restano nell’app.
- Prezzi e destinatari di attività e pasti sono modificabili anche con iscritti. Il ricalcolo atomico delle sole prenotazioni attive interessate conserva versamenti e scadenze: eccedenze a credito, confermate sempre confermate, in attesa confermate se coperte. Scadute e chiuse non si riattivano. Nessun rimborso automatico o tracciamento di pagamenti all’erogatore.

## Conferma con la sola quota (MVP 18, approvato)

- La regola si configura per edizione e resta `legacy_total` finché un admin non ricalcola un'anteprima e applica esplicitamente il risultato. Distribuire il codice o aggiungere la migrazione non attiva la regola.
- Con `registration_fee`, la soglia per confermare è la quota di partecipazione: quota base più una quota per ciascun giorno scelto. Pasti e attività incassati dall'organizzazione concorrono al totale dovuto, ma non alla soglia di conferma; le voci pagate direttamente al fornitore non entrano negli incassi o nei costi dell'organizzazione e restano solo un promemoria/istruzione per la persona.
- I pagamenti registrati restano nel loro importo effettivo. La prenotazione in attesa si conferma quando i versamenti attivi raggiungono la quota; la ricevuta riporta l'importo appena registrato, il totale dell'organizzazione e l'eventuale saldo residuo, senza dichiarare saldato il totale. Una prenotazione confermata con soli extra dovuti non torna in attesa per l'aggiunta di slot, pasti o attività. Se l'annullamento di un pagamento porta i versamenti sotto la quota, torna in attesa secondo le regole di blocco. Quota zero conferma senza creare un pagamento fittizio.
- Scadenze di blocco e promemoria riguardano solo le prenotazioni in attesa e il residuo per raggiungere la quota. Una confermata con saldo dovuto solo per pasti o attività non riceve una scadenza per perdere il posto né un promemoria di conferma; gli extra restano visibili negli incassi. I percorsi di lista d'attesa rispettano la stessa soglia.
- L'anteprima admin ricalcola i prezzi correnti per le prenotazioni attive in attesa o confermate; scadute, chiuse e sole voci di lista sono escluse. Prima di applicare mostra quota, totale, versato, saldo/credito e stato prima/dopo. L'applicazione cambia i due importi dovuti secondo l'anteprima senza modificare pagamenti o rimborsi; una conferma risultante dall'applicazione non inventa un incasso e produce la notifica di conferma prevista. Un cambiamento intervenuto dopo l'anteprima richiede un nuovo calcolo.
- Report, CSV, pagina personale e viste admin continuano a mostrare il totale dovuto all'organizzazione e il saldo complessivo, distinguendoli dalla quota richiesta per confermare. I costi dei fornitori non entrano in entrambi i totali dell'organizzazione.
