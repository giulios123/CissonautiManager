## Cosa cambia per gli organizzatori

- Nuova pagina **«Consegne»** nel menu admin: scegli un benefit del catalogo (accanto al nome, quanti ne hai consegnati e quante persone hanno diritto), cerca per nome, filtra «Da consegnare / Consegnati» e premi **«Consegna»** sulla riga. Restano registrati chi, quando e quale benefit.
- Hanno diritto gli iscritti attivi che sono interni non paganti, hanno la quota esentata o hanno versato (al netto dei rimborsi) almeno la quota base. Esterni, lista d'attesa, scaduti e disdetti no. Con quota base 0 non basta la sola soglia.
- Una sola consegna attiva per persona e benefit: un doppio clic o due organizzatori insieme non la duplicano.
- **«Annulla consegna…»** chiede un motivo obbligatorio; la consegna resta nello storico come annullata e si può registrare una nuova.
- Se la persona perde il diritto dopo la consegna (disdetta, categoria, rimborso), la consegna resta e la riga è marcata «Senza diritto attuale»; nessuna restituzione tracciata.
- Benefit ritirato: niente nuove consegne, storico leggibile. CSV con gli stessi filtri. I partecipanti non vedono nulla.

## Checklist di test manuali (per gli organizzatori)

Vedi [test-manuali.md](test-manuali.md) (12 passi, italiano e inglese).

## Dettagli tecnici

- Migrazione additiva `0029_benefit_delivery` (sopra la `0028`): tabella legata a persona, benefit ed edizione (non alla prenotazione), indice univoco filtrato `uq_benefit_delivery_active` (una consegna attiva per persona e benefit) e `uq_benefit_delivery_request_key`. **Da verificare nella CI SQL Server.**
- Regola pura `domain/benefits.py::is_entitled`, distinta dalla conferma base+giorni; servizio `services/benefit_deliveries.py` (idempotente per chiave e per consegna attiva, corsa gestita con `IntegrityError`); API `api/admin_deliveries.py` (solo admin, nessuna email, telefono, allergia o importo nei payload); cronologia in `AuditLog` agganciata alla prenotazione.
- Frontend `AdminDeliveries.tsx`, voce di menu e rotta `/admin/deliveries`; guida admin IT/EN (`17-deliveries`) e rimando in Impostazioni.
- Verificato in locale: test backend e frontend, Ruff, lint, TypeScript, build, controllo guida. **Da verificare:** CI SQL Server, prova visiva su telefono, collaudo organizzatori. Nessun deploy.
- Branch `feat/mvp-30-consegne-benefit`, impilato su `feat/mvp-29-proposta-attivita` (PR #32): conviene unire prima quella.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
