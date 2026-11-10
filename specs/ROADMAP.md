# Roadmap

MVP piccoli e successivi. Ogni MVP ha la sua cartella `specs/mvp-NN-<slug>/` creata nella fase B1. Lo stato aggiornato è in `memory-bank/progress.md`.

## MVP 1 · Iscrizione base

- **Obiettivo**: raccogliere iscrizioni vere con posto bloccato fino al pagamento, e far registrare i pagamenti agli organizzatori.
- **Contenuto**: scheletro dell'app, DB e migrazioni, impostazioni essenziali dell'edizione gestite da un admin seed, pagina pubblica di iscrizione incorporabile, calcolo dell'importo, blocco di N giorni, magic link con email in console, admin che vede le iscrizioni e registra i pagamenti, deploy su Azure.
- **Fatto quando**: su Azure una persona si iscrive dall'iframe di Google Sites, vede importo, causale, istruzioni e scadenza; l'admin vede l'iscrizione, registra il pagamento e la prenotazione diventa `confermata`; una prenotazione non pagata risulta `scaduta` dopo la scadenza e libera i posti.

## MVP 2 · Pagina personale

- **Obiettivo**: rendere il partecipante autonomo dopo l'iscrizione.
- **Contenuto**: login con magic link e cookie da 14 giorni, modifica degli slot, saldo e istruzioni, richiesta di disdetta, email reali (Azure Communication Services) e due promemoria di pagamento (a metà blocco e 24 ore prima della scadenza).
- **Fatto quando**: un partecipante riceve una vera email, entra nella pagina personale, cambia i suoi slot con l'importo ricalcolato, vede il saldo, richiede la disdetta liberando i posti; ogni promemoria parte una sola volta.

## MVP 3 · Pannello admin completo

- **Obiettivo**: la vista "come un Excel navigabile" per gli organizzatori.
- **Contenuto**: viste per persona, per giorno e slot, per settimana aggregata, pagamenti da verificare; export CSV per ogni vista; gestione degli admin; rimborsi; modifica manuale di qualsiasi iscrizione.
- **Fatto quando**: un admin sa dire quante persone ci sono in ogni slot, scarica il CSV, aggiunge o rimuove un altro admin, segna una disdetta come `rimborsata` e corregge a mano un'iscrizione.

## MVP 4 · Lista d'attesa

- **Obiettivo**: non perdere chi trova uno slot pieno.
- **Contenuto**: iscrizione in lista d'attesa per slot pieno, limite percentuale configurabile (default 20%), promozione automatica del primo in lista con email e blocco di N giorni.
- **Fatto quando**: con uno slot pieno ci si iscrive in lista fino al limite; liberando un posto il primo in lista riceve email e blocco con le stesse regole di pagamento.

## MVP 5 · Pranzi e cene

