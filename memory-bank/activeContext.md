# Active context

## Ora

MVP 1, Parte 1a, in implementazione sul branch `feat/mvp-01-iscrizione-base` (fallback: `claude/ecstatic-davinci-20qb6m`). Task in `specs/mvp-01-iscrizione-base/tasks.md`.

## Decisioni del maintainer (2026-11-04)

1. MVP 1 diviso in 1a (task 1-12, locale e CI) e 1b (task 13-14, deploy Azure).
2. Branch `feat/mvp-01-iscrizione-base`; se non si riesce a crearlo si usa quello della sessione.
3. Accesso anche con password, oltre al magic link (aggiornato `domain.md`).
4. Scadenza del blocco: N x 24 ore esatte dalla creazione.
5. Email già iscritta con prenotazione scaduta: nuova prenotazione se c'è posto, altrimenti rifiuto.
6. Pagamento su prenotazione scaduta: riattivazione se c'è posto, altrimenti pagamento registrato e avviso all'admin.
7. Email di conferma pagamento nell'MVP 1 (non risposto, assunto sì).

## Prossimo passo

Task 1 (scaffold backend), poi in ordine.

## Dubbi aperti

- Il maintainer ha scritto "prevedi solo 8-18 e post 18" rispondendo al punto 4. Interpretazione adottata: orari configurabili con default 9-13 e 14-18 come in `domain.md` (quindi 8-18 si ottiene configurandoli). Se invece si intende un solo slot diurno 8-18 più la sera, serve una modifica a `domain.md`.
- Test di integrazione su SQLite in locale (nessun Docker in questo ambiente), su SQL Server in CI.
