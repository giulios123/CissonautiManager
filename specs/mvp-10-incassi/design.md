# MVP 10 · Incassi (controllo del conto) · Design

Una migrazione (0010) con due colonne su `payment` per l'invio differito dell'email di conferma. Nessun nuovo endpoint di scrittura: si riusano la registrazione e l'annullo dei pagamenti, quindi conferma, riattivazione e cronologia restano quelle di sempre.

## Schema d'insieme

| Pezzo | Cosa | Nuovo? |
|---|---|---|
| Regola `to_collect` | funzione pura: stato, dovuto, versato → vero/falso e ordine | sì, `backend/app/domain/payments_review.py` |
| Servizio `collect_rows` | carica l'edizione attiva, scade le prenotazioni, filtra e ordina | sì, `backend/app/services/views.py` |
| Endpoint lettura | `GET /api/admin/views/to-collect` | sì, `backend/app/api/admin_views.py` |
| Scrittura | `POST /api/admin/registrations/{id}/payments`, con il flag nuovo `defer_confirmation_email` | quasi: un campo in più |
| Invio differito | `payment.confirmation_email_due_at` e `confirmation_email_sent_at`, migrazione 0010 | sì |
| Esecuzione | un timer in processo a 30 secondi, più il job orario come rete di sicurezza | sì |
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

## Email differita

`PaymentIn` accetta `defer_confirmation_email: bool = False` (solo la vista «Da incassare» lo manda a `true`). Con il flag, se il pagamento conferma la prenotazione, `record_payment` non spedisce: scrive `confirmation_email_due_at = now + 30 s` sul pagamento e restituisce la scadenza. Senza flag tutto resta come oggi (invio immediato).

`send_due_confirmations(db, sender, now)` prende i pagamenti con `due_at <= now`, `sent_at` nullo e `voided_at` nullo, e per ciascuno fa un `UPDATE ... WHERE sent_at IS NULL AND voided_at IS NULL` condizionale prima di spedire (stesso schema dei promemoria: due esecuzioni non spediscono due volte; un errore di consegna non si ritenta, è nei log). Spedisce solo se la prenotazione è ancora `confermata`. L'annullo di un pagamento non richiede altro: il filtro su `voided_at` basta.

Chi la esegue: (1) dopo la risposta, l'endpoint avvia un timer da 30 secondi (`app.state.run_later`, sostituibile nei test) che apre una sessione sua e chiama `send_due_confirmations`; (2) `send_reminders` la chiama a ogni passaggio orario, per le email perse se l'app si è fermata. L'app scala a zero, quindi il timer da solo non basta: per questo la scadenza è salvata nel database.

## Endpoint

`GET /api/admin/views/to-collect` (`require_admin`) restituisce righe `{ booking_id, first_name, last_name, email, personal_code, status, amount_due_cents, paid_cents, balance_cents, hold_expires_at }`. Nessun parametro: la ricerca è nel browser, perché le iscrizioni sono centinaia al massimo. Nessun CSV (le altre viste lo hanno, questa serve a lavorare, non a esportare).

## Pagina

- In cima: selettore canale (stessi quattro valori di `PaymentIn.channel`, etichette come nella scheda) e campo «Cerca per nome, email o causale». La scelta del canale sta in `localStorage` (convenienza per visitatore, con `try/catch`).
- Riga: persona con link alla scheda, causale, stato (`StatusBadge`), dovuto, versato, saldo, scadenza in ora di Roma, tasto «Segna pagato» e link «Altro importo».
- Dopo il clic: la riga passa a «Pagato {importo} · Annulla» per 10 secondi (timer in un `useEffect` con pulizia). Allo scadere si rilegge l'elenco. L'id del pagamento da annullare è l'ultimo della risposta `RegistrationDetail`.
- Stato di caricamento, errore e vuoto come le altre viste; esiti in una regione `aria-live="polite"`.
- Titolo di pagina in `pageTitle.ts`: «Da incassare».

## Impatti sugli MVP precedenti

- «Da verificare» resta com'è: segnala le anomalie, non l'attesa normale. Il testo della sua guida rimanda alla nuova pagina.
- `domain.md`, sezione Pannello admin: vedi sotto.

## Modifiche a domain.md (proposte, non applicate)

1. In «Pannello admin», tra le viste: «da incassare (iscrizioni in attesa o con un saldo da versare, con registrazione del pagamento a saldo in un clic e annullo immediato)».
2. In «Pagamenti»: «Dalla vista "da incassare" l'admin registra in un clic il saldo intero, sul canale scelto e con la data di oggi; l'importo diverso si registra dalla scheda.»

## Rischi

- Un clic sbagliato su una iscrizione in attesa la conferma subito. L'annullo entro 10 secondi la riporta in attesa e l'email non parte; passati i 30 secondi l'email è partita e non si ritira.
- Il timer in processo può non scattare (riavvio, scala a zero): la rete di sicurezza del job orario spedisce l'email al più entro un'ora, mai due volte.
- Con due admin sulla stessa pagina la riga può risultare già pagata: il server calcola sul saldo reale, ma il tasto registra comunque l'importo mostrato. Mitigazione: l'importo inviato è il saldo mostrato, e se nel frattempo il saldo è cambiato la risposta lo rende visibile; accettato per un'app con pochi admin.
