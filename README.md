# Cissonauti Booking

Gestione delle iscrizioni al **Cissonauti Summer Camp**, una settimana di coworking informale in un salone comunale tra amici e amici di amici.

L'app serve a sapere quante persone ci sono ogni giorno nello spazio, ai pasti e alle attività, a ridurre le rinunce legando il posto al pagamento e a dare agli organizzatori una vista completa e modificabile.

## Stato

MVP 1 completato salvo la verifica dentro Google Sites: iscrizione pubblica, accesso con magic link o password, impostazioni dell'edizione, elenco iscrizioni e registrazione dei pagamenti, deploy su Azure. MVP 2 (pagina personale) implementato: il partecipante cambia i suoi slot, vede il saldo e disdice da solo, le email partono davvero e due promemoria di pagamento escono da un job orario. MVP 3 (pannello admin) implementato: viste per persona, giorno e slot, settimana e pagamenti da verificare con export CSV, gestione degli admin, rimborsi, modifica manuale delle iscrizioni e annullamento dei pagamenti, con cronologia. MVP 4 (lista d'attesa) implementato: chi trova uno slot pieno si mette in lista dal modulo o dalla pagina personale e riceve il posto, con un'email, appena si libera. MVP 5 (pranzi e cene) implementato: dalla pagina personale si scelgono pranzi e cene con l'importo aggiornato, si indicano regime e allergie (con consenso specifico) e gli organizzatori hanno la vista per pasto con CSV. Lo stato aggiornato è in [`memory-bank/progress.md`](memory-bank/progress.md), la roadmap in [`specs/ROADMAP.md`](specs/ROADMAP.md).

## Come è organizzato il repo

- `AGENTS.md`: istruzioni per chi sviluppa con Claude Code, Codex o GitHub Copilot (e utili anche agli umani).
- `memory-bank/`: contesto del progetto, regole di dominio, decisioni, avanzamento.
- `specs/`: roadmap e una cartella per ogni MVP con requisiti, design e task.
- `backend/`: FastAPI (Python 3.12), API sotto `/api`.
- `frontend/`: React con Vite e TypeScript, servito dal backend.
- `infra/`: infrastruttura Azure in Bicep.

## Avvio in locale

I comandi sono in [`AGENTS.md`](AGENTS.md#comandi). In breve: copia `.env.example` in `.env` (imposta `ADMIN_EMAIL` e `ADMIN_PASSWORD`), applica le migrazioni, avvia backend e frontend. Senza Docker l'app usa un file SQLite locale. Le email in sviluppo compaiono nel log del backend.

## Contribuire

Issue e pull request sono benvenute. Prima di proporre una modifica leggi `AGENTS.md` e `memory-bank/domain.md`: le idee fuori dall'MVP corrente vanno nel Backlog di `specs/ROADMAP.md`.

## Licenza

[MIT](LICENSE)
