# E · Interfaccia del partecipante · Requisiti

**Stato:** aggiornata con le risposte, non implementata. P3: E1–E2; P2: E3. Decisioni D-071–D-073 e precisazioni D-095/D-096. [Risposte e dettagli residui](../domande-aperte.md).

## US-E1 · Riconoscere importo e iscrizione (E1)

- Quando scorro il modulo, allora la barra con importo e iscrizione rimane sempre in alto, con offset sotto l'intestazione se presente, anche su telefono e nell'iframe.
- Quando la barra è sovrapposta al contenuto, allora sfondo, testo e comando sono chiaramente distinguibili; testo almeno con contrasto AA e area di tocco almeno 44 px, senza coprire campi focalizzati o errori.
- Quando uso zoom al 200% o la lingua inglese con stringhe più lunghe, allora importo e comando restano leggibili e raggiungibili senza scorrimento orizzontale della pagina.
- Quando B1/B2 sono presenti, allora la barra usa le grandezze corrette del server o la stessa anteprima di dominio; il miglioramento visivo non introduce una formula di quota diversa.

## US-E2 · Leggere il recap laterale (E2)

- Quando scorro su desktop, allora il riquadro a destra del riepilogo dei giorni scorre con il contenuto della pagina; non diventa un secondo pannello fisso.
- Quando vedo il riquadro, allora il suo fondo è bianco e la striscia di enfasi si distingue dal resto della pagina, senza cambiare lo sfondo generale del design system.
- Quando la colonna laterale si impila su telefono, allora resta nel flusso senza sovrapporsi alla barra superiore; i riepiloghi compatti già implementati non vengono espansi di nuovo.

## US-E3 · Consultare le proposte altrui (E3)

- Quando sono autenticato, allora un comando separato apre una modale con le proposte degli altri nell'edizione corrente; la gestione dei miei contributi resta distinta.
- Quando una proposta mostra il nome dell'autore, allora quell'autore ha un consenso presenza A2 vigente; senza sessione non vengono restituiti né nome né proposte.
- Quando il consenso è assente, negato o revocato, allora la proposta resta visibile **anonima**, soltanto agli autenticati, senza nome né identificativi del profilo dell'autore. La scelta di mostrare il testo anonimo è confermata; la gestione di riferimenti personali nel testo libero resta il dettaglio Q-E1.
- Quando apro i dati altrui, allora non ricevo email, telefono, Telegram, note interne, allergie, pagamenti o motivi di cancellazione. Nome nel payload filtrato dal server, non semplicemente nascosto nel browser.
- Quando aggiungo un contributo mio, allora posso scegliere anche «Competenze che cerco / Skills I'm looking for», distinto dalle competenze offerte e con titolo obbligatorio; i tre tipi precedenti continuano a funzionare.
- Quando filtro o cambio lingua, allora i quattro tipi hanno etichette coerenti in modale, editor personale, vista admin, report/CSV e guida.
- Quando chiudo la modale, allora il focus torna al comando; caricamento, vuoto ed errore sono comprensibili. Si mostrano **solo proposte di prenotazioni attive**, in attesa o confermate; scadute/disdette restano eventualmente nello storico admin, secondo conservazione, come approvato in Q-E2.
