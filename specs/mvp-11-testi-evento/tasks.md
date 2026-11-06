# MVP 11 · Task

Branch: `feat/mvp-11-testi-evento`. **Dimensione**: 10 task.

- [x] **1. Spec**: questi file, voce in `ROADMAP.md`, `activeContext.md`.
- [x] **2. Migrazione 0011** + modelli. Test: su/giù da zero.
- [x] **3. Dominio `email_texts.py`**. Test: risoluzione, segnaposto, limiti.
- [x] **4. Email con testi** (`templates.py`, servizio, punti di invio). Test: oggetto con nome edizione, apertura/chiusura personalizzate, blocco invariato.
- [x] **5. API admin** `email-texts` e `registration_intro`. Test: 403, 404, ripristino, cronologia, pubblico.
- [x] **6. Accesso**: redirect `/io`, link 10 minuti riusabile, `Verify.tsx` senza clic, testi «30 minuti». Test: backend e `Access.test.tsx`.
- [x] **7. Nome evento** (`EventNameProvider`, header, titoli, home). Test.
- [x] **8. Paragrafo del modulo** in `Registration.tsx`. Test.
- [x] **9. Pagina `AdminTexts`**, menu, «La mia pagina», barra admin in `Personal.tsx`. Test.
- [x] **10. Chiusura**: guida, `progress`, `activeContext`, `decisions` (D-041), `domain.md`, `pr-description.md`.

## Da verificare a mano
- Rinomina l'edizione: intestazione, titolo scheda e oggetto delle email cambiano.
- Modifica il testo di un'email: arriva con il testo nuovo e il blocco dati intatto.
- Admin che entra: atterra su «La tua iscrizione» con il link al pannello.
- Link di accesso: si entra aprendolo, riaprendolo entro 10 minuti si entra ancora, dopo no.
