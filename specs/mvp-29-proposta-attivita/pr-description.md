## Cosa cambia per gli organizzatori

- Nella vista «Contributi» ogni proposta ha il pulsante **«Crea attività»**: si apre il modulo attività con titolo e descrizione della proposta nella lingua in uso (l'altra lingua resta da completare). Finché non si salva non esiste nessuna attività; «Annulla» non lascia tracce.
- Dalla stessa proposta si possono creare più attività: la colonna «Attività» le elenca con il link. Un doppio clic su «Crea l'attività» non ne crea due.
- Modificare, nascondere o cancellare la proposta non cambia le attività già create. L'autore non viene iscritto all'attività.
- La scheda dell'attività mostra «Dalla proposta «…»»; se la proposta è sparita (cancellata dall'autore o rimossa con la sua iscrizione) resta il titolo d'origine con «(non più disponibile)», visibile solo agli organizzatori.
- Il CSV dei contributi ha la colonna «Attività create».

I partecipanti non vedono niente di nuovo.

## Checklist di test manuali (per gli organizzatori)

Vedi [test-manuali.md](test-manuali.md) (12 passi), in italiano e in inglese.

## Dettagli tecnici

- Migrazione additiva `0028_activity_source` (sopra la 0027): `activity.source_contribution_id` (FK), `source_title`, `request_key` con indice univoco filtrato.
- `POST /api/admin/activities` accetta `source_contribution_id` e `request_key` (stessa chiave = stessa attività, 200 invece di 201; corsa tra due richieste gestita con `IntegrityError`); la proposta deve essere dell'edizione corrente (404 altrimenti), anche se nascosta.
- Lo scollegamento della fonte è fatto dal servizio (`detach_activities`) prima di cancellare il contributo o la prenotazione, non con `ON DELETE SET NULL` (comportamento diverso tra SQLite e SQL Server).
- La vista contributi legge i collegamenti con una sola query. `ActivityForm` è stato spostato in `ActivityForm.tsx` e riusato dalla modale.
- Verificato in locale: test backend e frontend, Ruff, lint, TypeScript, build. Da verificare: CI su SQL Server (indice filtrato e vincolo `fk_activity_source_contribution` della 0028), prova visiva in browser e collaudo organizzatori. Nessun deploy.
- Branch `feat/mvp-29-proposta-attivita`, impilato sul branch delle spec 29–31 (`docs/spec-mvp-29-31`) e sullo stack 26–28.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
