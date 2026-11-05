# AGENTS.md

Istruzioni per gli agent (Claude Code, Codex, GitHub Copilot). Questo file è la fonte unica: `CLAUDE.md` e `.github/copilot-instructions.md` rimandano qui.

## Il progetto in tre righe

Cissonauti Booking gestisce le iscrizioni al Cissonauti Summer Camp: slot di coworking, pasti, attività e pagamenti registrati a mano.
App unica: FastAPI (Python 3.12) espone le API sotto `/api` e serve la build statica di un frontend React (Vite + TypeScript).
Database Azure SQL (SQL Server in locale), deploy su Azure Container Apps, open source con licenza MIT.

## Comandi

```bash
# Setup
cp .env.example .env
# Optional: SQL Server in Docker. Without it the app uses a local SQLite file (default DATABASE_URL).
docker compose up -d db
cd backend && uv sync
cd frontend && npm ci

# Run locale (due terminali)
cd backend && uv run alembic upgrade head && uv run uvicorn app.main:app --reload   # API su http://localhost:8000
cd frontend && npm run dev                             # UI su http://localhost:5173, proxy /api verso 8000

# Test
cd backend && uv run pytest                       # SQLite; con TEST_DATABASE_URL gira su SQL Server
cd frontend && npm test

# Lint e formattazione
cd backend && uv run ruff check . && uv run ruff format --check .
cd frontend && npm run lint

# Job dei promemoria di pagamento (in produzione gira ogni ora come Container Apps Job)
cd backend && uv run python -m app.jobs.send_reminders

# Note di rilascio (in produzione le genera il deploy; serve la storia git completa)
python scripts/release_notes.py --out backend/release_notes.json

# Migrazioni
cd backend && uv run alembic upgrade head
cd backend && uv run alembic revision --autogenerate -m "short description"

# Build di produzione (un solo container)
docker build -t cissonauti-booking .
```

## Convenzioni di codice

- Codice, nomi, commit e commenti in **inglese**. Memory Bank, spec e README in **italiano**. I testi della UI, le email e la guida sono in **italiano e inglese** (vedi la regola «Bilingue da subito»).
- Commit in formato Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`).
- Backend: FastAPI, SQLAlchemy 2 (stile tipizzato `Mapped[...]`), Alembic, Pydantic per input e output. Le regole di dominio stanno in funzioni pure, testabili senza database.
- Importi sempre in centesimi interi (`int`), mai `float`.
- Date e orari salvati in UTC; mostrati e interpretati in `Europe/Rome`.
- Frontend: React + TypeScript strict, mobile-first, accessibile (etichette sui campi, contrasto, navigazione da tastiera).
- Qualità: ruff sul backend, eslint + prettier sul frontend. Lint e test devono essere verdi prima di ogni commit.
- Configurazione solo da variabili d'ambiente, documentate in `.env.example`.

## Regole

- Niente fuori dalla spec dell'MVP corrente: le idee nuove vanno nel Backlog di `specs/ROADMAP.md`.
- Ogni regola di dominio ha almeno un test.
- Ogni modifica allo schema passa da una migrazione Alembic.
- Nessun segreto nel repo: configurazione tramite variabili d'ambiente con un `.env.example`.
- Ogni modifica a una funzione visibile (pagine in `frontend/src/pages/`, API in `backend/app/api/`) aggiorna la sezione giusta della guida in `frontend/src/guide/{it,en}/` (`participant/` o `admin/`, un file Markdown per sezione e per lingua, con lo stesso nome). Il controllo `Guide` della CI fallisce se una PR tocca pagine o API senza toccare la guida in tutte e due le lingue; se non cambia nulla di visibile, si salta con la label `senza-guida`. La guida si pubblica con ogni deploy, le note di rilascio sono generate dai commit (Conventional Commits fatti bene = note leggibili).
- **Bilingue da subito**: ogni funzione nuova o modificata nasce in italiano e in inglese (testi della UI nei dizionari `frontend/src/i18n/{it,en}.ts`, messaggi del server e email nel catalogo `backend/app/i18n.py`, guida in `frontend/src/guide/{it,en}/`). Gli indirizzi (rotte) sono solo in inglese, definiti in `frontend/src/routes.ts`; un alias italiano esiste solo se serve a non rompere link già in circolazione. Una PR che aggiunge testi in una lingua sola non è completa.
- `memory-bank/domain.md` è la fonte di verità: se una spec la contraddice, vince `domain.md` finché non viene aggiornato con il consenso del maintainer.

## Come iniziare ogni sessione

* Se `memory-bank/` non esiste: esegui la Parte A · Bootstrap.
* Se esiste: leggi tutta `memory-bank/` e `specs/ROADMAP.md`, poi esegui la Parte B · Ciclo MVP sull'MVP che ti viene indicato. Se non te ne viene indicato uno, prendi il primo non completato.

## Parte B · Ciclo MVP

### B0. Controllo

Verifica in `progress.md` che l'MVP precedente sia completato. Se non lo è, dimmelo e fermati.

### B1. Spec

1. Crea `specs/mvp-NN-<slug>/` con:
   * `requirements.md`: user story numerate con criteri di accettazione "Quando ... allora ...";
   * `design.md`: modifiche al modello dati e migrazioni, endpoint, pagine, flussi, impatti sugli MVP precedenti;
   * `tasks.md`: checklist ordinata di task piccoli e verificabili, con i test previsti.
2. Rispetta `domain.md`. Se l'MVP richiede di cambiare una regola, scrivi la modifica proposta in una sezione "Modifiche a domain.md" e non applicarla.
3. Tieni l'MVP piccolo: se supera circa 10 task, proponi come dividerlo.
4. Aggiorna `activeContext.md`.
5. Riassumi la spec in massimo 10 righe, elenca le domande aperte e fermati in attesa della mia conferma.

### B2. Implementazione

1. Crea il branch `feat/mvp-NN-<slug>`.
2. Procedi un task alla volta: implementa, scrivi i test, esegui test e lint, spunta il task in `tasks.md` e fai il commit (Conventional Commits, in inglese).
3. Se emerge qualcosa fuori scope, aggiungilo al Backlog senza implementarlo.
4. Se una scelta tecnica non è banale, aggiungi una voce in `decisions.md`.
5. Se ti blocchi o la spec si rivela sbagliata, fermati e chiedimi invece di improvvisare.

### B3. Chiusura

1. Tutti i test e il lint sono verdi, le migrazioni si applicano da zero senza errori.
2. Aggiorna:
   * `progress.md`: MVP completato e cosa va verificato a mano;
   * `activeContext.md`: prossimo MVP e dubbi aperti;
   * `domain.md`: solo le modifiche approvate;
   * `README.md` e `AGENTS.md`: se sono cambiati setup o comandi;
   * la guida in `frontend/src/guide/{it,en}/`: se è cambiata una funzione visibile.
3. Prepara la descrizione della PR con una checklist di test manuali scritta per gli organizzatori, non per sviluppatori.
4. Riassumimi il lavoro in massimo 10 righe.

### Regole sempre valide

* Niente refactor o feature non richiesti dalla spec.
* Codice in inglese; testi della UI, email e guida in italiano e inglese; documentazione (memory bank, spec, README) in italiano.
* Nessun segreto nel repo.
* Bug o piccole richieste fuori MVP: se è un bug, correggilo con un test che lo riproduce e annotalo in `progress.md`; altrimenti mettilo nel Backlog.
