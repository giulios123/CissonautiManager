# Project brief

> Cambia raramente. Fonte: sezioni 1, 2 e 3 del prompt di progetto.

## Contesto

Il Cisonauti Summer Camp è un evento informale di circa una settimana in un salone polivalente comunale usato come coworking. Partecipano persone che si conoscono, amici di amici, passaparola: l'anno scorso 45 persone in totale, 25-28 presenti contemporaneamente. Non è un servizio commerciale: niente partita IVA né associazione, i contributi coprono i costi.

Problemi da risolvere:

- sapere quante persone ci sono di giorno nello spazio, ai pranzi, alle cene e alle attività;
- ridurre i drop (50% l'anno scorso) legando la conferma del posto al pagamento;
- dare agli organizzatori una vista completa e modificabile, "come un Excel navigabile".

## Vincoli

- Semplicità prima di tutto: lo mantengono volontari, budget quasi zero, hosting su crediti Azure.
- Open source su GitHub, licenza MIT. Chiunque può aprire issue e PR.
- Codice, nomi, commit e commenti in inglese. Memory Bank, spec, README e UI in italiano.
- UI solo in italiano, mobile-first, accessibile. Timezone Europe/Rome.
- Il repo deve funzionare con Claude Code, Codex e GitHub Copilot.

## Stack

- **App unica**: backend Python 3.12 con FastAPI che espone le API sotto `/api` e serve la build statica del frontend React (Vite + TypeScript). Un solo container, un solo deploy.
- **Database**: Azure SQL (serverless, free offer). SQLAlchemy 2 + Alembic, driver `pyodbc` con ODBC Driver 18. In locale SQL Server in `docker-compose`.
- **Email**: interfaccia astratta `EmailSender`; provider "console" in sviluppo, Azure Communication Services Email in produzione.
- **Hosting**: Azure Container Apps con scale to zero. IaC in Bicep, CI/CD con GitHub Actions.
- **Test**: pytest sul backend, con priorità alle regole di dominio (capienza, scadenze, importi, lista d'attesa). Vitest minimo sul frontend.
- **Qualità**: ruff, eslint + prettier.
