# MVP 28 · Design

Solo `frontend/src/styles.css` e, se serve, un minimo di `Registration.tsx`. Nessuna migrazione, nessuna API.

## Stato attuale (verificato)

- `form#registration.with-summary` contiene `div.registration-toolbar` (sticky, `top: var(--registration-sticky-offset, 0px)`, `z-index: 4`, fondo `--color-bg-glass`, bordo inferiore sottile, `backdrop-filter: blur(8px)`), poi `div.form-main` e `aside.summary`.
- L'offset è calcolato da un effect in `Registration.tsx` (misura `.site-header` quando è sticky o fixed).
- `.summary`: nessun fondo, né sticky né fixed; su desktop è la colonna da 20 rem con bordo, raggio e ombra.
- Nessuna striscia d'enfasi esiste oggi.

## Modifiche

**Barra (`.registration-toolbar`)**
- `background: var(--color-paper)` pieno; si toglie il `backdrop-filter`.
- `border-bottom: 3px solid var(--color-cta)` come striscia d'enfasi (vietate solo le laterali).
- `.fee`: dimensione e peso maggiori, `--color-heading`; pulsante con `min-height: 2.75rem`.
- L'offset sticky resta quello esistente. Per i campi con focus o errore: `scroll-margin-top` sui campi basato sull'altezza della barra più l'offset, in modo che `scrollIntoView` e il focus non finiscano sotto la barra. Se la barra cambia altezza (inglese, zoom), la variabile CSS si aggiorna con lo stesso effect che già misura l'intestazione.

**Recap (`.summary`)**
- `background: var(--color-paper)`.
- Striscia superiore: `border-top: 3px solid var(--color-cta)` (non laterale).
- Nessuna posizione sticky: si aggiunge un test che lo garantisce.

**Contrasto**
- Coppie nuove (`--color-heading` su `--color-paper`, `--color-text` su `--color-paper` se non già presenti) vanno aggiunte alla lista di `theme.test.ts`; il bordo `--color-cta` su `--color-paper` è decorativo e non entra nel controllo del testo.

## Impatti sugli MVP precedenti

Nessuna regola di dominio; la struttura DOM resta (il test `Registration.test.tsx` verifica già che importo e pulsante siano nella barra e il riepilogo fuori). Il riepilogo compatto dell'MVP 15 non cambia.

## Test previsti

Vedi [tasks.md](tasks.md). Prove visive: desktop, telefono, iframe, zoom al 200%, inglese.
