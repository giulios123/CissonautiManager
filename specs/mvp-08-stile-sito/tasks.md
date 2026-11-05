# MVP 8 · Stile del sito Cissone Eventi · Task

Branch di implementazione: `feat/mvp-08-stile-sito`. Indipendente dall'MVP 7: può partire appena il task 1 è chiuso. Se gli MVP 4-7 non sono ancora su `main`, il task 2 va ripetuto sulle loro pagine al momento dell'unione.

**Dimensione**: 7 task.

- [ ] **1. Raccolta dello stile** (bloccante): screenshot, colori, font, forma dei componenti e logo in `specs/mvp-08-stile-sito/stile.md`; conferma del maintainer.
  Richiede `sites.google.com` tra i domini consentiti dall'ambiente, oppure i materiali forniti a mano.
- [ ] **2. Token CSS**: palette su `:root`, tutti i colori scritti a mano sostituiti.
  Test: vitest sul contrasto delle coppie testo/sfondo, bottone/testo e bordo dei campi/sfondo; `grep` senza colori fuori da `:root`; test esistenti verdi.
- [ ] **3. Font e tipografia**: `@fontsource`, scala dei titoli, cifre tabellari negli importi.
  Test: build senza richieste esterne (controllo sul `dist/`); test esistenti verdi.
- [ ] **4. Componenti**: bottoni, campi, fieldset degli slot, checkbox, messaggi, `ConfirmDialog`.
  Test: altezza minima 44 px e focus visibile controllati negli screenshot; test esistenti verdi.
- [ ] **5. Pannello admin**: navigazione, tabelle, `CsvButton`, scheda della persona.
  Test: tabelle scorrevoli a 390 px senza scorrimento della pagina; test esistenti verdi.
- [ ] **6. Intestazione e modalità iframe**: `SiteHeader` con logo, classe `in-frame`.
  Test vitest: intestazione visibile fuori dall'iframe e nascosta con `in-frame`; logo con `alt`; nome in testo se il logo manca.
- [ ] **7. Verifica visiva e chiusura**: screenshot Playwright a 390 e 1280 px, anche dentro un iframe di prova, confrontati con il sito; lint e test verdi; Memory Bank aggiornata (`progress.md`, `activeContext.md`, `decisions.md`); descrizione PR con checklist per organizzatori.

## Da verificare a mano

- Aprire la pagina del sito con l'iframe, da telefono e da computer, e controllare che il modulo sembri parte della pagina.
- Fare un'iscrizione completa dal sito e una visita al pannello admin con il nuovo stile.
- Navigare il modulo di iscrizione solo con la tastiera.