- **Obiettivo**: sapere quanti mangiano e cosa possono mangiare.
- **Contenuto**: adesione per giorno a pranzi e cene dalla pagina personale (dopo l'iscrizione, modificabile; la presenza serale abilita la cena), prezzo flat per pasto, esigenze alimentari con consenso specifico visibili solo agli admin, vista per pasto con export.
- **Fatto quando**: il partecipante aderisce ai pasti e l'importo si aggiorna; l'admin vede per ogni pasto numero di persone ed esigenze alimentari; senza consenso le allergie non si salvano.

## MVP 6 · Attività e contributi

- **Obiettivo**: organizzare attività e raccogliere proposte per l'unconference.
- **Contenuto**: attività create dall'admin, gratuite o a pagamento, con capienza opzionale; adesione dalla pagina personale; contributi offerti (talk, temi, competenze); vista per attività con export.
- **Fatto quando**: l'admin crea un'attività a pagamento con capienza, i partecipanti aderiscono fino al limite, l'importo si aggiorna e i contributi compaiono in una vista dedicata.

## MVP 7 · Inviti e report

- **Obiettivo**: gestire i +1 e chiudere l'edizione con i numeri.
- **Contenuto**: priorità in lista d'attesa a chi è stato invitato (il +1), con il legame verificato dall'admin (resta il campo testuale «chi ti ha invitato?», già presente); report di riepilogo dell'edizione.
- **Fatto quando**: un +1 verificato passa davanti in lista d'attesa e l'admin genera il report di riepilogo (presenze, pasti, attività, incassi) a video, in stampa e in CSV.

## MVP 8 · Stile del sito

- **Obiettivo**: far sembrare l'app parte del sito Cissone Eventi (https://sites.google.com/view/cissoneeventi/welcome), che ospita l'iframe di iscrizione.
- **Contenuto**: colori, font, logo e componenti ripresi dal sito su tutte le pagine; modalità iframe senza intestazione doppia; font self-hosted; accessibilità invariata.
- **Fatto quando**: dentro il sito il modulo di iscrizione sembra parte della pagina, login, pagina personale e pannello admin hanno lo stesso stile e i contrasti restano AA.

## MVP 9 · Guida in app e note di rilascio

- **Obiettivo**: spiegare le funzioni dentro l'app, per ruolo, e tenere la spiegazione allineata a ogni deploy.
- **Contenuto**: pagina «Guida» dopo il login (partecipante: sua guida; admin: guida organizzatori, guida partecipanti e «Novità»), versione in pagina, note di rilascio generate dai commit al deploy, regola in `AGENTS.md` e controllo CI.
- **Fatto quando**: un partecipante vede solo la sua guida, un admin vede anche organizzatori e novità del deploy, e una PR che cambia pagine senza toccare la guida fallisce in CI.

## MVP 10 · Incassi (controllo del conto)

- **Obiettivo**: far controllare il conto e segnare le quote incassate in fila, da una sola pagina.
- **Contenuto**: pagina «Da incassare» con le iscrizioni in attesa o con un saldo da versare, ricerca per nome, email e causale, canale scelto una volta, tasto «Segna pagato» che registra il saldo, annullo immediato per 10 secondi, email di conferma differita di 30 secondi (con rete di sicurezza nel job orario), link alla scheda per importi diversi. Una migrazione.
- **Fatto quando**: dall'elenco un admin cerca la causale di un bonifico, segna il pagamento in un clic, l'iscrizione diventa `confermata` e parte l'email; un clic sbagliato si annulla entro 10 secondi, la prenotazione torna in attesa e l'email non parte.

## MVP 11 · Lingue e indirizzi

- **Obiettivo**: app in italiano e inglese, indirizzi in inglese con alias italiani che reindirizzano.
- **Contenuto**: rotte in `routes.ts`, i18n con dizionari tipizzati, selettore IT/EN, lingua salvata sul partecipante, errori ed email nella sua lingua, pagine e guida del partecipante tradotte. Una migrazione.
- **Fatto quando**: `/iscrizione` porta a `/register`, un vecchio magic link funziona, una persona si iscrive in inglese e riceve le email in inglese.

## MVP 12 · Pannello admin in inglese

- **Obiettivo**: il pannello degli organizzatori nelle due lingue.
- **Contenuto**: viste, scheda e impostazioni tradotte, CSV per lingua, guida organizzatori in inglese con test di parità.
- **Fatto quando**: un admin usa tutto il pannello in inglese e scarica un CSV con intestazioni inglesi.

## MVP 13 · Email di iscrizione personalizzabile

- **Obiettivo**: testo della conferma modificabile e immagine con nome, evento e date.
- **Contenuto**: testi per lingua con segnaposto, sfondo caricato dall'admin, card PNG generata con Pillow e inline nella mail HTML, anteprima e invio di prova. Una migrazione.
- **Fatto quando**: l'admin carica uno sfondo, scrive il testo, vede l'anteprima e una nuova iscrizione riceve la mail con «I'm Nome Cognome and I'll be at ...».

## MVP 14 · Testi dell'evento e accesso diretto

- **Obiettivo**: nome dell'edizione ovunque, testi delle email e del modulo modificabili, accesso più diretto.
- **Contenuto**: nome dell'edizione in intestazione, titolo delle pagine e oggetti delle email; oggetto e testo iniziale delle altre 8 email (per lingua, con i segnaposto dell'MVP 13) e testo sopra il modulo (per lingua) dalle Impostazioni; dopo il login sempre la pagina personale con il link al pannello; magic link riusabile 10 minuti e senza pagina «Entra». Una migrazione.
- **Fatto quando**: l'admin cambia un testo e lo trova nella prossima email e nel modulo, un admin entra sulla sua pagina, un link di accesso si apre senza clic.

## MVP 15 · Riepiloghi compatti delle presenze

- **Obiettivo**: rendere leggibili presenze, importi e scadenze durante l'iscrizione, sulla pagina personale e nelle email.
- **Contenuto**: righe per giorno condivise tra interfaccia ed email; fasce mostrate solo per giornate parziali; legenda unica degli orari; lista d'attesa separata; riepilogo responsive in italiano e inglese.
- **Fatto quando**: cinque giorni pieni occupano cinque righe; mattina+pomeriggio equivalgono a giornata piena; riepilogo, conferma e email mostrano gli stessi giorni, fasce e orari.

