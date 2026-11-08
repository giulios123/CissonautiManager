# MVP 21 e 22 · Storico cancellazioni e incasso rapido

## Cosa include

- **MVP 21 · Storico cancellazioni:** vista admin delle disdette dell'edizione corrente, ricerca per nome/email, autore ed esito; registro atomico delle nuove disdette e conservazione per un anno, con pulizia nel job orario.
- **MVP 22 · Incasso rapido:** modale «Altro importo» in «Da incassare», snapshot per evitare incassi su saldi cambiati, retry idempotente, annullo entro 10 secondi ed email differita di 30 secondi.
- Testi e guide aggiornati in italiano e inglese; migrazioni additive `0020` e `0021`.

## Verifiche automatiche

- [x] Suite backend completa: 1106 test passati.
- [x] Suite frontend: 407 test passati; lint, TypeScript e build passati.
- [x] Ruff e formattazione backend passati.
- [x] Migrazioni SQLite da zero e da `0019` verificate.
- [x] Verifica SQL Server confermata dal maintainer.
- [ ] CI della PR completata.

## Collaudo per gli organizzatori

- [x] A6: provate disdette autonome e admin, con e senza versamenti, inclusi posti, rimborso, reiscrizione, duplicati e accesso non admin.
- [x] MVP 22: collaudo manuale completato dal maintainer.
- [ ] Dopo il deploy, verificare accesso admin e ricerca delle disdette rimosse.
- [ ] Dopo il deploy, verificare pagamento parziale, conferma quota con extra residui, annullo, ritentativo e una sola email.

Gli esiti di CI e collaudo sono separati dallo stato del deploy. Nessun deploy è incluso in questa PR.
