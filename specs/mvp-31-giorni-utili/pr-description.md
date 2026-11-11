## Cosa cambia per gli organizzatori

- In **Settimana**, **Giorni e slot** e **Pasti**, durante l'edizione i giorni sono in ordine utile: prima **oggi** (segnato «Oggi»), poi i giorni che verranno, poi i passati. Prima e dopo l'edizione resta l'ordine cronologico. Il giorno è quello di Roma, qualunque sia il fuso del telefono.
- L'ordine si aggiorna quando apri o ricarichi la pagina e quando torni sulla scheda del browser: il nuovo giorno sale in testa da solo.
- Se hai una finestra aperta, un editor aperto o un campo in modifica, **nulla si ricarica e nulla si sposta**; si riprova al ritorno successivo.
- I numeri restano legati alla loro data. I **CSV** restano sempre in ordine cronologico, uguali per tutti.
- Report, Contributi, Esterni, Da incassare e le altre viste non cambiano.

## Checklist di test manuali (per gli organizzatori)

Vedi [test-manuali.md](test-manuali.md) (12 passi, italiano e inglese).

## Dettagli tecnici

- Nessuna migrazione, nessun dato nuovo. Funzioni pure `useful_day_order`, `event_today`, `in_useful_order` (`domain/presence.py`) e `rome_today` (`timefmt.py`); le API JSON di `/week`, `/slots` e `/meals` restituiscono i giorni ordinati e un campo `today`; i rami CSV non cambiano.
- Frontend: hook `useRefreshOnReturn`, badge testuale «Oggi», testi IT/EN (`views.today`), guida admin IT/EN (Settimana, Giorni e slot, Pasti).
- Verificato in locale: test backend e frontend, Ruff, lint, TypeScript, build, controllo guida. **Da verificare:** prova visiva su telefono e collaudo organizzatori. **Da concordare:** la giornata senza demo per il rilascio. Nessun deploy.
- Branch `feat/mvp-31-giorni-utili`, impilato su `feat/mvp-30-consegne-benefit` (PR #33), a sua volta su `feat/mvp-29-proposta-attivita` (PR #32): conviene unire prima quelle.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
