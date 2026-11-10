# MVP 27 · Proposte tra partecipanti

**Stato:** confermata il 2026-11-10 e implementata sul branch `feat/mvp-27-proposte-partecipanti` (sopra il branch del 26, PR #29); 8 task completati. Restano CI SQL Server e collaudo organizzatori. P2, E3. Origine: [US-E3](../revisione-2026-11-07/e-interfaccia-partecipante/requirements.md), Q-E1/E2 e le due risposte del 2026-11-10 (D-117, D-118). Dipende dal consenso «presenza» dell'MVP 17 (già in `main`). Indipendente dai lavori economici. Una migrazione additiva.

## US-27.1 · Consultare le proposte degli altri

- Quando sono autenticato con una prenotazione attiva (in attesa o confermata) nell'edizione corrente, allora nella sezione dei contributi della pagina personale trovo il comando «Proposte degli altri» che apre una modale separata.
- Quando apro la modale, allora vedo le proposte (tipo, titolo, descrizione) delle **sole prenotazioni attive** dell'edizione corrente, senza le mie e senza quelle nascoste dall'admin.
- Quando la mia prenotazione è scaduta, disdetta, rimborsata o sono solo in lista d'attesa, allora il comando non compare e l'API risponde 403.
- Quando non sono autenticato, allora l'API risponde 401: né proposte né nomi.
- Quando un admin è autenticato, allora l'API gli risponde con la stessa proiezione, senza dati in più (nessun comando dedicato nell'interfaccia: gli admin hanno già la vista completa).
- Quando la persona ha prenotazioni in due edizioni, allora le proposte delle edizioni non si mescolano.

## US-27.2 · Autore solo con consenso

- Quando l'autore ha un consenso «presenza» concesso e valido per il documento corrente, allora la proposta mostra il suo nome.
- Quando il consenso è assente, negato, revocato o riferito a una versione precedente, allora la proposta resta visibile **anonima** con «Autore non mostrato / Author not shown»: nessun nome, id partecipante, email, telefono, Telegram o link al profilo.
- Quando un consenso viene revocato, allora alla lettura successiva la proposta è anonima; nessuna cache conserva i nomi. Una modale già aperta si aggiorna alla riapertura; non si promette di cancellare copie già viste.
- Quando apro i dati altrui, allora non ricevo note interne, allergie, pagamenti né motivi di cancellazione: il filtro è nella risposta del server, non nel browser.
- Quando una persona non ha dato il consenso al nome, allora continua a modificare i propri contributi senza obblighi.

## US-27.3 · Testo libero e nascondere (D-117)

- Quando scrivo o modifico un contributo, allora un avviso mi dice che titolo e descrizione sono visibili agli altri iscritti e che non devo inserire nomi o recapiti di altre persone.
- Quando un admin trova nel testo un nome o un dato da non mostrare, allora può **nascondere** la proposta dalla consultazione (e rimostrarla), con autore, data e motivo facoltativo in cronologia; la proposta non viene cancellata né modificata e l'autore continua a vederla e a modificarla.
- Quando una proposta è nascosta, allora non compare nella modale dei partecipanti; resta visibile agli admin, marcata «Nascosta», anche nel CSV.
- Quando chi non è admin tenta di nascondere, allora riceve 403.
- Quando nascondere o mostrare si ripete, allora non si duplicano voci di cronologia.

## US-27.4 · Il quarto tipo «Competenze che cerco»

- Quando aggiungo un contributo, allora posso scegliere anche «Competenze che cerco / Skills I'm looking for», con titolo obbligatorio come gli altri.
- Quando esistono contributi già salvati, allora talk, temi e competenze funzionano come prima, senza modifiche alle righe esistenti.
- Quando filtro o cambio lingua, allora i quattro tipi hanno le stesse etichette in modale, editor personale, vista admin, report, CSV, guida e messaggi di errore.
- Quando il report conta i contributi, allora il quarto tipo ha il suo conteggio.

## US-27.5 · Accessibilità e stati

- Quando apro la modale, allora il focus entra nella modale; Esc o «Chiudi» la chiudono e il focus torna al comando.
- Quando carico, allora vedo un indicatore; con zero proposte uno stato vuoto; in caso di errore un messaggio con «Riprova».
- Quando filtro per tipo, allora l'elenco si aggiorna senza ricaricare e il filtro è un controllo con etichetta.
- Quando faccio logout, allora i dati delle proposte sono azzerati.

## Fuori scope

Messaggi tra partecipanti, contatto con l'autore, elenco pubblico, anonimizzazione automatica del testo libero, notifiche per nuove proposte.

## Modifiche a domain.md (proposta, non applicata)

- Contributi: quattro tipi (talk, temi, competenze offerte, competenze cercate).
- Consultazione delle proposte altrui riservata a iscritti attivi e admin; nome mostrato solo con consenso «presenza» valido, altrimenti anonima; l'admin può nasconderle dalla consultazione senza cancellarle.
