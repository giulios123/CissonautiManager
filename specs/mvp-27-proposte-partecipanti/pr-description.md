# MVP 27 · Proposte tra partecipanti

## Cosa cambia per gli organizzatori

- Nella pagina personale, sezione «Cosa porti al camp», il pulsante **«Proposte degli altri»** apre l'elenco di ciò che gli altri iscritti propongono o cercano. Lo vede solo chi ha un'iscrizione attiva.
- Il **nome** dell'autore compare solo se ha dato il consenso alla presenza; altrimenti la proposta resta visibile con «Autore non mostrato».
- Nuovo tipo di contributo: **«Competenza che cerco»**.
- Chi scrive vede un avviso: il testo è visibile agli altri, niente nomi o recapiti di terzi.
- Nella vista admin «Contributi» si può **nascondere** una proposta agli altri (con motivo) e mostrarla di nuovo; l'autore continua a vederla; resta traccia nella cronologia della scheda.

## Come provarlo

Segui [test-manuali.md](test-manuali.md) (10 passi, in italiano e in inglese).

## Dettagli tecnici

- Migrazione `0027_contribution_hidden` (additiva) sopra la 0026. **Da verificare nella CI SQL Server.**
- `GET /api/me/proposals`: iscritti attivi e admin; filtro nel server; consenso valutato a ogni lettura in una sola query; `Cache-Control: no-store`; nessun id, email o telefono dell'autore.
- `POST /api/admin/contributions/{id}/hide|unhide`: solo admin, idempotenti, voce in `AuditLog`.
- La lettura non richiede l'informativa accettata (come le altre letture personali).
- Il branch parte da quello del 26 (PR #29): conviene unire prima quella.
- Verificato in locale: test backend e frontend, Ruff, lint, build. Da verificare: CI SQL Server, collaudo organizzatori.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
