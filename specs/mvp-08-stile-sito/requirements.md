# MVP 8 · Stile del sito Cissone Eventi · Requisiti

Riferimento: `memory-bank/domain.md`. In caso di conflitto vince `domain.md`. Nessuna regola di dominio cambia: questo MVP tocca solo l'aspetto grafico.

Obiettivo: la grafica dell'app riprende lo stile del sito https://sites.google.com/view/cissoneeventi/welcome, che ospita l'iframe della pagina di iscrizione. Chi si iscrive dal sito non deve avere la sensazione di passare a un'altra applicazione.

**Stato**: la sessione che ha scritto questa spec non ha potuto aprire il sito (`sites.google.com` non è tra i domini consentiti dalla rete dell'ambiente). Colori, font e logo vanno raccolti nel task 1, prima di qualsiasi modifica: nessuna palette è stata inventata.

## US-1 · Iscrizione dentro il sito

Come persona che si iscrive dal sito voglio che il modulo sembri parte della pagina.

- Quando apro la pagina di iscrizione dentro l'iframe del sito, allora colori, font, bottoni e spaziature sono quelli del sito.
- Quando la pagina è dentro l'iframe, allora non ripete l'intestazione del sito (niente logo grande né titolo doppio) e lo sfondo si fonde con la sezione che la contiene.
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

- Modalità scura (il sito è chiaro; da valutare se il sito la introduce).
- Personalizzazione dello stile dal pannello admin.
- Restyling dei testi delle email (restano in testo semplice).