## MVP 16 · Orari, telefono e pagamenti diretti

- **Obiettivo**: scegliere gli orari delle attività, raccogliere il telefono e distinguere gli incassi degli organizzatori dai pagamenti all’erogatore.
- **Contenuto**: intervalli orari da menu, telefono obbligatorio, modalità di incasso per attività e singolo pasto con costo e istruzioni; ricalcolo anche dopo le adesioni; report, CSV e guida bilingue. Migrazione 0015.
- **Fatto quando**: le adesioni esterne restano nell’app ma non aumentano il saldo agli organizzatori; i cambi di costo/destinatario ricalcolano le prenotazioni attive interessate conservando versamenti e crediti.

## MVP 17 · Consensi separati e riservatezza

Sequenza condivisa con il 18: [piano operativo](piano-mvp-17-18.md), 17 prima e 18 sulla sua base, senza checklist duplicate.

- **Stato:** [spec esecutiva pronta per revisione](mvp-17-consensi-riservatezza/requirements.md), 8 task; nessuna implementazione.
- **Contenuto:** scelte presenza/media facoltative, eventi per persona/edizione, gestione autenticata, testi legali IT/EN e protezione degli account già noti; legacy preservato, A5/A6/E3 nei rispettivi rilasci.
- **Fatto quando:** form e sola lista registrano prove indipendenti, il proprietario cambia/revoca dopo login, nessuna nuova lettura nominale anonima o modifica di consensi altrui; testi definitivi distinti dai dati di prova.

## MVP 18 · Conferma con la sola quota

- **Stato:** [spec esecutiva pronta per revisione](mvp-18-conferma-quota/requirements.md), 10 task; preparata insieme al 17 su richiesta, nessuna implementazione.
- **Contenuto:** quota base+giorni separata dal totale, transizioni/notifiche/promemoria coerenti e attivazione admin con ricalcolo in anteprima confermato in D-105; nessuna inclusione/esenzione anticipata.
- **Fatto quando:** il pagamento della quota conferma anche con extra dovuti; preview/apply sono coerenti e idempotenti, confermate stabili e pagamenti intatti; codice distribuito e attivazione reale restano due passi distinti.

## MVP 20 · Nuova accettazione privacy

- **Stato:** implementato localmente su base MVP 17; spec e checklist in [mvp-20-riaccettazione-privacy](mvp-20-riaccettazione-privacy/requirements.md). L'MVP 19 resta indipendente.
- **Contenuto:** accettazione autenticata e versionata, blocco delle modifiche partecipante finché pendente, storico admin, migrazione delle prove legacy e richiesta email una tantum dal job orario.
- **T20-8 completata:** suite backend completa (1103 test in locale), migrazione SQL Server e collaudo organizzatori confermati dal maintainer. Prima dell'uso reale restano destinatari email e testi legali IT/EN definitivi. Nessun deploy o invio reale dichiarato.

## MVP 21 · Storico delle cancellazioni

- **Stato:** implementato sul branch `feat/mvp-21-storico-cancellazioni`; suite locale, migrazione SQL Server CI e collaudo manuale A6 confermati completati dal maintainer. Nessun deploy eseguito.
- **Contenuto:** registro amministrativo delle nuove disdette, consultabile dopo la rimozione della prenotazione, con autore, edizione, data ed esito; migrazione additiva e prova di accettazione esclusivamente manuale A6.
- **Conservazione:** un anno dalla cancellazione, pulizia automatica nel job orario; collaudo manuale A6 completato.

## MVP 22 · Altro importo da «Da incassare»

- **Stato:** implementato sullo stesso branch di lavoro; test SQLite, frontend, lint, build, migrazione SQL Server CI e collaudo manuale confermati completati dal maintainer. Nessun deploy eseguito.
- **Contenuto:** modale per registrare importi parziali, con controllo concorrente del saldo, retry idempotente, annullo entro 10 secondi ed email differita di 30 secondi.
- **Fatto quando:** un admin aggiorna il saldo dalla lista senza duplicare pagamenti, e il raggiungimento della quota conferma il posto secondo la policy 18 lasciando visibili gli extra dovuti.

## MVP 23 · Composizione della quota e destinatari

- **Stato:** implementato e integrato in `main` con PR #26 il 2026-11-09; suite backend (1130), frontend (409), lint, build, Guide e CI SQLite/SQL Server/immagine verdi. Resta il collaudo manuale organizzatori.
- **Contenuto:** primo pasto selezionato con incasso dell’organizzazione, applicato con anteprima dopo l’attivazione della conferma sulla sola quota; catalogo minimo benefit bilingue.

