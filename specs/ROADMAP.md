# Roadmap

MVP piccoli e successivi. Ogni MVP ha la sua cartella `specs/mvp-NN-<slug>/` creata nella fase B1. Lo stato aggiornato è in `memory-bank/progress.md`.

## MVP 1 · Iscrizione base

- **Obiettivo**: raccogliere iscrizioni vere con posto bloccato fino al pagamento, e far registrare i pagamenti agli organizzatori.
- **Contenuto**: scheletro dell'app, DB e migrazioni, impostazioni essenziali dell'edizione gestite da un admin seed, pagina pubblica di iscrizione incorporabile, calcolo dell'importo, blocco di N giorni, magic link con email in console, admin che vede le iscrizioni e registra i pagamenti, deploy su Azure.
- **Fatto quando**: su Azure una persona si iscrive dall'iframe di Google Sites, vede importo, causale, istruzioni e scadenza; l'admin vede l'iscrizione, registra il pagamento e la prenotazione diventa `confermata`; una prenotazione non pagata risulta `scaduta` dopo la scadenza e libera i posti.

## MVP 2 · Pagina personale

- **Obiettivo**: rendere il partecipante autonomo dopo l'iscrizione.
- **Contenuto**: login con magic link e cookie da 14 giorni, modifica degli slot, saldo e istruzioni, richiesta di disdetta, email reali (Azure Communication Services) e avviso di scadenza 24 ore prima.
- **Fatto quando**: un partecipante riceve una vera email, entra nella pagina personale, cambia i suoi slot con l'importo ricalcolato, vede il saldo, richiede la disdetta liberando i posti; l'avviso di scadenza parte una sola volta.

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
- **Contenuto**: +1 collegato a chi invita, report di riepilogo dell'edizione.
- **Fatto quando**: un partecipante registra un +1 collegato a sé e l'admin genera il report di riepilogo (presenze, pasti, attività, incassi).

## Backlog

Idee e questioni fuori dagli MVP correnti. Si aggiungono qui, non si implementano.

- Importi definitivi della quota e dei pasti.
- Testi legali definitivi (in attesa di parere).
- Meccanismo dell'unconference.
- Prelazione per chi ha già partecipato.
- Gestione esplicita del +1 (dettagli da definire prima dell'MVP 7).
- Limite di richieste (rate limit) su richiesta del magic link e sul login con password, per evitare invii email ripetuti e tentativi a raffica.
- Canale "contanti/altro" per registrare pagamenti fuori dai quattro canali previsti.
- Regola per i pranzi: serve la presenza di giorno per aderire al pranzo? (da chiarire prima dell'MVP 5)
- Se la quota giornaliera debba contare un giorno con la sola sera (per ora sì).
