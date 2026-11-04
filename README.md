# Cisonauti Booking

Gestione delle iscrizioni al **Cisonauti Summer Camp**, una settimana di coworking informale in un salone comunale tra amici e amici di amici.

L'app serve a sapere quante persone ci sono ogni giorno nello spazio, ai pasti e alle attività, a ridurre le rinunce legando il posto al pagamento e a dare agli organizzatori una vista completa e modificabile.

## Stato

Progetto appena avviato: ci sono la documentazione e la spec del primo MVP, il codice arriva con l'MVP 1. Lo stato aggiornato è in [`memory-bank/progress.md`](memory-bank/progress.md), la roadmap in [`specs/ROADMAP.md`](specs/ROADMAP.md).

## Come è organizzato il repo

- `AGENTS.md`: istruzioni per chi sviluppa con Claude Code, Codex o GitHub Copilot (e utili anche agli umani).
- `memory-bank/`: contesto del progetto, regole di dominio, decisioni, avanzamento.
- `specs/`: roadmap e una cartella per ogni MVP con requisiti, design e task.
- `backend/`: FastAPI (Python 3.12), API sotto `/api`.
- `frontend/`: React con Vite e TypeScript, servito dal backend.
- `infra/`: infrastruttura Azure in Bicep.

## Avvio in locale

I comandi sono in [`AGENTS.md`](AGENTS.md#comandi). In breve: copia `.env.example` in `.env`, avvia il database con `docker compose up -d db`, poi backend e frontend.

## Contribuire

Issue e pull request sono benvenute. Prima di proporre una modifica leggi `AGENTS.md` e `memory-bank/domain.md`: le idee fuori dall'MVP corrente vanno nel Backlog di `specs/ROADMAP.md`.

## Licenza

[MIT](LICENSE)
