# MVP 10 · Incassi (controllo del conto) · Task

Branch: `claude/brave-babbage-ttfx6u` (vincolo di push della sessione). **Dimensione**: 8 task.

- [ ] **1. Spec**: questi tre file, voce in `ROADMAP.md`, `activeContext.md`.
- [ ] **2. Regola `to_collect`** in `domain/payments_review.py`.
  Test: in attesa a zero, in attesa parziale, confermata con saldo, confermata coperta (no), confermata in credito (no), scaduta (sì, in coda), disdetta e rimborsata (no), ordine per scadenza.
- [ ] **3. Servizio e endpoint** `GET /api/admin/views/to-collect`.
  Test: admin 200, partecipante 403, anonimo 401, senza edizione attiva lista vuota, pagamenti annullati non contano, scadute alla fine, edizione diversa esclusa.
- [ ] **4. Pagina** `AdminCollect.tsx`, rotta, menu, titolo di pagina.
  Test: elenco, vuoto, errore di caricamento, link alla scheda.
- [ ] **5. Ricerca e canale**.
  Test: filtro per nome, email e causale senza maiuscole, «Nessun risultato», canale ricordato in `localStorage` e pagina funzionante se `localStorage` lancia.
- [ ] **6. Segna pagato e annullo**: `POST` del saldo con canale e data di oggi, riga «Pagato · Annulla» per 8 secondi, `void` con il motivo fisso, errore accanto alla riga.
  Test: importo e canale inviati, la riga scompare dopo 8 secondi (timer finti), annullo che la riporta, avviso di riattivazione mostrato, errore del server.
- [ ] **7. Accessibilità e telefono**: etichette con il nome, `aria-live`, aree di tocco da 44 px, nessuno scorrimento laterale a 390 px.
  Test: etichetta del tasto con il nome, regione `aria-live` presente. Provato in browser a 390 px.
- [ ] **8. Chiusura**: guida `12-da-incassare.md` e rimando da `08-da-verificare.md`; lint e test verdi, migrazioni da zero (nessuna nuova); `progress.md`, `activeContext.md`, `decisions.md`, `domain.md` (solo le modifiche approvate), `README.md` se serve; `pr-description.md` con checklist per gli organizzatori.

## Da verificare a mano

- Da telefono: cerca per causale, segna pagato, annulla entro 8 secondi, riga che sparisce.
- Una iscrizione in attesa segnata come pagata diventa `confermata` e in «Persone» risulta saldata; l'annullo la riporta in attesa.
- Una iscrizione scaduta segnata come pagata si riattiva se c'è posto, altrimenti mostra l'avviso.
- «Da verificare» non si riempie di casi normali.
