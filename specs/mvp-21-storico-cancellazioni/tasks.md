# MVP 21 · Task

- [x] T21-1 Confermare la spec e l'ordine di rilascio; rinviare il criterio di conservazione a prima del rilascio in produzione.
- [x] T21-2 Estendere il modello audit con migrazione additiva `0020`; verificare upgrade/downgrade SQLite da zero e da `0019`.
- [x] T21-3 Registrare atomicamente disdette autonome e admin con persona, edizione, autore, timestamp ed esito; mantenere una sola voce per evento.
- [x] T21-4 Aggiungere `GET /api/admin/registrations/cancellations`, filtro per nome/email e paginazione stabile protetta da admin.
- [x] T21-5 Aggiungere vista e collegamento «Storico cancellazioni» con testi IT/EN, data Europe/Rome e stati accessibili.
- [x] T21-6 Aggiornare la cronologia della scheda e le guide admin IT/EN; suite, migrazione SQL Server, Ruff, frontend, build e controllo Guide CI completati.
- [x] T21-7 Collaudo manuale A6 completato dal maintainer; esiti confermati l'8 novembre 2026.
