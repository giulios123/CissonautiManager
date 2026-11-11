# MVP 31 · Giorni utili per primi

**Stato:** spec pronta per la revisione (B1), nessuna implementazione. P3, D2. Origine: [US-D2](../revisione-2026-11-07/d-admin-comunicazioni/requirements.md), Q-D2 e la risposta del 2026-11-11 sul perimetro (D-122). Solo presentazione: **nessuna migrazione**. Rilascio separato, in una giornata senza demo (data ancora da concordare, vedi «Domande aperte»).

## US-31.1 · Ordine «oggi, poi i prossimi, poi i passati»

- Quando la data di oggi in Europe/Rome è compresa tra inizio e fine dell'edizione, allora le viste admin **Settimana**, **Giorni e slot** e **Pasti** mostrano prima il giorno di oggi (se ha una riga), poi i giorni futuri in ordine cronologico, poi i giorni passati in ordine cronologico.
- Quando l'evento non è ancora iniziato, allora l'ordine resta cronologico. Quando è finito, resta cronologico.
- Quando oggi è dentro l'edizione ma non ha righe (nessuno slot quel giorno), allora si parte dal primo giorno futuro.
- Quando il giorno è quello di oggi, allora è marcato «Oggi» a parole (non solo a colore o posizione) in tutte e tre le viste.
- Il giorno è sempre quello di **Roma**, anche se il browser o il server sono in un altro fuso (a mezzanotte UTC non cambia nulla; cambia a mezzanotte di Roma).

## US-31.2 · Quando l'ordine si aggiorna

- Quando apro la pagina o la ricarico, allora vedo l'ordine di quel momento.
- Quando torno sulla scheda del browser dopo averla lasciata (la scheda torna visibile), allora i dati e l'ordine si ricaricano, così un giorno nuovo passa in testa senza ricaricare a mano.
- Quando sto interagendo (una finestra di dettaglio aperta, un campo in modifica, un'azione in corso), allora **nulla si riordina né si ricarica**: l'aggiornamento al ritorno si salta e si riprova al ritorno successivo. Nessun salto improvviso sotto le dita.
- Quando i giorni si riordinano, allora numeri, selezioni, dettagli e titoli restano legati alla **loro data reale**: l'ordine cambia, non il contenuto.

## US-31.3 · Export e altre viste

- Il CSV della settimana, dei giorni e slot e dei pasti restano in **ordine cronologico stabile**, uguale per tutti e in ogni giorno (D-122).
- Report, «Contributi», «Esterni», «Da incassare» e le altre viste non cambiano.
- La finestra di dettaglio dei numeri della settimana (MVP 26) non cambia: apre i dati del giorno scelto.

## US-31.4 · Accessibilità e lingue

- «Oggi» è testo con il suo nome accessibile (nei titoli di giorno e nelle righe della tabella settimanale); l'ordine visivo coincide con l'ordine di lettura e di tabulazione.
- Testi IT/EN in `frontend/src/i18n/{it,en}.ts` (`views.today`), guida admin IT/EN aggiornata (viste «Settimana», «Giorni e slot», «Pasti»).

## Fuori scope

Ordine dei CSV diverso da quello cronologico, scorrimento automatico verso oggi, evidenziazione di altri giorni, aggiornamento in tempo reale mentre la pagina è aperta, cambiare l'ordine di altre viste, impostare «oggi» a mano.

## Modifiche a domain.md (proposta, non applicata)

- Viste admin Settimana, Giorni e slot e Pasti: durante l'edizione i giorni sono ordinati oggi, futuri, passati (data di Roma); prima e dopo l'edizione cronologico; i CSV restano cronologici.

## Domande aperte

- **Finestra di rilascio:** in quale giornata, senza demo, vogliamo distribuire? (Non blocca la spec né l'implementazione; blocca solo il deploy.)
