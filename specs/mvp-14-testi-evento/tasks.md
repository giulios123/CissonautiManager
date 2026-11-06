# MVP 14 · Task

Branch: `feat/mvp-11-testi-evento` (PR #14, nome dal primo giro). **Dimensione**: 9 task.

- [x] **1. Spec**: questi file, voce in `ROADMAP.md`, `activeContext.md`.
- [x] **2. Migrazione 0013** e modello. Test: su/giù da zero, modelli e migrazioni allineati.
- [x] **3. Testi e template**: `EmailTexts`, dizionari spezzati, `templates.py`. Test: oggetto con il nome dell'edizione, apertura scritta, dati intatti.
- [x] **4. Servizio e punti di invio**. Test: lingua del destinatario, segnaposto, ripiego senza edizione.
- [x] **5. API admin e pubblica**. Test: 401/403/404, segnaposto sconosciuto, limiti, primo salvataggio concorrente, testo del modulo per lingua.
- [x] **6. Accesso**: redirect `/me`, link da 10 minuti riusabile. Test: riuso, scadenza, primo uso registrato una volta.
- [x] **7. Nome evento**: provider, intestazione, titoli, home. Test.
- [x] **8. Pagine**: `Verify` senza clic, barra admin, «La mia pagina», paragrafo del modulo, `AdminEmailTexts`. Test.
- [x] **9. Chiusura**: guida it/en, `progress`, `activeContext`, `decisions` (D-047), `domain.md`, `pr-description.md`.

## Da verificare a mano
- Rinomina l'edizione: intestazione, titolo scheda e oggetto delle email cambiano.
- Modifica il testo di un'email in italiano e in inglese: ogni persona riceve quello della sua lingua, con i dati intatti.
- Admin che entra: atterra su «Ciao …!» con il pulsante verso il pannello.
- Link di accesso: si entra aprendolo, riaprendolo entro 10 minuti si entra ancora, dopo no.
