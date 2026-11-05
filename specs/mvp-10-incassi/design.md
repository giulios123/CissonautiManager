# MVP 10 · Incassi (controllo del conto) · Design

Nessuna modifica al modello dati né migrazioni. Nessun nuovo endpoint di scrittura: si riusano la registrazione e l'annullo dei pagamenti, quindi conferma, riattivazione, email e cronologia restano quelle di sempre.

## Schema d'insieme

| Pezzo | Cosa | Nuovo? |
|---|---|---|
| Regola `to_collect` | funzione pura: stato, dovuto, versato → vero/falso e ordine | sì, `backend/app/domain/payments_review.py` |
| Servizio `collect_rows` | carica l'edizione attiva, scade le prenotazioni, filtra e ordina | sì, `backend/app/services/views.py` |
| Endpoint lettura | `GET /api/admin/views/to-collect` | sì, `backend/app/api/admin_views.py` |
| Scrittura | `POST /api/admin/registrations/{id}/payments` | no |
| Annullo | `POST /api/admin/registrations/{id}/payments/{pid}/void` | no |
| Pagina | `AdminCollect.tsx`, rotta `/admin/da-incassare`, voce di menu «Da incassare» | sì |
| Guida | `frontend/src/guide/admin/12-da-incassare.md` | sì |

## Regola

`to_collect(status, due_cents, paid_cents)`:

- `in_attesa_pagamento` (non scaduta): sì, anche con versato 0;
- `confermata` con `paid < due`: sì;
- `scaduta`: sì, in coda;
- ogni altro caso: no (disdette, rimborsate, confermate coperte o in credito, queste ultime restano in «Da verificare»).

Ordine: prima non scadute per `hold_expires_at` crescente, poi confermate con saldo (per cognome), poi scadute per cognome.

## Endpoint

`GET /api/admin/views/to-collect` (`require_admin`) restituisce righe `{ booking_id, first_name, last_name, email, personal_code, status, amount_due_cents, paid_cents, balance_cents, hold_expires_at }`. Nessun parametro: la ricerca è nel browser, perché le iscrizioni sono centinaia al massimo. Nessun CSV (le altre viste lo hanno, questa serve a lavorare, non a esportare).

## Pagina

- In cima: selettore canale (stessi quattro valori di `PaymentIn.channel`, etichette come nella scheda) e campo «Cerca per nome, email o causale». La scelta del canale sta in `localStorage` (convenienza per visitatore, con `try/catch`).
- Riga: persona con link alla scheda, causale, stato (`StatusBadge`), dovuto, versato, saldo, scadenza in ora di Roma, tasto «Segna pagato» e link «Altro importo».
- Dopo il clic: la riga passa a «Pagato {importo} · Annulla» per 8 secondi (timer in un `useEffect` con pulizia). Allo scadere si rilegge l'elenco. L'id del pagamento da annullare è l'ultimo della risposta `RegistrationDetail`.
- Stato di caricamento, errore e vuoto come le altre viste; esiti in una regione `aria-live="polite"`.
- Titolo di pagina in `pageTitle.ts`: «Da incassare».

## Impatti sugli MVP precedenti

- «Da verificare» resta com'è: segnala le anomalie, non l'attesa normale. Il testo della sua guida rimanda alla nuova pagina.
- `domain.md`, sezione Pannello admin: vedi sotto.

## Modifiche a domain.md (proposte, non applicate)

1. In «Pannello admin», tra le viste: «da incassare (iscrizioni in attesa o con un saldo da versare, con registrazione del pagamento a saldo in un clic e annullo immediato)».
2. In «Pagamenti»: «Dalla vista "da incassare" l'admin registra in un clic il saldo intero, sul canale scelto e con la data di oggi; l'importo diverso si registra dalla scheda.»

## Rischi

- Un clic sbagliato su una iscrizione in attesa la conferma e manda l'email. L'annullo la riporta in attesa, ma l'email resta inviata (Backlog: ritardarla).
- Con due admin sulla stessa pagina la riga può risultare già pagata: il server calcola sul saldo reale, ma il tasto registra comunque l'importo mostrato. Mitigazione: l'importo inviato è il saldo mostrato, e se nel frattempo il saldo è cambiato la risposta lo rende visibile; accettato per un'app con pochi admin.
