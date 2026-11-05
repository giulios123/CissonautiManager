# MVP 8 · Stile del sito Cissone Eventi · Design

Solo frontend. Nessuna migrazione, nessun endpoint nuovo, nessun cambio alla CSP in `backend/app/main.py`.

## Raccolta dello stile (prerequisito)

Da raccogliere nel task 1 e salvare in `specs/mvp-08-stile-sito/stile.md` (con gli screenshot accanto):

- screenshot desktop e telefono della home e di una pagina interna del sito, e della sezione che contiene l'iframe;
- colori in esadecimale: sfondo, testo, titoli, colore principale (bottoni, link), colore secondario, bordi;
- font di titoli e testo (nome, pesi usati);
- forma dei bottoni (raggio, maiuscole, peso) e dei campi;
- logo in SVG o PNG ad alta risoluzione, con la licenza d'uso (è del sito dell'evento).

Due strade: aggiungere `sites.google.com` tra gli Allowed domains dell'ambiente cloud e lasciare che l'agent ricavi stili calcolati e screenshot con Playwright, oppure fornire i materiali a mano. In entrambi i casi il maintainer conferma la palette prima del task 2.

## Token CSS

Oggi `frontend/src/styles.css` ha tre variabili (`--fg`, `--bg`, `--accent`) e una decina di colori scritti a mano (`#6b6760` bordi dei campi, `#c9c4ba` e `#ddd8cd` bordi e separatori, `#8a1c10` e `#9b2c1f` errori, `#e3f3ec` e `#fbe4e1` sfondi di conferma ed errore, `#fff`). Diventano tutti token su `:root`:

| Token | Uso |
|-------|-----|
| `--color-bg`, `--color-surface` | sfondo pagina, sfondo di schede e campi |
| `--color-text`, `--color-text-muted` | testo principale e secondario |
| `--color-primary`, `--color-on-primary` | bottoni, link, focus; testo sopra il colore principale |
| `--color-border`, `--color-border-strong` | separatori; bordi dei campi (contrasto 3:1) |
| `--color-success-bg`, `--color-error`, `--color-error-bg` | messaggi |
| `--font-body`, `--font-heading` | famiglie |
| `--radius`, `--space-*` | raggio e spaziature |

Nessun colore scritto a mano fuori da `:root`. I nomi delle classi esistenti non cambiano, così componenti e test restano uguali.

## Font

Self-hosted con i pacchetti `@fontsource/<famiglia>` (licenza OFL), importati in `frontend/src/main.tsx` e serviti dalla build. Motivi: nessuna richiesta a Google Fonts (privacy dei visitatori, che in Italia è un tema concreto), nessun cambio alla CSP, funzionamento uguale dentro e fuori dall'iframe. Solo i pesi usati, con `font-display: swap`. Se il sito usa un font non libero, si sceglie il più simile tra quelli liberi e lo si annota.

## Intestazione e modalità iframe

- Componente `SiteHeader` in `App.tsx` al posto dell'attuale `<h1>Cissonauti Summer Camp</h1>`: logo (`frontend/public/logo.svg` o `.png`, con `alt`) e nome.
- Modalità iframe: in `main.tsx` si controlla `window.self !== window.top` (dentro `try`, perché alcuni browser lanciano un errore cross-origin) e si aggiunge la classe `in-frame` a `<html>`. Con `in-frame`: intestazione ridotta (solo il nome, piccolo, senza logo), sfondo uguale a quello della sezione del sito, margini ridotti.
- Il pannello admin (`AdminLayout.tsx`, `header.admin-nav`) usa gli stessi token; la navigazione resta un elenco di link.

## Componenti da allineare

Bottoni (principale, secondario, pericolo), campi e `select`, `fieldset` degli slot, checkbox, messaggi di errore e conferma, `ConfirmDialog.tsx`, tabelle admin (intestazioni, righe alternate, contenitore scorrevole), `CsvButton.tsx`, link.

## Verifica

- Script Playwright (in `frontend/scripts/` o nei test e2e se presenti) che apre iscrizione, pagina personale e pannello admin a 390 px e 1280 px e li fotografa; una pagina HTML di prova che incorpora l'iscrizione in un iframe per la modalità `in-frame`. Gli screenshot servono al confronto con il sito, non sono test automatici.
- Test vitest sul contrasto: legge i token da `styles.css` e controlla le coppie testo/sfondo con la formula WCAG.
- Test esistenti invariati.

## Impatti sugli MVP precedenti

- **MVP 1-3**: cambia solo l'aspetto; struttura, testi e classi restano. L'header CSP `frame-ancestors` resta com'è.
- **MVP 4-7**: le pagine nuove usano i token; se arrivano prima dell'MVP 8, i loro colori scritti a mano si portano ai token nel task 2.

## Scelte tecniche da registrare in `decisions.md`

- Font self-hosted invece di Google Fonts.
- Token CSS unici su `:root`, nessun framework CSS.
- Modalità iframe rilevata lato client con una classe su `<html>`.
