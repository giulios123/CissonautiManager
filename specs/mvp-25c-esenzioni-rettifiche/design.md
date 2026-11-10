# MVP 25c · Design

## Dati e migrazione `0026_exemptions_refunds`

Migrazione additiva dopo `0025_external_movements`. Se il 25c si rilascia prima di 25a/25b, la migrazione prende il numero successivo alla testa corrente e lo stesso `down_revision`; nulla altro dipende dall'ordine.

- `booking.category`: stringa, default `ordinary` (anche per le righe esistenti), valori `ordinary` | `internal_non_paying`.
- `booking.fee_exempt`: bool, default `false`.
- `booking_meal.exempt`, `booking_activity.exempt`: bool, default `false`.
- **`booking_refund`**: `id`, `booking_id` (FK, indicizzato), `amount_cents` (> 0), `channel`, `refunded_on`, `note`, `recorded_by_id`, `created_at`, `voided_at`, `voided_by_id`, `void_reason`, `request_key` con indice univoco parziale (come `0021`).

I default espliciti vanno gestiti con `op.batch_alter_table` e, per SQL Server, con vincoli di default eliminati nel `downgrade` (come `0023`). Nessun importo salvato cambia con la migrazione.

## Calcolo unico (D-029)

`services/amounts.calculate_meal_selection` resta l'unico punto:

- quota = `0` se `booking.fee_exempt`, altrimenti `compute_fee(...)`;
- ogni `BookingMeal` ed ogni `BookingActivity` con `exempt` contribuisce `0`;
- il pasto compreso (policy `first_organizer_meal`) è il primo pasto organizzativo **non esentato**;
- `registration_fee_cents` e `amount_due_cents` sono salvati come oggi, nello stesso ricalcolo. Per la policy `legacy_total` si usa il totale come soglia, già coerente.

Gli stessi flag sono letti da `recompute_amount`, `reprice`, `change_meals`, `change_activities`, `change_slots` e dalle promozioni: nessun percorso li ignora. Togliere una voce elimina la riga e quindi la sua esenzione (vedi requisito sul ripristino); aggiungerla di nuovo parte da `exempt=False`.

### Versato netto

`services/payments.paid_total(booking)` diventa pagamenti attivi meno `booking_refund` attivi. Tutte le chiamate (circa dieci: conferma, saldo, annullo, report, anteprime MVP 18/23) usano già questa funzione; nessuna deve sommare `Payment` per conto proprio. `domain/report.py` riceve il netto dai fatti di `load_report`. `can_refund` (disdetta) confronta `refund_cents` con il versato netto.

Il tetto di un rimborso attivo è `versato netto − amount_due_cents`: così il versato netto non scende sotto il totale dovuto e quindi nemmeno sotto la soglia di conferma, e il rimborso non può mai far perdere il posto. L'annullo di un pagamento resta l'unico percorso che può riportare in attesa (`status_after_void`, sul versato netto).

## Anteprima e applicazione (`services/exemptions.py`)

Sul modello di `included_meals.preview/apply`, ma per una singola prenotazione:

- `preview(db, booking, change)` — `change` = categoria, `fee_exempt`, voci esentate; richiede prenotazione attiva (in attesa o confermata). Non scrive. Restituisce quota, totale, versato netto, saldo/credito, stato prima/dopo e un `token` SHA-256.
- Il fingerprint include categoria, flag, voci e relativi flag, prezzi e destinatari delle voci, quota e totale salvati, pagamenti e rimborsi (con stato di annullo), stato e scadenza.
- `apply(db, booking, change, token)` — `lock_edition`, poi `lock_booking`; riesegue `preview`; se il token differisce lancia `PreviewChanged` (409); se coincide scrive flag e importi nella stessa transazione, conferma la prenotazione in attesa ora coperta (`queue_confirmation_notice`; invio dopo il commit con `send_transition_confirmation`) e scrive `audit.log`. Idempotente grazie a un `exemption_preview_token` sul booking (stessa tecnica di `included_meal_preview_token`; colonna nella stessa migrazione).
- Nessun pagamento è toccato. Una prenotazione confermata non torna mai in attesa per un'esenzione tolta.