## MVP 24 · Dettagli e note delle attività

- **Stato:** implementato e integrato in `main` tramite PR #25; resta il collaudo manuale organizzatori.
- **Contenuto:** testi attività IT/EN con fallback legacy, schede localizzate e note admin con cronologia, protette nelle API e nei CSV.

## MVP 25a · Presenze esterne

- **Stato:** [implementato sul branch](mvp-25a-presenze-esterne/requirements.md) `feat/mvp-25a-presenze-esterne`, 9 task completati; restano CI SQL Server e collaudo organizzatori. Nessun deploy.
- **Contenuto:** esterni senza account inseriti dall'admin con identità minima, pasti e attività senza coworking, capienza delle attività occupata, regime e allergie (con consenso dichiarato), viste, CSV e report con la colonna «Esterni».
- **Fatto quando:** una persona conta una volta per voce, nessun account o prenotazione fittizi e importi invariati.

## MVP 25b · Incassi degli esterni

- **Stato:** [implementato sul branch](mvp-25b-incassi-esterni/requirements.md) `feat/mvp-25b-incassi-esterni` (sopra il 25a), 8 task completati; restano CI SQL Server e collaudo organizzatori. Nessun deploy.
- **Contenuto:** dovuto calcolato sulle sole voci incassate dall'organizzazione, registro di pagamenti e restituzioni separato dalle prenotazioni, sezione «Esterni» in «Da incassare», totale evento nel report.
- **Fatto quando:** i versamenti degli esterni sono distinti dalle quote ma sommati nel totale evento, senza doppi conteggi.

## MVP 25c · Esenzioni e rettifiche degli iscritti

- **Stato:** [integrato in `main`](mvp-25c-esenzioni-rettifiche/requirements.md) con la PR #28 (insieme a 25a e 25b), 9 task completati; migrazione 0026 sopra la 0025. Restano CI SQL Server e collaudo organizzatori. Nessun deploy.
- **Contenuto:** categoria «ordinaria / interno non pagante», esenzioni esplicite di quota e singole voci con anteprima e applicazione, rimborso tracciato su iscrizione attiva al massimo pari al credito, versato netto.
- **Fatto quando:** un'esenzione cambia solo le voci scelte, i pagamenti restano intatti e il rimborso non altera lo stato del posto.

## MVP 26 · Dettaglio dei numeri settimanali

- **Stato:** [implementato sul branch](mvp-26-dettaglio-settimana/requirements.md) `feat/mvp-26-dettaglio-settimana`, 6 task completati, nessuna migrazione. Restano CI SQL Server e collaudo organizzatori. Nessun deploy.
- **Contenuto:** ogni numero della vista settimanale (celle e totali) apre una modale admin con l'elenco che lo spiega: persone, pasti con esterni, adesioni alle attività; coerente con la tabella, solo admin, accessibile.
- **Fatto quando:** per ogni metrica il dettaglio ha tanti elementi quanto la cella e non espone dati sanitari né di contatto.

## MVP 27 · Proposte tra partecipanti

- **Stato:** [spec pronta](mvp-27-proposte-partecipanti/requirements.md), confermata, da implementare; 8 task, migrazione 0027.
- **Contenuto:** modale «Proposte degli altri» per iscritti attivi e admin, autore mostrato solo con consenso presenza, quarto tipo «Competenze che cerco», avviso sul testo libero e proposte nascondibili dall'admin (D-117, D-118).
- **Fatto quando:** senza consenso la proposta è anonima e il payload non contiene dati dell'autore.

## MVP 28 · Barra e recap più leggibili

- **Stato:** [spec pronta](mvp-28-barra-recap/requirements.md), confermata, da implementare; 4 task, solo CSS e test.
- **Contenuto:** barra superiore con fondo pieno e striscia d'enfasi, recap laterale con fondo bianco che scorre con la pagina.
- **Fatto quando:** importo e pulsante restano leggibili in alto (telefono, iframe, zoom 200%, inglese) e il recap non è sticky.

## Revisione dopo il collaudo del 7 novembre 2026

**Pianificazione aggiornata con le risposte del maintainer; nessun MVP avviato.** Il [dossier](revisione-2026-11-07/README.md) contiene spec A–E, valutazione F con stessa base dati scelta, proposta mappa A7 e riscontro promemoria D5. **Calendario D3 accantonato, mockup rimosso.** Decisioni canoniche D-050–D-075 e precisazioni D-076–D-104; [domande residue](revisione-2026-11-07/domande-aperte.md) limitate ai dettagli non risposti.

