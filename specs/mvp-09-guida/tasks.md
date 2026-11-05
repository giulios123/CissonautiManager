# MVP 9 · Guida in app e note di rilascio · Task

Branch: `claude/dreamy-ride-bzr112` (vincolo di push della sessione). **Dimensione**: 10 task.

- [x] **1. Spec**: questi tre file, voce in `ROADMAP.md`, `activeContext.md`.
- [x] **2. Backend**: impostazioni, `GET /api/version`, `GET /api/admin/release-notes`.
  Test: admin 200, partecipante 403, anonimo 401, file assente → lista vuota, file corrotto → lista vuota.
- [x] **3. Script delle note**: `scripts/release_notes.py`.
  Test: merge come rilascio, filtro dei tipi, scope tolto, ordine, limite di 30, commit diretto.
- [ ] **4. Deploy e Dockerfile**: `fetch-depth: 0`, generazione, `APP_VERSION` e `BUILT_AT`; `.gitignore`, `.env.example`.
- [ ] **5. Contenuti**: `content.ts` e `parseSections`, dipendenza `marked`.
  Test: ordinamento, titolo dalla prima riga, slug, file senza titolo.
- [ ] **6. Pagina `/guida`**: filtro per ruolo, schede admin, versione.
  Test: partecipante senza schede e senza chiamata alle novità; admin con tre schede; novità vuote; tastiera sulle schede; anonimo a `/accedi`.
- [ ] **7. Link**: da pagina personale e menu admin con sezione contestuale; titolo di pagina.
  Test: `titleFor("/guida")`; link con la sezione giusta.
- [ ] **8. Testi**: guida partecipante e organizzatori, controllata sulle pagine reali.
- [ ] **9. Regola e CI**: `AGENTS.md`, job `guide`.
- [ ] **10. Chiusura**: lint e test verdi, build Docker con `APP_VERSION`, `progress.md`, `activeContext.md`, `decisions.md`, `README.md`, `pr-description.md`.

## Da verificare a mano

- Dopo il deploy: «Novità» mostra i rilasci veri e la versione coincide con l'ultimo commit su `main`.
- Da telefono: schede e indice usabili, nessuno scorrimento laterale.
