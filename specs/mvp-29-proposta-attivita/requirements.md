# MVP 29 · Da proposta ad attività

**Stato:** spec pronta per la revisione (B1), nessuna implementazione. P3, C4. Origine: [US-C4](../revisione-2026-11-07/c-attivita-logistica/requirements.md) e la risposta del 2026-11-11 su Q-C4 (D-119). Dipende dai contributi (MVP 6, quarto tipo dal 27) e dai testi attività IT/EN (MVP 24). Una migrazione additiva (`0028`, dopo la `0027`).

## US-29.1 · Creare un'attività da una proposta

- Quando un admin sceglie «Crea attività» su un contributo della vista «Contributi», allora si apre il modulo attività già compilato con titolo e descrizione della proposta e un riferimento alla fonte visibile.
- Quando il modulo si apre, allora **non esiste ancora nessuna attività**: l'admin sceglie data, fascia, orari, costo, destinatario e capienza e conferma. «Annulla» chiude senza lasciare tracce.
- Quando salvo, allora valgono tutti i controlli dell'attività ordinaria (date dentro l'edizione, orari validi, capienza, modalità di incasso) e l'attività resta collegata alla proposta d'origine.
- Quando la proposta è nascosta agli altri (MVP 27), allora si può comunque creare un'attività: la visibilità della proposta non c'entra con l'organizzazione.
- Nessuna generazione automatica di calendario e **nessuna adesione automatica dell'autore**.

## US-29.2 · Titolo e descrizione nelle due lingue

- Quando il modulo si apre, allora il testo della proposta va nella lingua dell'interfaccia dell'admin e l'altra lingua è **vuota e da completare**: i testi IT/EN restano obbligatori (MVP 24) e nessuna traduzione viene inventata.
- Quando l'admin tocca il testo precompilato, allora è un normale testo dell'attività: non resta legato alla proposta.
- Quando la proposta è più lunga dei limiti dell'attività (titolo 200, descrizione 5000), allora il modulo la mostra com'è e il salvataggio chiede di accorciarla, come per qualsiasi attività.

## US-29.3 · Più attività da una proposta, senza duplicati accidentali

- Quando una proposta ha già attività collegate, allora la riga mostra l'elenco «Attività create» (titolo, giorno, fascia) con link alla scheda dell'attività.
- Quando l'admin usa di nuovo «Crea attività» sulla stessa proposta, allora si apre un modulo nuovo e può creare **un'altra attività**: una proposta può generarne più di una.
- Quando lo stesso salvataggio arriva due volte (doppio clic, rete lenta, ritentativo del browser), allora l'attività è **una sola**: la seconda richiesta restituisce quella già creata.
- Quando l'admin apre il modulo due volte e salva due volte, allora le attività sono due: ogni apertura è un comando intenzionale diverso.

## US-29.4 · La proposta resta modificabile e indipendente

- Quando l'autore o un admin modifica o nasconde la proposta, allora le attività già create **non cambiano** (titolo, descrizione, orari, iscritti).
- Quando un'attività viene modificata o cancellata, allora la proposta non cambia e il suo elenco «Attività create» si aggiorna.
- Quando l'attività collegata a una proposta viene cancellata (solo senza iscritti, regola esistente), allora sparisce anche dall'elenco della proposta.

## US-29.5 · Se la proposta sparisce (D-119)

- Quando la proposta viene cancellata dall'autore, oppure sparisce con la sua prenotazione (disdetta senza pagamenti), allora le attività create **restano** e conservano una copia del titolo della proposta.
- Quando apro la scheda di un'attività con la fonte sparita, allora l'admin legge «Dalla proposta «<titolo>» (non più disponibile)», senza nome dell'autore.
- Quando la fonte esiste ancora, allora la scheda mostra «Dalla proposta «<titolo>»» con link alla vista dei contributi.
- Il titolo copiato è un dato dell'attività, visibile **solo agli admin**: non compare mai in pagina personale, email, guida o export dei partecipanti.

## US-29.6 · Protezioni

- Quando chi non è admin tenta di creare un'attività da una proposta, allora riceve 403 (401 se anonimo).
- Quando la proposta indicata appartiene a un'altra edizione o non esiste, allora la richiesta è rifiutata (404) e nessuna attività viene creata.
- Quando la stessa chiave di richiesta è usata con contenuti diversi, allora vince la prima creazione e la risposta indica l'attività esistente (nessun secondo salvataggio silenzioso).
- Tutte le creazioni lasciano una voce di cronologia con autore e proposta d'origine.

## US-29.7 · Accessibilità e lingue

- Il comando «Crea attività» è un vero pulsante con nome accessibile che include il titolo della proposta; il modulo conserva focus, etichette e messaggi d'errore dell'attività ordinaria; al salvataggio o all'annullo il focus torna al comando.
- Testi dell'interfaccia in `frontend/src/i18n/{it,en}.ts`, messaggi del server in `backend/app/i18n.py`, guida admin IT/EN aggiornata.

## Fuori scope

Aggiornamento automatico delle attività quando la proposta cambia; conversione in blocco di più proposte; collocazione automatica nel programma; iscrizione automatica dell'autore; notifica all'autore che la sua proposta è diventata attività; mostrare la fonte ai partecipanti (idee nel Backlog).

## Modifiche a domain.md (proposta, non applicata)

- Contributi: un admin può creare, da un contributo, una o più attività indipendenti; resta il riferimento alla fonte (e, se la fonte sparisce, una copia del suo titolo visibile solo agli admin). Le modifiche alla proposta non si propagano alle attività.
