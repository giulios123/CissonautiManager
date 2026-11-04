# MVP 1 · Iscrizione base · Design

## Struttura dell'app

```
backend/
  app/
    main.py            FastAPI, router /api, file statici e fallback SPA
    config.py          impostazioni da variabili d'ambiente
    db.py              engine e sessioni SQLAlchemy
    models.py          modelli SQLAlchemy
    domain/            regole pure: importi, stati, disponibilità, codice personale
    api/               router: public, auth, me, admin
    email/             EmailSender + ConsoleEmailSender
  alembic/
  tests/
frontend/
  src/pages/           Iscrizione, Accedi, Verifica, Io, Admin*
Dockerfile             multi-stage: build frontend, poi Python + ODBC Driver 18
infra/main.bicep
.github/workflows/     ci.yml, deploy.yml
```

## Modello dati (migrazione iniziale unica)

| Tabella | Campi principali |
|---------|------------------|
| `edition` | id, name, start_date, end_date, morning_start/end, afternoon_start/end, evening_start/end, default_capacity, hold_days, base_fee_cents, per_day_fee_cents, is_active |
| `slot` | id, edition_id, date, period (`morning`/`afternoon`/`evening`), start_time, end_time, capacity (nullable: vuoto = senza limite, usato dalla sera) |
| `participant` | id, first_name, last_name, email (unica), phone, invited_by, can_bring, personal_code (unico), role (`participant`/`admin`), password_hash (nullable), created_at |
| `booking` | id, edition_id, participant_id, status, hold_expires_at, amount_due_cents, privacy_document_id, privacy_accepted_at, disclaimer_document_id, disclaimer_accepted_at, created_at |
| `booking_slot` | booking_id, slot_id |
| `payment` | id, booking_id, amount_cents, channel, paid_on, note, recorded_by_id, created_at |
| `payment_channel` | id, edition_id, code (`revolut`/`satispay`/`paypal`/`iban`), label, instructions, enabled, sort_order |
| `legal_document` | id, edition_id, kind (`privacy`/`disclaimer`), version, body, published_at |
| `magic_link_token` | id, participant_id, token_hash, expires_at, used_at |
| `auth_session` | id, participant_id, token_hash, expires_at, created_at |

- Il campo `waitlist_pct` e i prezzi dei pasti si aggiungono con migrazioni negli MVP 4 e 5.
- `amount_due_cents` è salvato al momento dell'iscrizione e ricalcolato a ogni modifica degli slot (MVP 2).
- Token e sessioni sono salvati solo come hash SHA-256.

## Regole di dominio (funzioni pure in `app/domain/`)

- `compute_fee(slot_dates, base, per_day) -> int`: base + per_day x giorni distinti.
- `effective_status(booking, paid_cents, now) -> Status`: `in_attesa_pagamento` scaduta diventa `scaduta`.
- `occupies_seats(status) -> bool`: vero per `in_attesa_pagamento` non scaduta e `confermata`.
- `available_seats(capacity, occupied) -> int`.
- `generate_personal_code() -> str`: `CSC-` + 4 caratteri da un alfabeto senza caratteri ambigui (niente 0, O, 1, I, L).
- `hold_deadline(created_at, hold_days) -> datetime`: created_at + hold_days x 24 ore.
- `can_reactivate(status, free_seats_per_slot) -> bool`: una prenotazione `scaduta` si riattiva solo se tutti i suoi slot hanno posto.

Quando una prenotazione viene letta ed è scaduta, lo stato viene anche scritto in DB (materializzazione pigra), così elenco e filtri restano coerenti.

## Endpoint

| Metodo e path | Accesso | Scopo |
|---------------|---------|-------|
| `GET /api/health` | pubblico | stato app e DB |
| `GET /api/public/edition` | pubblico | edizione attiva, slot con posti liberi, quote, testi legali correnti, canali attivi |
| `POST /api/public/registrations` | pubblico | crea partecipante e prenotazione, risponde con il riepilogo |
| `POST /api/auth/magic-link` | pubblico | invia il link (risposta neutra) |
| `POST /api/auth/verify` | pubblico | consuma il token, imposta il cookie |
| `POST /api/auth/login` | pubblico | accesso con email e password |
| `POST /api/auth/logout` | sessione | chiude la sessione |
| `PUT /api/me/password` | sessione | imposta o cambia la password |
| `GET /api/me` | sessione | dati e riepilogo della prenotazione |
| `GET`, `PUT /api/admin/edition` | admin | impostazioni dell'edizione e generazione degli slot |
| `PUT /api/admin/payment-channels` | admin | canali e istruzioni |
| `POST /api/admin/legal-documents` | admin | nuova versione di un testo legale |
| `GET /api/admin/registrations` | admin | elenco con filtri |
| `GET /api/admin/registrations/{id}` | admin | scheda |
| `POST /api/admin/registrations/{id}/payments` | admin | registra un pagamento |

## Pagine

- `/iscrizione`: modulo pubblico, unica pagina con CSP `frame-ancestors https://sites.google.com https://*.googleusercontent.com`. Tutte le altre risposte hanno `frame-ancestors 'self'`.
- `/accedi`: richiesta del magic link oppure accesso con email e password.
- `/accedi/verifica?token=...`: pagina con il pulsante «Entra» che invia il token con una POST. Il token non si consuma al caricamento della pagina, così i client email e gli scanner che pre-aprono i link non lo bruciano.
- `/io`: pagina personale in sola lettura, con il modulo per impostare la password.
- `/admin`, `/admin/iscrizioni/:id`, `/admin/impostazioni`.

## Flussi

**Iscrizione**: validazione input, poi in un'unica transazione lock sugli slot scelti (`SELECT ... FOR UPDATE` di SQLAlchemy, che su SQL Server diventa `WITH (UPDLOCK, ROWLOCK)`), conteggio dei posti occupati, eventuale errore 409 con gli slot pieni, creazione di partecipante (o riuso per email) e prenotazione, calcolo importo e scadenza, invio email dopo il commit.

**Magic link**: generazione token casuale (`secrets.token_urlsafe`), salvataggio dell'hash, link `APP_BASE_URL/accedi/verifica?token=...`. Nell'email il link è assoluto e la pagina di riepilogo lo apre con `target="_blank"`, così esce dall'iframe.

**Pagamento**: inserimento del pagamento, somma dei pagamenti, se copre l'importo stato `confermata` ed email di conferma.

## Infrastruttura

- Bicep in `infra/main.bicep`: Log Analytics, Container Apps Environment, Container App (min 0 repliche), Azure SQL server + database serverless con free offer.
- Immagine su GitHub Container Registry (gratuito per repo pubblici).
- `deploy.yml`: login Azure con OIDC, build e push immagine, `az deployment group create`, migrazioni Alembic all'avvio del container.
- Segreti (`DATABASE_URL`, `SECRET_KEY`, `ADMIN_EMAIL`) come secret della Container App, valorizzati dai secret di GitHub.

## Scelte tecniche proposte

Da registrare in `decisions.md` quando vengono implementate: password hashate con argon2 (`argon2-cffi`); `uv` per le dipendenze Python; test di dominio puri; test di integrazione su SQLite in memoria di default e su SQL Server quando è impostata `TEST_DATABASE_URL` (service container in CI), perché negli ambienti senza Docker SQL Server non gira; sessioni in tabella DB invece di cookie firmati (revocabili); immagine su GHCR invece di Azure Container Registry (costo zero); migrazioni all'avvio del container.

## Impatti sugli MVP precedenti

Nessuno: è il primo MVP. Anticipa dall'MVP 2 il login con magic link e cookie da 14 giorni, perché serve all'admin.