Il [piano 17–31](revisione-2026-11-07/mvp.md) parte da consensi/riservatezza (17) e conferma su quota base+giorni (18), entrambi P1; pacchetto 25 diviso in presenze esterne senza account (25a), incassi separati (25b), esenzioni e rettifiche degli iscritti (25c). B4 comprende pasti e soltanto benefit aggiuntivi; pagina consegne nel 30 con soglia quota base/interni non paganti. F ha obiettivo prima del prossimo evento se fattibile, in una futura spec separata; mappa e tratto.email restano ai livelli di bozza previsti. Nessun reset/deploy avviato.

## Backlog

Idee e questioni fuori dagli MVP correnti. Si aggiungono qui, non si implementano.

- Importi definitivi della quota e dei pasti.
- Testi legali definitivi (in attesa di parere).
- Meccanismo dell'unconference.
- Prelazione per chi ha già partecipato.
- Limite di richieste (rate limit) su richiesta del magic link e sul login con password, per evitare invii email ripetuti e tentativi a raffica.
- Canale "contanti/altro" per registrare pagamenti fuori dai quattro canali previsti.
- Se la quota giornaliera debba contare un giorno con la sola sera (per ora sì).
- Modifica manuale dell'importo dovuto da parte dell'admin (sconti, organizzatori gratis), emersa nella spec dell'MVP 3.
- Dominio proprio per le email (oggi dominio gestito Azure) se il recapito o i limiti di invio danno problemi.
- Passaggio dell'invio email a una coda se il volume cresce (oggi l'invio è sincrono dopo il commit).
- La pagina pubblica di iscrizione permette di scegliere anche giorni già passati: valutare se bloccarli durante l'evento (emerso nella prova dell'MVP 2).
- Avvisare con un'email il partecipante quando un admin cambia i suoi slot (oggi non parte nulla), emerso nell'MVP 3.
- Due admin che si rimuovono a vicenda nello stesso istante possono lasciare zero admin: serve un controllo con blocco se diventa un problema reale.
- Vista Persone senza paginazione: se le iscrizioni diventano molte, aggiungere pagine o scorrimento.
- Lista d'attesa per le attività piene (emersa nella spec dell'MVP 6).
- Annullare un'attività con iscritti togliendola a tutti e ricalcolando gli importi (MVP 6).
- Attività su più fasce o su tutto il giorno, come le escursioni (MVP 6).
- Capienza dei pasti o chiusura delle adesioni a un'ora fissa (MVP 5).
- Avviso a chi è in lista d'attesa quando la sua posizione cambia (MVP 4).
- Anteprima della quota calcolata dal server nei modificatori di pasti e attività: oggi l'anteprima parte dalla quota salvata e, se un admin cambia un prezzo con iscrizioni già presenti, può differire dall'importo che viene poi salvato (che è sempre giusto). Emerso nella revisione della PR #6.
- La verifica del +1 sta sul partecipante: con più edizioni va spostata (MVP 7).
- Collegare il +1 a un partecipante vero: proposta precedente **superata da A3/D-052**; resta testo libero verificato dall'admin, senza tendine nominali.
- Report che confronta più edizioni, emerso nella spec dell'MVP 7.
- Modalità scura e stile configurabile dal pannello admin, emersi nella spec dell'MVP 8.
- Iscrizione in 3 passi con indicatore (scegli i turni, dati, pagamento) come nel mockup; accordion per giorno su telefono.
- Note di rilascio riscritte per gli organizzatori in italiano (oggi sono i testi dei commit, in inglese), emerso nella spec dell'MVP 9.
- Guida in più lingue, ricerca nel testo e immagini (MVP 9).
- Importare l'estratto conto (CSV della banca) e abbinare i movimenti ai codici in automatico; ritardo dell'email di conferma anche dalla scheda; ritiro di un'email già partita; sollecito ai non paganti dalla vista «Da incassare» (emersi nella spec dell'MVP 10).
- Traduzione dei contenuti scritti dall'admin (attività, istruzioni di pagamento, testi legali), emersa nella spec dell'MVP 11.
- Card dell'email scaricabile dalla pagina personale; altre email modificabili dall'admin (MVP 13).
- Note di rilascio tradotte in inglese (MVP 12).
- Voci di cronologia strutturate e tradotte alla lettura, invece di testi italiani salvati (emerso nell'MVP 12).
- Email modificabili oltre alla conferma di iscrizione (pagamento ricevuto, promemoria, lista d'attesa); card dell'immagine scaricabile dalla pagina personale; font con caratteri non latini per i nomi (emersi nell'MVP 13).
