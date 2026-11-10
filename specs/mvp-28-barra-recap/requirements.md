# MVP 28 · Barra e recap più leggibili

**Stato:** confermata il 2026-11-10 e implementata sul branch `feat/mvp-28-barra-recap` (sopra il 27, PR #30); 4 task completati. Restano le prove visive complete e il collaudo organizzatori. P3, E1–E2. Origine: [US-E1 e US-E2](../revisione-2026-11-07/e-interfaccia-partecipante/requirements.md), D-071–D-073 e D-095/D-096. Solo presentazione: nessuna migrazione, nessun cambiamento di quota, flusso o logo. Compatibile con la quota di conferma dell'MVP 18 (la barra mostra le grandezze già calcolate).

## US-28.1 · Riconoscere importo e iscrizione (E1)

- Quando scorro il modulo, allora la barra con importo e pulsante resta in alto, sotto l'intestazione se questa è sticky, anche su telefono e nell'iframe (comportamento già presente, da conservare).
- Quando la barra si sovrappone al contenuto, allora ha fondo pieno e opaco (non più «vetro» trasparente), un bordo inferiore d'enfasi ben visibile, importo in evidenza e pulsante alto almeno 44 px; il testo ha contrasto almeno AA.
- Quando un campo ha il focus o un errore, allora non resta coperto dalla barra: lo scorrimento verso il campo tiene conto dell'altezza della barra.
- Quando uso zoom al 200% o la lingua inglese, allora importo e pulsante restano leggibili e raggiungibili senza scorrimento orizzontale.
- Quando l'importo cambia, allora si aggiorna come oggi (`aria-live`) con le grandezze del server o la stessa anteprima di dominio: nessuna formula diversa.

## US-28.2 · Leggere il recap laterale (E2)

- Quando scorro su desktop, allora il riquadro a destra del riepilogo dei giorni scorre con la pagina: non è sticky né fixed.
- Quando lo vedo, allora ha fondo bianco (`--color-paper`) e una striscia d'enfasi in alto che lo distingue dal fondo pagina, senza cambiare lo sfondo generale.
- Quando la colonna si impila su telefono, allora resta nel flusso, sotto il contenuto, senza sovrapporsi alla barra.
- Quando il riepilogo è compatto (MVP 15), allora non si espande di nuovo.

## US-28.3 · Vincoli di stile

- Tutti i colori sono token esistenti: niente valori esadecimali fuori da `:root`.
- Nessuna striscia laterale da 2 px o più (lo vieta `theme.test.ts`): l'enfasi è in alto o in basso.
- `--color-cta` si usa solo come riempimento o decorazione, mai come colore del testo.

## Fuori scope

Barra fissa a ogni costo con `position: fixed`, ridisegno del flusso di iscrizione, indicatore a 3 passi (Backlog), modalità scura.

## Modifiche a domain.md (proposta, non applicata)

Aggiornare la nota D-038: la barra con importo e iscrizione resta in alto durante lo scorrimento; il recap segue la pagina.
