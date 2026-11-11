# MVP 31 · Design

Nessuna migrazione, nessun dato nuovo. Il giorno «oggi» viene dal server (`get_now`, `deps.py`) e si ricava in `Europe/Rome` con `timefmt.ROME`; il fuso del dispositivo non entra mai nel calcolo.

## Dominio puro

Nuova funzione in `backend/app/domain/presence.py` (o modulo `domain/day_order.py` se si preferisce non appesantire il file):

```python
def useful_day_order(days: Sequence[date], today: date, start: date | None, end: date | None) -> list[date]
```

- Se `start` o `end` mancano, oppure `today < start` o `today > end`: ordine cronologico (`sorted(set(days))`).
- Altrimenti: `[today]` se presente, poi i giorni `> today` in ordine, poi i giorni `< today` in ordine.
- Funzione pura: nessun orologio, nessun database. Un helper `rome_today(now)` in `timefmt.py` restituisce `to_rome(now).date()` (con `now` timezone-aware UTC come il resto dell'app).

## API (`backend/app/api/admin_views.py`)

- `/week`, `/slots` e `/meals`, ramo **JSON**: le liste `days` si restituiscono già nell'ordine utile, e la risposta ha un nuovo campo `today: date | None` (la data di Roma, o `None` se fuori dall'edizione, cosicché l'interfaccia sa se marcare «Oggi»).
- Ramo **CSV** di ognuna: nessun cambio, resta cronologico (D-122). Un test confronta ordine e contenuto dei CSV prima e dopo.
- Calcoli, totali e conteggi non cambiano: si riordinano solo le righe già calcolate (`week_summary`, `groupby` degli slot, `MealDayOut`). I `total_*` restano uguali.
- `/week/detail` (MVP 26) e gli altri endpoint non cambiano.

Perché nel server e non nel browser: una sola regola, testabile con `get_now` finto; l'interfaccia non deve conoscere l'edizione né il fuso.

## Frontend

- Nuovo hook `frontend/src/useRefreshOnReturn.ts`: ascolta `visibilitychange`; quando la scheda torna `visible` e `blocked()` è falso, chiama `load()`. Si disiscrive allo smontaggio.
- `AdminWeek.tsx`, `AdminSlots.tsx`, `AdminMeals.tsx`: usano l'hook. `blocked` è vero con una finestra di dettaglio aperta (`WeekDetailDialog`), con un editor o una conferma aperti (editor degli slot in `AdminSlots`), o con un salvataggio in corso. Il `load` esistente già sostituisce `days` per intero.
- Le chiavi React restano `day.date`: i giorni si spostano senza rimontare le righe sbagliate; la finestra di dettaglio aperta sul giorno X resta sul giorno X.
- Marcatura: `day.date === today` mostra il badge testuale «Oggi / Today» accanto alla data (`StatusBadge` o un `<span>` con testo, stile dei token esistenti, contrasto AA già verificato da `theme.test.ts`).
- Testi `views.today` in `i18n/{it,en}.ts`; guida `03-week.md`, `02-days-and-slots.md`, `04-meals.md` IT/EN con una frase sull'ordine e sul comportamento al ritorno.

## Impatti sugli MVP precedenti

- MVP 26: celle e totali con la loro modale non cambiano; il pulsante di ogni cella conserva focus e ritorno del focus.
- MVP 25a: la presenza degli esterni non cambia l'ordine, che dipende solo dalle date.
- Nessun impatto su calcoli, importi, email o pagina personale.

## Test previsti

Vedi [tasks.md](tasks.md).
