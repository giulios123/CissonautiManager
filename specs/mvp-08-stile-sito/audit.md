# MVP 8 · Audit tecnico dell'interfaccia

Data: 2026-11-05. Perimetro: tutta l'interfaccia dopo l'unione con gli MVP 4-6 (iscrizione, accesso, pagina personale, pannello con tutte le voci, scheda, attività), a 390 px (iPhone 13) e 1280 px.

## Come è stato fatto

Il playbook è quello del comando `audit` di Impeccable (`reference/audit.md`, 5 dimensioni, punteggio 0-4, gravità P0-P3) e la soglia di qualità di `craft-floor.md`. **Il rilevatore automatico di Impeccable non è stato eseguito**: il suo launcher scarica ed esegue un binario esterno e la sessione lo ha negato. I controlli sono quindi stati fatti con uno script Playwright scritto per l'occasione (non nel repo) su un'app locale con dati degli MVP 4-6 (iscritti in ogni stato, lista d'attesa, pasti, attività, contributi):

- contrasto di ogni testo visibile (AA: 4,5:1, 3:1 per il testo grande);
- aree di tocco di pulsanti, campi, checkbox, voci di menu (minimo 44 px);
- titoli (un solo `h1`, nessun salto), landmark, nomi dei campi, dei pulsanti e dei link, testi alternativi, `caption` e `scope` delle tabelle, id duplicati, titolo della pagina, lingua;
- scorrimento orizzontale della pagina e a testo ingrandito al 200%;
- anello di focus su ogni elemento raggiungibile con Tab (80 passi per pagina sulle pagine più ricche);
- errori in console;
- lettura degli screenshot.

Non coperti: lettore di schermo reale, Safari e Firefox, prestazioni misurate con strumenti. Per chiudere il cerchio con il rilevatore: `npx impeccable detect frontend/src` e `npx impeccable detect http://localhost:5173` da una macchina dove si può eseguire.

## Punteggio

| # | Dimensione | Prima | Dopo | Nota |
|---|------------|-------|------|------|
| 1 | Accessibilità | 3 | 4 | titoli di pagina, tabelle con nome, aree di tocco, anello di focus sui campi data |
| 2 | Prestazioni | 3 | 3 | non misurate: JS 315 kB (95 kB gzip), font serviti dall'app, nessuna animazione |
| 3 | Temi | 4 | 4 | tutti i colori sono token e un test lo impone; modalità scura esclusa per decisione |
| 4 | Responsive | 2 | 3 | menu admin da 4 righe a una sola; le tabelle larghe scorrono di lato |
| 5 | Integrità dell'implementazione | 3 | 4 | bordi laterali colorati tolti, numerazione doppia corretta; senza il rilevatore |
| | **Totale** | **15/20** (buono) | **18/20** (eccellente) | |

**Verdetto di integrità**: coerente. Un solo sistema di token, componenti con la stessa forma ovunque, nessun gradiente, nessuna ombra decorativa. L'ombra del dialogo è l'unica ed è un token.

## Problemi trovati e corretti

| Gravità | Problema | Dove | Correzione |
|---------|----------|------|------------|
| P1 | Stesso titolo di pagina («Cissonauti Summer Camp») su tutte le rotte (WCAG 2.4.2, AA) | tutte | `pageTitle.ts`: «Pagina · Cissonauti Summer Camp», aggiornato a ogni cambio di rotta; test che ogni rotta ha un titolo diverso |
| P1 | Menu admin su telefono: 4 righe, circa 540 px su 844 | `AdminLayout` | riga unica scorrevole, la voce corrente viene portata in vista; ora 60 px |
| P2 | Lista d'attesa con numerazione doppia («1. 1. Luca Verdi») | `AdminSlots` | `ol.plain` senza simboli |
| P2 | Tre tabelle senza nome (Persone, Attività, Contributi) | `AdminRegistrations`, `AdminActivities`, `AdminContributions` | `caption` solo per lettori di schermo; test sul nome |
| P2 | Campi data senza anello di focus da tastiera | pannello Impostazioni | regola `:focus-within` per `date` e `time`; verificato con Tab su 4 pagine |
| P2 | Bordo laterale colorato di 4 px su messaggi e badge degli stati, un segno tipico delle interfacce fatte da template | `.notice`, `.status` | tolto, resta la tinta; il bordo superiore del dialogo diventa un bordo sottile con ombra a token; un test vieta i bordi laterali spessi |
| P2 | Etichette delle checkbox alte 30 px | moduli | altezza minima 44 px |
| P2 | «Esci» del menu largo 40 px | `AdminLayout` | larghezza minima 44 px |
| P3 | Spazio in eccesso sopra il titolo nelle schede | `.card` | primo e ultimo elemento senza margine esterno |
| P3 | Elenchi con pulsanti in linea che si spezzano male su telefono (contributi, lista d'attesa) | `Contributions`, `Waitlist`, `AdminSlots` | classe `.item`: testo e azioni vanno a capo come blocchi |
| P3 | Email in grassetto nelle intestazioni di riga; badge attaccato al nome | tabelle admin | `th small` normale; margine tra link e badge |
| P3 | Selezione del testo, cursore e sottolineatura dei link con i valori del browser | globali | `::selection`, `caret-color`, `text-underline-offset`, `text-wrap: balance` sui titoli |

## Verificato e a posto

- Contrasto: nessun testo sotto soglia in nessuna pagina (misurato, 32 pagine tra telefono e computer).
- Un solo `h1` per pagina, nessun salto di livello, un solo `main`, nomi presenti su tutti i campi e i pulsanti, nessun id doppio, `lang="it"`.
- Nessuno scorrimento orizzontale della pagina, anche con testo al 200%.
- Nessun errore in console.
- Altezza dei controlli: almeno 44 px su tutti i pulsanti, i campi e le voci di menu.
- Montserrat arriva dall'app, nessuna richiesta a domini esterni.

## Lasciato aperto (P3, non blocca)

- Su telefono le tabelle larghe scorrono di lato e l'ultima colonna può risultare tagliata senza un segnale visivo: chi usa il pannello da telefono lo scopre scorrendo.
- Gli stati di caricamento sono la scritta «Caricamento…»: niente scheletri.
- Nessuna evidenziazione della riga al passaggio del mouse nelle tabelle admin.
- Rilevatore automatico di Impeccable non eseguito (vedi sopra).
