# MVP 1 · Iscrizione base · Task

Divisione confermata: **Parte 1a** (task 1-12, tutto funzionante in locale con CI) e **Parte 1b** (task 13-14, deploy su Azure).

## Parte 1a · In locale

- [x] **1. Scaffold backend**: `pyproject.toml` con `uv` (Python 3.12), FastAPI, `config.py` da variabili d'ambiente, `GET /api/health`, ruff, pytest.
  Test: health risponde 200; config legge i valori d'ambiente.
- [x] **2. Scaffold frontend e app unica**: Vite + React + TypeScript, React Router, eslint, prettier, vitest; FastAPI serve la build con fallback SPA; `Dockerfile` multi-stage con ODBC Driver 18.
  Test: vitest di smoke sul router; pytest che una rotta SPA restituisce `index.html` e `/api/...` sconosciuto restituisce 404 JSON.
- [x] **3. Database e migrazione iniziale**: SQLAlchemy 2, Alembic, modelli del design, migrazione iniziale.
  Test: `alembic upgrade head` da zero e `downgrade base` senza errori (SQLite in locale, SQL Server in CI).
- [x] **4. Regole di dominio**: `compute_fee`, `effective_status`, `occupies_seats`, `available_seats`, `hold_deadline`, `can_reactivate`, `generate_personal_code`.
  Test: importo con giorni distinti e stesso giorno contato una volta; scadenza prima e dopo; stati che occupano posti; riattivazione; formato e alfabeto del codice.
- [x] **5. Magic link, sessione e admin seed**: `EmailSender` astratto e `ConsoleEmailSender`, magic link (hash, 30 minuti, monouso), `auth_session` con cookie 14 giorni, dipendenze `current_user` e `require_admin`, seed da `ADMIN_EMAIL`.
  Test: token scaduto, token riusato, risposta neutra per email sconosciuta, attributi del cookie, accesso admin negato a un partecipante, seed idempotente.
- [x] **6. Password**: hash argon2, `POST /api/auth/login`, `PUT /api/me/password`, `ADMIN_PASSWORD` opzionale nel seed.
  Test: password corta rifiutata, login corretto, errore identico per email sconosciuta, password errata e utente senza password.
- [x] **7. Impostazioni edizione**: API e pagina `/admin/impostazioni` per dati edizione, generazione slot, canali di pagamento, nuove versioni dei testi legali.
  Test: generazione slot dalle date; rifiuto della rimozione di giorni prenotati; versionamento dei testi.
- [x] **8. API iscrizione pubblica**: `GET /api/public/edition`, `POST /api/public/registrations` con lock sugli slot, CSP `frame-ancestors`.
  Test: capienza rispettata, slot pieno 409, posti liberati da prenotazione scaduta, email già iscritta (attiva e scaduta con o senza posto), versioni legali salvate, header CSP su `/iscrizione` e sulle altre pagine.
- [x] **9. Pagina di iscrizione**: modulo accessibile e mobile-first, posti liberi per slot, errori per campo, riepilogo con importo, causale, istruzioni, scadenza e link che si apre fuori dall'iframe.
  Test: vitest sul calcolo dell'anteprima dell'importo lato client.
- [x] **10. Accesso e pagina personale minima**: pagine `/accedi` (magic link e password), `/accedi/verifica`, `/io` con modulo password; `GET /api/me`.
  Test: `/api/me` senza sessione 401; con sessione restituisce saldo e scadenza corretti.
- [x] **11. Admin iscrizioni e pagamenti**: elenco con filtri e ricerca, scheda, registrazione pagamento, conferma automatica, riattivazione se c'è posto, avviso se non c'è, email di conferma in console.
  Test: pagamento parziale lascia `in_attesa_pagamento`; pagamento che copre conferma; pagamento su scaduta con posto riattiva; senza posto resta scaduta con avviso; saldo corretto; email inviata una volta.
- [x] **12. CI**: workflow `ci.yml` con ruff, pytest (anche su SQL Server come service container), eslint, vitest, build del frontend e dell'immagine.
  Test: la CI è verde sul branch.

## Parte 1a bis · Slot serale

- [x] **13. Slot serale**: terzo slot `evening` (default 19-24, orario di fine 00:00 = mezzanotte) senza limite di posti; migrazione 0002 con `evening_start/end` sull'edizione e `capacity` nullable sullo slot; API, pagina di iscrizione e impostazioni aggiornate; `available` assente per la sera.
  Test: generazione di tre slot al giorno; la sera accetta più persone della capienza; giorno con la sola sera conta nella quota; orari serali configurabili; mezzanotte come fine valida; la migrazione 0002 si applica e torna indietro; ordine mattina, pomeriggio, sera.

## Parte 1b · Deploy su Azure

- [ ] **14. Infrastruttura e deploy** (SCRITTO, NON VALIDATO: servono `az bicep build`, `what-if` e un primo deploy): Container App con minimo 0 repliche (si spegne se non usata, da ricordare al maintainer) e database Basic; `infra/main.bicep`, workflow `deploy.yml` con OIDC e GHCR, migrazioni all'avvio, istruzioni in `infra/README.md`.
  Test: `az bicep build` senza errori; deploy su una risorsa di prova; `GET /api/health` 200.
- [ ] **15. Verifica e chiusura** (IN ATTESA: sbloccare dopo alcuni MVP, decisione del maintainer): prova manuale completa dentro Google Sites, aggiornamento Memory Bank e README, descrizione PR con checklist per gli organizzatori.
