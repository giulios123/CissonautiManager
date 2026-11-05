# MVP 9 · Guida in app e note di rilascio · Design

Nessuna modifica al modello dati né migrazioni. Nessun impatto su `domain.md`.

## Contenuti

`frontend/src/guide/partecipante/NN-slug.md` e `frontend/src/guide/admin/NN-slug.md`: una sezione per file, prima riga `# Titolo`, ordine dal prefisso numerico. `content.ts` li carica con `import.meta.glob(..., { query: "?raw" })`: la guida partecipante è eager, quella admin è lazy, così il suo chunk lo scarica solo chi apre la scheda. `parseSections` (pura) produce `{ slug, title, body }[]`. Mappa percorso admin → slug per l'aiuto contestuale.

Rendering con `marked`: i testi sono del repo, non input utente. Il sorgente non finisce mai in un `innerHTML` se non passa da `marked`.

## Pagina

`/guida` sotto `RequireLogin`, `Guide.tsx` usa `useMe()`. Partecipante: indice con ancore e sezioni. Admin: tablist accessibile (frecce, Home, End), pannello attivo per `?scheda=` e `#sezione`. Fondo pagina: versione da `GET /api/version`. Link «Guida» in `Personal.tsx` e nel menu di `AdminLayout.tsx`.

## Backend

- `Settings`: `app_version` (default `dev`), `built_at` (opzionale), `release_notes_path` (default `release_notes.json`).
- `GET /api/version` (pubblico, solo versione e data) e `GET /api/admin/release-notes` (`require_admin`). File assente o illeggibile → `{ "releases": [] }`.
- Formato: `{ "releases": [{ "version": "<sha>", "date": "<ISO>", "features": [..], "fixes": [..] }] }`.

## Generazione delle note

`scripts/release_notes.py`: `build_notes(commits)` pura. Legge `git log --first-parent`: ogni merge su `main` è un rilascio; i commit unitari sono quelli del ramo (`merge^1..merge^2`). Tiene `feat`, `fix`, `perf`; toglie prefisso e scope; ultimi 30 rilasci. Commit diretti su `main` senza merge formano un rilascio a sé.

`deploy.yml`: `fetch-depth: 0`, genera il JSON in `backend/app/`, `Dockerfile` riceve `APP_VERSION` e `BUILT_AT` come `ARG` → `ENV`. `release_notes.json` è in `.gitignore`.

## Regola e CI

Job `guide` in `ci.yml` solo su `pull_request`: se il diff tocca `frontend/src/pages/` o `backend/app/api/` ma non `frontend/src/guide/`, fallisce; salta con la label `senza-guida`. Regola in `AGENTS.md`.

## Rischi

- Il job CI è euristico: non sa se la guida è davvero corretta, solo che è stata toccata.
- Note di rilascio dipendono dalla qualità dei messaggi di commit.
