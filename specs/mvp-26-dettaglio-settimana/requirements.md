# MVP 26 · Dettaglio dei numeri settimanali

**Stato:** spec pronta (B1), in attesa di conferma; nessuna implementazione. P2, D1. Origine: [US-D1](../revisione-2026-11-07/d-admin-comunicazioni/requirements.md), risposta Q-D1 («dettagli per i numeri, inclusi totali e fasce»). Nessuna dipendenza bloccante: usa gli esterni del 25a perché sono già nei conteggi di pasti e attività. Solo admin, nessuna migrazione.

## US-26.1 · Aprire il dettaglio da un numero

- Quando nella vista settimanale attivo una cella (mattina, pomeriggio, sera, persone, pranzi, cene, attività) di un giorno, allora si apre una modale con il titolo «giorno · metrica», il conteggio e l'elenco che spiega esattamente quel numero.
- Quando attivo un totale in fondo (persone diverse, pranzi, cene, attività), allora la modale elenca tutta la settimana, con il giorno accanto a ogni riga.
- Quando la modale apre un conteggio di persone, allora ogni riga mostra nome, stato dell'iscrizione e un link alla scheda; per la sera derivata (D-009) la riga è marcata «derivata».
- Quando la modale apre pranzi o cene, allora le righe comprendono anche gli esterni (25a) marcati «esterno», senza link alla scheda iscritto ma con il link alla scheda dell'esterno.
- Quando la modale apre le attività, allora si mostra **una riga per adesione** con titolo dell'attività e persona, e in testa «N adesioni · M persone diverse»; il numero non è mai presentato come persone se conta adesioni.
- Quando il numero è zero, allora il pulsante resta attivo e la modale mostra uno stato vuoto comprensibile.
- Quando una riga è un iscritto, allora il link porta alla sua scheda admin; la modale non espone email, telefono, regime alimentare, allergie, note né importi.

## US-26.2 · Coerenza con la tabella

- Quando apro un dettaglio, allora il numero in testa alla modale e il numero di righe usano gli stessi criteri della tabella (stesse prenotazioni attive, stessa sera derivata, stessa esclusione della lista d'attesa e delle scadute): nessuna formula duplicata nel browser.
- Quando lo stato cambia tra il caricamento della tabella e l'apertura della modale e i due numeri differiscono, allora la modale lo dice («Il numero è cambiato da X a Y») e la tabella si ricarica.
- Quando c'è un errore di rete, allora la modale mostra un messaggio e un comando per riprovare; il resto della pagina resta usabile.

## US-26.3 · Tastiera e accessibilità

- Quando navigo da tastiera, allora ogni numero è un vero `<button>` con nome accessibile («Pranzi di lun 9 nov: 12») e focus visibile.
- Quando la modale si apre, allora il focus entra nella modale, Tab non esce dalla modale ed Esc o «Chiudi» la chiudono riportando il focus sul numero che l'ha aperta.
- Quando cambio lingua, allora titoli, etichette e stato vuoto sono in italiano e inglese.

## US-26.4 · Permessi

- Quando chi non è admin o non è autenticato chiama il dettaglio, allora riceve 403 (o 401): la protezione è nell'API, non solo nella pagina.
- Quando data o metrica non sono valide o la data è fuori dall'edizione, allora la risposta è 422.

## Fuori scope

- CSV del dettaglio e del tabellone con ordine diverso (Q-D2 riguarda l'MVP 31).
- Dettagli sulla pagina «Persone» o altre viste.
- Modifica di dati dalla modale: è di sola lettura.

## Modifiche a domain.md (proposta, non applicata)

Nella riga delle viste admin: «ogni numero della settimana apre l'elenco che lo spiega (persone, pasti, adesioni alle attività), senza dati sanitari né di contatto».
