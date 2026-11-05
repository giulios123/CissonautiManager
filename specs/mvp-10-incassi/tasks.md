# MVP 10 · Incassi (controllo del conto) · Task

Branch: `claude/brave-babbage-ttfx6u` (vincolo di push della sessione). **Dimensione**: 10 task.

- [x] **1. Spec**: questi tre file, voce in `ROADMAP.md`, `activeContext.md`.
- [x] **2. Regola `to_collect`** in `domain/payments_review.py`.
  Test: in attesa a zero, in attesa parziale, confermata con saldo, confermata coperta (no), confermata in credito (no), scaduta (sì, in coda), disdetta e rimborsata (no), ordine per scadenza.
- [x] **3. Servizio e endpoint** `GET /api/admin/views/to-collect`.
  Test: admin 200, partecipante 403, anonimo 401, senza edizione attiva lista vuota, pagamenti annullati non contano, scadute alla fine, edizione diversa esclusa.
- [ ] **4. Email differita**: migrazione 0010 (`confirmation_email_due_at`, `confirmation_email_sent_at` su `payment`), flag `defer_confirmation_email`, `send_due_confirmations`, timer `run_later`, chiamata dal job orario.
  Test: senza flag l'email parte subito; con flag non parte e la scadenza è a +30 s; dopo 30 s parte una sola volta (anche con due esecuzioni); pagamento annullato prima: non parte; prenotazione non più confermata: non parte; job orario recupera quelle perse; migrazione da zero e downgrade.
- [ ] **5. Pagina** `AdminCollect.tsx`, rotta, menu, titolo di pagina.
  Test: elenco, vuoto, errore di caricamento, link alla scheda.
- [ ] **6. Ricerca e canale**.
  Test: filtro per nome, email e causale senza maiuscole, «Nessun risultato», canale ricordato in `localStorage` e pagina funzionante se `localStorage` lancia.
- [ ] **7. Segna pagato e annullo**: `POST` del saldo con canale, data di oggi e `defer_confirmation_email`, riga «Pagato · Annulla» per 10 secondi, `void` con il motivo fisso, errore accanto alla riga.
  Test: importo e canale inviati, la riga scompare dopo 10 secondi (timer finti), annullo che la riporta, avviso di riattivazione mostrato, errore del server.
- [ ] **8. Accessibilità e telefono**: etichette con il nome, `aria-live`, aree di tocco da 44 px, nessuno scorrimento laterale a 390 px.
  Test: etichetta del tasto con il nome, regione `aria-live` presente. Provato in browser a 390 px.
- [ ] **9. Chiusura**: guida `12-da-incassare.md` (con il tempo di 10 secondi e l'email dopo 30) e rimando da `08-da-verificare.md`; lint e test verdi, migrazioni da zero; `progress.md`, `activeContext.md`, `decisions.md`, `domain.md` (solo le modifiche approvate), `README.md` se serve; `pr-description.md` con checklist per gli organizzatori.

## Da verificare a mano

- Da telefono: cerca per causale, segna pagato, annulla entro 10 secondi, riga che sparisce, email di conferma che arriva dopo circa 30 secondi (e non arriva se annulli).
- Una iscrizione in attesa segnata come pagata diventa `confermata` e in «Persone» risulta saldata; l'annullo la riporta in attesa.
- Una iscrizione scaduta segnata come pagata si riattiva se c'è posto, altrimenti mostra l'avviso.
- «Da verificare» non si riempie di casi normali.
