# MVP 22 · Task

- [x] T22-1 Confermare la spec e controllare compatibilità con il comportamento aggiornato del 18.
- [x] T22-2 Aggiungere chiave idempotente al pagamento e migrazione `0021`, verificata su SQLite.
- [x] T22-3 Implementare controllo sotto lock di chiave, payload e snapshot saldo/stato; restituire lo stesso pagamento nei retry identici.
- [x] T22-4 Estendere `AdminCollect` con modale bilingue, importo vuoto, canale/data precompilati, nota e riepilogo dei saldi.
- [x] T22-5 Gestire conflitto aggiornando lo snapshot senza perdere l'importo digitato e mantenere la chiave sui retry incerti.
- [x] T22-6 Collegare replay alla scadenza originaria dell'annullo e alla email differita/job.
- [x] T22-7 Aggiungere test API di snapshot/idempotenza e test UI di invio rapido.
- [ ] T22-8 Guide IT/EN e verifiche locali completate; SQL Server CI e collaudo manuale restano da eseguire.
