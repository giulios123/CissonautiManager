# MVP 31 · Task

- [ ] **T31-1** `useful_day_order` e `rome_today` in dominio e `timefmt`. Test (puri): prima dell'evento, primo giorno, metà, ultimo giorno, dopo l'evento; oggi senza riga; giorni duplicati; `start`/`end` mancanti; l'istante 2026-07-10 22:30 UTC è già l'11 luglio a Roma; 23:30 UTC prima dell'ora legale; mezzanotte UTC senza cambio di giorno a Roma.
- [ ] **T31-2** `/week`, `/slots`, `/meals` (JSON): giorni ordinati e campo `today`. Test: ordine nei tre endpoint con orologio finto, totali e contenuto invariati, **CSV cronologici identici a prima**, 401/403, edizione senza giorni.
- [ ] **T31-3** Frontend: hook `useRefreshOnReturn`, uso nelle tre pagine, marcatura «Oggi». Test: ordine reso come dal server, ricarica al ritorno della scheda, **nessuna ricarica con una finestra aperta**, il dettaglio aperto sul giorno X resta sul giorno X dopo un riordino, «Oggi» come testo, disiscrizione allo smontaggio.
- [ ] **T31-4** Guide IT/EN (`02-days-and-slots`, `03-week`, `04-meals`), `test-manuali.md` pronto, suite completa, Ruff, lint, TypeScript e build verdi. Nessuna migrazione da verificare.
