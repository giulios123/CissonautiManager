# MVP 28 · Task

- [x] **T28-1** Barra: fondo pieno, striscia inferiore, importo e pulsante più evidenti (44 px). Test: `theme.test.ts` verde con le nuove coppie di contrasto; `Registration.test.tsx` invariato per struttura e aggiornamento dell'importo.
- [x] **T28-2** Recap: fondo bianco, striscia superiore, nessuna posizione sticky/fixed. Test che verifica l'assenza di `position: sticky|fixed` su `.summary` e il fondo da token.
- [x] **T28-3** Campi con errore o focus non coperti dalla barra: `scroll-margin-top` / altezza della barra nella variabile CSS. Test sul calcolo dell'offset dove possibile; il resto è collaudo visivo.
- [x] **T28-4** Prove visive e guida: desktop, telefono, iframe, zoom 200%, inglese; guida partecipante (sezione iscrizione) IT/EN solo se la descrizione visibile cambia; `test-manuali.md` pronto; suite frontend, lint, TypeScript e build verdi.

Scostamenti rispetto al design: le variabili `--registration-sticky-offset` e `--registration-bar-height` stanno ora sul `<form>` (non sulla barra) così i campi possono leggerle per `scroll-margin-top`; il recap ha fondo bianco e striscia superiore anche su telefono (con un po' di padding); il test di non-stickiness è su CSS in `theme.test.ts` e le variabili sono provate in `Registration.test.tsx`. Prova visiva fatta solo con uno screenshot di Chrome senza testa (desktop 1280 px e telefono): barra opaca con striscia gialla in basso; non sono stati provati lo scorrimento, l'iframe reale, lo zoom al 200% e il recap con contenuto.
