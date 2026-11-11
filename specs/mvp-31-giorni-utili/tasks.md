# MVP 31 · Task

- [x] **T31-1** `useful_day_order` e `rome_today` in dominio e `timefmt`. Test (puri): prima dell'evento, primo giorno, metà, ultimo giorno, dopo l'evento; oggi senza riga; giorni duplicati; `start`/`end` mancanti; l'istante 2026-07-10 22:30 UTC è già l'11 luglio a Roma; 23:30 UTC prima dell'ora legale; mezzanotte UTC senza cambio di giorno a Roma.
- [x] **T31-2** `/week`, `/slots`, `/meals` (JSON): giorni ordinati e campo `today`. Test: ordine nei tre endpoint con orologio finto, totali e contenuto invariati, **CSV cronologici identici a prima**, 401/403, edizione senza giorni.
- [x] **T31-3** Frontend: hook `useRefreshOnReturn`, uso nelle tre pagine, marcatura «Oggi». Test: ordine reso come dal server, ricarica al ritorno della scheda, **nessuna ricarica con una finestra aperta**, il dettaglio aperto sul giorno X resta sul giorno X dopo un riordino, «Oggi» come testo, disiscrizione allo smontaggio.
- [x] **T31-4** Guide IT/EN (`02-days-and-slots`, `03-week`, `04-meals`), `test-manuali.md` pronto, suite completa, Ruff, lint, TypeScript e build verdi. Nessuna migrazione da verificare.

## Scostamenti rispetto al design

- Oltre a `useful_day_order` ci sono due piccoli helper puri in `domain/presence.py`: `event_today` (oggi solo se dentro l'edizione, estremi inclusi) e `in_useful_order` (riordina righe già calcolate per data); `rome_today` sta in `timefmt.py`.
- Senza edizione attiva le tre viste restano vuote e `today` è `null` (le viste lo facevano già, prima del campo nuovo).
- «Nessuna ricarica con qualcosa in corso» è decisa nel hook `useRefreshOnReturn` guardando la pagina (finestra aperta, editor `details` aperto, campo con il focus) più un `blocked()` opzionale: «Settimana» lo usa per il suo dettaglio. Così «Giorni e slot» e «Pasti» non portano stato in più.
- Nei test API l'orologio avanzato scade la sessione: i test accedono di nuovo dopo aver spostato l'ora.
