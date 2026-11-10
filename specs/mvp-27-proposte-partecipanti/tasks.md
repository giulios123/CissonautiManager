# MVP 27 · Task

- [x] **T27-1** Tipo `wanted_skill`: costanti, validazione, `Literal`, etichette di backend (CSV, report, `admin_texts`, messaggio di errore) e di frontend, chiavi IT/EN. Test: i quattro tipi in editor, admin, CSV e report; righe precedenti intatte.
- [x] **T27-2** Migrazione `0027_contribution_hidden` e modello. Test: upgrade/downgrade su SQLite, vincoli compatibili con SQL Server.
- [x] **T27-3** Helper batch `attendance_authorized` in `services/consents.py`. Test: concesso valido, revocato, negato, assente, versione precedente non riaccettata, due edizioni.
- [x] **T27-4** `GET /api/me/proposals` con accesso, esclusioni e proiezione dell'autore. Test: autore con consenso, anonimo senza; nessun id/email/telefono nel payload; escluse proprie, scadute, disdette, in lista d'attesa, nascoste, altra edizione; 401/403; filtro per tipo.
- [x] **T27-5** Admin: `hide`/`unhide` idempotenti con cronologia, colonna «Nascosta» in vista e CSV. Test: 403 per non admin, doppio invio, proposta nascosta fuori dalla consultazione ma visibile all'autore.
- [x] **T27-6** Frontend partecipante: comando, `ProposalsDialog`, filtro, stati e avviso sul testo libero. Test: apertura/chiusura e focus, anonimo, vuoto, errore, comando assente senza prenotazione attiva.
- [x] **T27-7** Frontend admin: nascondi/mostra con conferma e marcatura. Test.
- [x] **T27-8** Guide IT/EN (partecipante e admin), `test-manuali.md` pronto, suite completa, Ruff, lint, TypeScript, build e migrazioni da zero verdi.

Scostamenti rispetto al design: `GET /api/me/proposals` **non** usa `require_privacy_acceptance` (è una lettura, consentita anche con l'informativa pendente come le altre letture personali); gli endpoint admin stanno in `api/admin_contributions.py` (`POST /api/admin/contributions/{id}/hide|unhide`); «Nascondi» chiede conferma con motivo facoltativo, «Mostra di nuovo» è immediato; il comando «Proposte degli altri» sta nella sezione dei contributi della pagina personale (che compare con un'iscrizione modificabile) e per gli admin la consultazione è solo via API; il filtro per tipo è fatto dal server. La cronologia usa `AuditLog` (azioni `contribution_hidden` / `contribution_shown`) agganciato alla prenotazione dell'autore.
