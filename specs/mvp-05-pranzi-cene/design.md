# MVP 5 · Pranzi e cene · Design

## Modello dati (migrazione 0006)

Su `edition`:

| Campo | Scopo |
|-------|-------|
| `lunch_price_cents` (int) | prezzo del pranzo, default segnaposto da confermare |
| `dinner_price_cents` (int) | prezzo della cena, default segnaposto da confermare |

Nuova tabella `booking_meal`: `booking_id`, `date`, `kind` (`lunch` o `dinner`), chiave primaria composta. Costanti `MEAL_LUNCH`, `MEAL_DINNER` in `app/models.py`. Le righe si cancellano con la prenotazione.

Su `booking`:

| Campo | Scopo |
|-------|-------|
| `diet` (nullable) | `omnivore`, `vegetarian`, `vegan` |
| `allergies` (nullable, testo) | allergie e intolleranze |
| `health_consent_document_id` (nullable) | versione del testo di consenso accettata |
| `health_consent_at` (nullable) | data e ora del consenso |

Nuovo tipo di testo legale `DOC_HEALTH = "health"`. Resta fuori da `LEGAL_KINDS` (`app/services/edition.py`), che oggi decide se l'iscrizione è aperta: si aggiunge un elenco separato dei testi gestiti da Impostazioni, così il consenso sanitario non blocca le iscrizioni.

I dati sanitari stanno sulla prenotazione e non sulla persona: valgono per un'edizione e spariscono con la prenotazione rimossa (minimizzazione).

## Regole di dominio (funzioni pure)

In `app/domain/meals.py`:

- `can_have_lunch(periods) -> bool`: mattina o pomeriggio.
- `can_have_dinner(periods) -> bool`: `has_evening` da `app/domain/presence.py` (D-009).
- `allowed_meals(periods_by_day) -> set[(date, kind)]`.
- `meals_to_drop(meals, periods_by_day) -> set[(date, kind)]`: usata da ogni cambio di slot.
- `check_meal_change(current, wanted, allowed, past_days, allow_past) -> MealCheck`: con motivo del rifiuto (`not_allowed`, `past_day`).
- `check_health_data(allergies, consent) -> ok | consent_required`: allergie non vuote senza consenso rifiutate; consenso tolto svuota le allergie.
- `diet_counts(rows) -> dict`: conteggio per regime nella vista.

In `app/domain/fees.py`: `compute_amount_due(slot_dates, lunches, dinners, base, per_day, lunch_price, dinner_price) -> int`. `compute_fee` resta e viene richiamata: a zero pasti il risultato è identico (i test dell'MVP 1 non cambiano).

## Servizi

- `app/services/amounts.py`: `recompute_amount(edition, booking) -> int`, unico punto che scrive `amount_due_cents`. Sostituisce le chiamate dirette a `compute_fee` in `services/registration.py` e `services/booking_changes.py`, e la promozione dell'MVP 4. L'MVP 6 vi aggiungerà le attività.
- `app/services/meals.py`: `change_meals(db, sender, booking, wanted, now, allow_past=False, actor=None) -> ChangeResult`, con la stessa forma di `change_slots`: `expire_overdue`, controllo dello stato (`can_edit_slots`), ricalcolo, conferma automatica se coperta, email di conferma come oggi, `audit.log` per l'admin.
- `change_slots` (`booking_changes.py`) chiama `meals_to_drop`, toglie i pasti, li riporta in `ChangeResult.dropped_meals` e nella cronologia.
- `app/services/health.py`: `save_dietary(db, booking, diet, allergies, consent, now)`.

## Endpoint

| Metodo e path | Scopo |
|---------------|-------|
| `GET /api/me` | esteso: `meals`, `allowed_meals`, prezzi, `diet`, `allergies`, testo del consenso |
| `PUT /api/me/booking/meals` | `{meals: [{date, kind}], preview?}`; risposta come il cambio slot |
| `PUT /api/me/booking/dietary` | `{diet, allergies, consent}` |
| `PUT /api/admin/registrations/{id}/meals` | come sopra, giorni passati ammessi, cronologia |
| `GET /api/admin/registrations/{id}` | esteso con pasti, regime, allergie |
| `GET /api/admin/views/meals` | vista per giorno e pasto (`?format=csv`) |
| `GET /api/admin/views/week` | esteso con pranzi e cene |
| `PUT /api/admin/edition` | esteso con i due prezzi |
| `POST /api/admin/legal-documents` | accetta il tipo `health` |

Le allergie non entrano mai in `booking_view` pubblico, nelle email (`app/email/templates.py`) né nei log.

## Pagine

- `Personal.tsx`: sezione «Pranzi e cene» con una riga per giorno di presenza (componente `MealEditor`, sullo stile di `SlotEditor`, con anteprima dell'importo); sezione «Esigenze alimentari» con regime, allergie e casella del consenso che mostra il testo.
- `AdminRegistrationDetail.tsx`: pasti modificabili, regime e allergie in sola lettura.
- Nuova pagina `AdminMeals.tsx` alla voce «Pasti» di `AdminLayout`; `AdminWeek.tsx` con due colonne in più; `AdminSettings.tsx` con prezzi e testo del consenso.
- `CsvButton.tsx`: avviso facoltativo prima del download («contiene dati sanitari»).

## Impatti sugli MVP precedenti

- **MVP 1**: l'importo passa da `recompute_amount`; senza pasti il risultato non cambia.
- **MVP 2**: `change_slots` può togliere pasti; l'email di conferma della disdetta non cambia.
- **MVP 3**: «Settimana» e la scheda si estendono; «Da verificare» funziona da sola (saldo positivo o credito dopo i pasti).
- **MVP 4**: la promozione usa `recompute_amount`.

## Scelte tecniche da registrare in `decisions.md`

- Un solo punto (`recompute_amount`) che calcola l'importo dovuto.
- Dati sanitari sulla prenotazione, non sulla persona.
- Consenso sanitario versionato come i testi legali ma senza bloccare l'iscrizione.
- I pasti che perdono il titolo cadono da soli, con avviso, invece di bloccare il cambio degli slot.
