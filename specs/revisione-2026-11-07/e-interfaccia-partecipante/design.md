# E · Design proposto

## Flusso e presentazione

E1/E2 rifiniscono `Registration.tsx` e `styles.css`: la barra è già sticky e il recap già nel flusso. Conservare struttura/offset della correzione del 7 novembre; aumentare contrasto e dimensione dei punti principali, impostare esplicitamente il fondo bianco del recap e un accento visibile. Non tradurre «sempre fissa» in un pannello `fixed` che copre gli errori: il comportamento richiesto è permanenza in alto durante lo scorrimento. Verificare tabulazione e scroll verso i campi invalidi sotto l'intestazione.

Nessuna migrazione per E1/E2; non modificare il logo. Le scelte visive devono rispettare i token esistenti, AA, font del progetto e IT/EN, senza rifare il calendario o il flusso di iscrizione.

E3: pagina personale → comando «Proposte degli altri / Other participants' proposals» → modale separata con filtro tipo e righe titolo/descrizione/autore ammesso → chiusura e ritorno al contesto. Non convertire in un elenco pubblico né in un canale di messaggistica.

## Dati e accessi E3

Riutilizzare `Contribution` e il legame booking→edition. Nuovo valore proposto `wanted_skill` (entro limite attuale `kind` di 16 caratteri), validato insieme a `talk/topic/skill`; migrazione solo se i vincoli reali lo richiedono, senza rinominare le vecchie righe. Rivedere tutte le mappe di etichette e report per non ignorare il quarto tipo.

Nuova lettura autenticata separata dall'API admin: filtrare per edizione e prenotazioni attive; proiettare l'autore soltanto con consenso presenza A2 vigente. Senza consenso restituire il testo con autore non mostrato, omettendo nome, id partecipante, link al profilo e contatti. Non riusare la vista admin togliendo il ruolo: contiene informazioni non destinate ai partecipanti. Verificare che due edizioni non si mescolino anche se l'account è lo stesso.

Scelta Q-E1 confermata: **mostrare la proposta anonima**, senza escluderla dal catalogo. Indicazione proposta «Autore non mostrato / Author not shown». Nascondere l'autore strutturato non garantisce che il testo libero sia privo di nomi: avviso all'autore e gestione di eventuali identificativi rimangono da definire, senza promettere anonimizzazione automatica. La persona continua a modificare i propri contributi senza dover concedere il consenso al nome.

Revoca: ricalcolare il filtro a ogni lettura, nessun cache pubblico di nomi; chiudere/ripulire i dati al logout e aggiornare all'apertura della modale. Un'eventuale schermata già aperta e il tempo di aggiornamento sono parte di Q-E1; non promettere di cancellare copie già viste o screenshot. A2 è dipendenza di rilascio: niente nomi visibili nell'attesa della sua implementazione.

## Modifiche a domain.md

Da approvare: quarta tipologia di contributo e consultazione autenticata delle proposte altrui subordinata al consenso presenza. La barra superiore aggiorna la descrizione storica D-038, senza cambiare quote o stato; il recap segue la pagina. Conservare modifica dei soli contributi propri e permessi admin esistenti.

Test futuri: filtri edizione/proprietà/stato attivo; nome presente solo con consenso e proposta anonima altrimenti, accesso senza login negato; quarto tipo nelle viste/report; prove visive E1/E2. Nessun test applicativo aggiunto in questa fase documentale.
