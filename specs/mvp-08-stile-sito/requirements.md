# MVP 8 · Stile del sito Cissone Eventi · Requisiti

Riferimento: `memory-bank/domain.md`. In caso di conflitto vince `domain.md`. Nessuna regola di dominio cambia: questo MVP tocca solo l'aspetto grafico.

Obiettivo: la grafica dell'app riprende lo stile del sito https://sites.google.com/view/cissoneeventi/welcome, che ospita l'iframe della pagina di iscrizione. Chi si iscrive dal sito non deve avere la sensazione di passare a un'altra applicazione.

**Stato**: colori, font e loghi rilevati il 2026-11-05 in `stile.md`. Confermati dal maintainer: nome «Cissonauti Summer Camp», palette, bottoni squadrati, intestazione ridotta nell'iframe, nessuna modalità scura.

## US-1 · Iscrizione dentro il sito

Come persona che si iscrive dal sito voglio che il modulo sembri parte della pagina.

- Quando apro la pagina di iscrizione dentro l'iframe del sito, allora colori, font, bottoni e spaziature sono quelli del sito.
- Quando la pagina è dentro l'iframe, allora mostra un'intestazione ridotta (solo il nome, piccolo, senza logo) e lo sfondo si fonde con la sezione che la contiene (confermato dal maintainer il 2026-11-05).
- Quando apro la stessa pagina fuori dall'iframe, allora vedo l'intestazione completa con logo e nome dell'evento.

## US-2 · Stesso stile in tutta l'app

- Quando apro login, verifica del magic link, pagina personale e pannello admin, allora usano gli stessi colori, font e componenti della pagina di iscrizione.
- Quando apro le tabelle del pannello admin, allora restano leggibili e scorrevoli su telefono come oggi.
- I dialoghi di conferma (disdetta, rimozione admin) e i messaggi di errore e di conferma seguono lo stesso stile.

## US-3 · Intestazione e identità

- Quando apro una pagina fuori dall'iframe, allora in alto vedo logo e nome «Cissonauti Summer Camp» e il logo ha un testo alternativo.
- Quando il logo non è disponibile, allora resta il nome in testo, senza spazi vuoti.

## US-4 · Accessibilità invariata o migliore

- Quando controllo i colori, allora testo e bottoni hanno contrasto almeno AA (4,5:1 per il testo normale, 3:1 per testo grande e bordi dei campi).
- Quando navigo da tastiera, allora il focus resta sempre visibile su ogni elemento interattivo.
- Quando uso il telefono, allora bottoni e campi restano alti almeno 44 px e la pagina non scorre in orizzontale.
- Quando un colore del sito non raggiunge il contrasto richiesto, allora si usa una variante più scura della stessa tinta, e la differenza è annotata.

## US-5 · Nessuna regressione

- Quando eseguo i test esistenti, allora sono tutti verdi senza modifiche ai testi o ai flussi.
- Quando l'app si apre, allora non fa richieste a domini esterni per font o immagini.

## Modifiche a domain.md

Nessuna.

## Fuori scope (Backlog)

- Modalità scura (esclusa dal maintainer il 2026-11-05; il sito è chiaro).
- Personalizzazione dello stile dal pannello admin.
- Restyling dei testi delle email (restano in testo semplice).