La sola modifica di `category` non richiede anteprima (nessun importo cambia) ma è tracciata.

## Rimborsi su prenotazione attiva (`services/booking_refunds.py`)

- `record_refund(db, booking, amount, channel, refunded_on, note, request_key, admin)` e `void_refund(db, refund, reason, admin)`.
- Solo per prenotazioni in attesa o confermate; tetto come sopra, controllato dopo `lock_booking` e rilettura dei rimborsi per evitare doppi rimborsi concorrenti.
- Nessuna email, nessun cambio di stato. Cronologia in `audit.log`.
- Il flusso esistente `services/refunds.record_refund` (disdetta) non cambia, tranne il tetto sul versato netto.

## API (`api/admin_registrations.py`)

- `PATCH /{id}` accetta `category`.
- `POST /{id}/exemptions/preview` e `POST /{id}/exemptions/apply` (con `token`).
- `POST /{id}/refunds` e `POST /{id}/refunds/{rid}/void`; 422 `refund.too_high`, 409 se la prenotazione non è attiva.
- `GET /{id}` e l'elenco aggiungono `category`, `fee_exempt`, flag per voce, `refunds[]`, `net_paid_cents`.
- CSV Persone: colonne «Categoria» e «Quota esente»; filtro `category`.
- `api/me.py`: payload con `exempt` per voce e con i rimborsi; **mai** `category`.

## Frontend

- `AdminRegistrationDetail`: pannello «Categoria ed esenzioni» (categoria, spunta quota, spunta per ogni pasto e attività) con anteprima prima/dopo e pulsante «Applica»; registro pagamenti e rimborsi; modulo rimborso accanto a `AdminRefundForm`; segnalazione delle esenzioni perse.
- `AdminRegistrations`: colonna e filtro per categoria.
- Pagina personale: etichetta «Esente» sulle voci, rimborsi nell'elenco dei movimenti.
- `AdminReport`: righe di conteggio, valore esentato e rimborsi su iscrizioni attive.
- Chiavi i18n IT/EN.

## Guida

Admin: `01-people` (categoria, esenzioni, rimborso) e `07-report`. Partecipante: `03-paying` (voci esenti e rimborsi). Entrambe le lingue.

## Impatti sugli MVP precedenti

- MVP 18: la soglia di conferma può valere zero per quota esentata (stessa logica della quota zero); le impronte di anteprima includono esenzioni e rimborsi.
- MVP 23: il pasto compreso salta le voci esentate.
- MVP 16: nessun cambio al destinatario di pasti e attività; l'esenzione si applica alle sole voci incassate dall'organizzazione (per una voce al fornitore non c'è nulla da esentare).
- MVP 22 («Da incassare»): saldi sul versato netto.

## Verifiche

Test di dominio parametrizzati: quota esente, voce esente, pasto compreso che salta l'esente, versato netto, tetto del rimborso. Test API: anteprima non mutante, conflitto dopo una modifica, retry idempotente, in attesa che si conferma e invia la notifica una sola volta, confermata che resta tale, nessun `Payment` modificato, 403, rifiuto su scaduta/chiusa/lista. Rimborso: stato invariato, oltre il credito (422), doppio invio, annullo, annullo di un pagamento dopo un rimborso, tetto della disdetta sul netto. Regressione dell'intera suite (circa dieci chiamate di `paid_total`). Migrazione da zero e da revisione precedente su SQLite e SQL Server; test sulle impronte MVP 18/23. Frontend: vitest sul pannello, sulla pagina personale e sul report.

## Modifiche a domain.md

Vedere [requirements.md](requirements.md#modifiche-a-domainmd). Applicarla solo dopo approvazione.
