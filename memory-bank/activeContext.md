# Active context

## Ora

MVP 1, Parte 1a completata sul branch `feat/mvp-01-iscrizione-base` (task 1-12 spuntati). Backend 173 test, frontend 33 test, lint verdi, provato end to end in locale.

## Prossimo passo

Parte 1b (task 13-14): Bicep, deploy su Azure, prova dentro Google Sites. Serve prima il via del maintainer e alcune informazioni (vedi dubbi).

## Dubbi aperti

- La CI su SQL Server non è mai girata: al primo push può mostrare differenze tra SQLite e SQL Server da correggere.
- Il Dockerfile non è stato costruito in sessione (nessun daemon Docker).
- Per la 1b servono: abbonamento e resource group Azure, nome dell'app, dominio (o quello di default di Container Apps), mittente email per l'MVP 2.
- "prevedi solo 8-18 e post 18" (risposta al punto 4): interpretato come orari configurabili con default 9-13 e 14-18. Se si voleva un solo slot diurno 8-18, serve una modifica a `domain.md`.
- Conferma pagamento via email già nell'MVP 1 (assunto sì, non era stato risposto).
