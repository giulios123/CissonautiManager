# MVP 1 · Iscrizione base · Task

I task sono 13, oltre la soglia di circa 10. Proposta di divisione: **Parte 1a** (task 1-11, tutto funzionante in locale con CI) e **Parte 1b** (task 12-13, deploy su Azure). In attesa di conferma.

## Parte 1a · In locale

- [ ] **1. Scaffold backend**: `pyproject.toml` con `uv`, FastAPI, `config.py` da variabili d'ambiente, `GET /api/health`, ruff, pytest.
  Test: health risponde 200; config legge `.env.example` senza errori.
- [ ] **2. Scaffold frontend e app unica**: Vite + React + TypeScript, React Router, eslint, prettier, vitest; FastAPI serve la build con fallback SPA; `Dockerfile` multi-stage con ODBC Driver 18.
  Test: vitest di smoke sul router; pytest che una rotta SPA restituisce `index.html` e `/api/...` sconosciuto restituisce 404 JSON.
- [ ] **3. Database e migrazione iniziale**: SQLAlchemy 2, Alembic, modelli del design, creazione del database se assente, migrazione iniziale.
  Test: `alembic upgrade head` da zero su SQL Server in docker; downgrade e nuovo upgrade senza errori.
- [ ] **4. Regole di dominio**: `compute_fee`, `effective_status`, `occupies_seats`, `available_seats`, `hold_deadline`, `generate_personal_code`.
  Test: importo con giorni distinti e stesso giorno contato una volta; scadenza prima e dopo; stati che occupano posti; formato e alfabeto del codice.
- [ ] **5. Auth e admin seed**: `EmailSender` astratto e `ConsoleEmailSender`, magic link (hash, 30 minuti, monouso), `auth_session` con cookie 14 giorni, dipendenze `current_user` e `require_admin`, seed da `ADMIN_EMAIL`.
  Test: token scaduto, token riusato, risposta neutra per email sconosciuta, attributi del cookie, accesso admin negato a un partecipante, seed idempotente.
- [ ] **6. Impostazioni edizione**: API e pagina `/admin/impostazioni` per dati edizione, generazione slot, canali di pagamento, nuove versioni dei testi legali.
  Test: generazione slot dalle date; rifiuto della rimozione di giorni prenotati; versionamento dei testi.
- [ ] **7. API iscrizione pubblica**: `GET /api/public/edition`, `POST /api/public/registrations` con lock sugli slot, CSP `frame-ancestors`.
  Test: capienza rispettata (anche con due iscrizioni concorrenti sull'ultimo posto), slot pieno 409, posti liberati da prenotazione scaduta, email duplicata, versioni legali salvate, header CSP su `/iscrizione` e sulle altre pagine.
- [ ] **8. Pagina di iscrizione**: modulo accessibile e mobile-first, posti liberi per slot, errori per campo, riepilogo con importo, causale, istruzioni, scadenza e link che si apre fuori dall'iframe.
  Test: vitest sul calcolo dell'anteprima dell'importo lato client.
- [ ] **9. Accesso e pagina personale minima**: pagine `/accedi`, `/accedi/verifica`, `/io`; `GET /api/me`.
  Test: `/api/me` senza sessione 401; con sessione restituisce saldo e scadenza corretti.
- [ ] **10. Admin iscrizioni e pagamenti**: elenco con filtri e ricerca, scheda, registrazione pagamento, conferma automatica, email di conferma in console.
  Test: pagamento parziale lascia `in_attesa_pagamento`; pagamento che copre conferma; saldo corretto; email inviata una volta.
- [ ] **11. CI**: workflow `ci.yml` con ruff, pytest (SQL Server come service container), eslint, vitest, build del frontend e dell'immagine.
  Test: la CI è verde sul branch.

## Parte 1b · Deploy su Azure

- [ ] **12. Infrastruttura e deploy**: `infra/main.bicep`, workflow `deploy.yml` con OIDC e GHCR, migrazioni all'avvio, istruzioni in `infra/README.md`.
  Test: `az bicep build` senza errori; deploy su una risorsa di prova; `GET /api/health` 200.
- [ ] **13. Verifica e chiusura**: prova manuale completa dentro Google Sites, aggiornamento Memory Bank e README, descrizione PR con checklist per gli organizzatori.
