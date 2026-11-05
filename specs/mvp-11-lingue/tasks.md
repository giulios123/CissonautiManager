# MVP 11 · Lingue e indirizzi · Task

Branch: `claude/relaxed-dijkstra-9z2e5o` (vincolo della sessione). **Dimensione**: 8 task.

- [x] **1. Spec** dei tre MVP (11, 12, 13), `ROADMAP.md`, `activeContext.md`, regola «bilingue da subito» in `AGENTS.md`.
- [x] **2. Rotte**: `routes.ts`, alias con redirect, link, `pageTitle.ts`, `guide/content.ts`, URL del backend e CSP.
  Test: `canonicalPath`, redirect che conserva query e hash, CSP su `/register` e `/iscrizione`, magic link `/login/verify`.
- [x] **3. Core i18n**: dizionari, provider, rilevamento, selettore, formattatori.
  Test: rilevamento (`?lang`, storage, browser), selettore, parità delle chiavi, `localStorage` che lancia.
- [x] **4. Backend**: migrazione 0011, `locale` in registrazione e `PUT /api/me/locale`, `AppError` e catalogo, conversione degli 81 messaggi.
  Test: errore in inglese con `Accept-Language: en`, lingua salvata, migrazione da zero e downgrade.
- [x] **5. Email IT/EN** e `timefmt` per lingua.
  Test: ogni email in inglese, lingua del partecipante rispettata, oggetto con il nome dell'edizione.
- [ ] **6. Pagine partecipante tradotte**.
  Test: iscrizione, accesso e pagina personale in inglese.
- [ ] **7. Guida**: nuova struttura `{it,en}/{participant,admin}`, guida partecipante in inglese, test di parità, `check-guide.sh`.
- [ ] **8. Chiusura**: lint, test, migrazioni da zero, `progress.md`, `activeContext.md`, `decisions.md`, `domain.md`, `pr-description.md`.

## Da verificare a mano

- Da telefono: selettore IT/EN, iscrizione in inglese, email in inglese nella casella, vecchio link `/accedi/verifica`.
- Iframe di Google Sites su `/iscrizione` e su `/register`.
