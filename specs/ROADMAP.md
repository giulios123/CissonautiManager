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
- Annullare un'attività con iscritti togliendola a tutti e ricalcolando gli importi; cambiarne il prezzo dopo le adesioni (MVP 6).
- Attività su più fasce o su tutto il giorno, come le escursioni (MVP 6).
- Capienza dei pasti o chiusura delle adesioni a un'ora fissa (MVP 5).
- Avviso a chi è in lista d'attesa quando la sua posizione cambia (MVP 4).
- Anteprima della quota calcolata dal server nei modificatori di pasti e attività: oggi l'anteprima parte dalla quota salvata e, se un admin cambia un prezzo con iscrizioni già presenti, può differire dall'importo che viene poi salvato (che è sempre giusto). Emerso nella revisione della PR #6.
- La verifica del +1 sta sul partecipante: con più edizioni va spostata (MVP 7).
- Collegare il +1 a un partecipante vero (relazione invece del testo libero), emerso nella spec dell'MVP 7.
- Report che confronta più edizioni, emerso nella spec dell'MVP 7.
- Modalità scura e stile configurabile dal pannello admin, emersi nella spec dell'MVP 8.
