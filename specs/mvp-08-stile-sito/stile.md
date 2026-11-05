# MVP 8 · Stile rilevato dal sito

Fonte: https://sites.google.com/view/cissoneeventi/welcome, letta il 2026-11-05 con Playwright (stili calcolati del contenuto) e con i due loghi scaricati dal sito.

**Limite della rilevazione**: il CSS generale di Google Sites arriva da `www.gstatic.com` e `ssl.gstatic.com`, ancora bloccati dalla rete della sessione. Colori e font del contenuto sono affidabili perché il sito li applica direttamente agli elementi; gli screenshot invece sono usciti senza impaginazione e non sono utilizzabili. Forma dei bottoni e spaziature vanno confermate guardando il sito.

## Cosa usa il sito

| Elemento | Valore rilevato |
|----------|-----------------|
| Font | **Montserrat** 400 e 700 (anche corsivo), per titoli e testo |
| Testo | `#000000` nei paragrafi, `#1C1C1C` in link e titolo principale |
| Titoli di sezione | Montserrat 700, `#22383D` (petrolio scurissimo) |
| Colore del logo «CISSONE» | `#005C68` (petrolio) |
| Bottoni («Scopri di più sul Camp», «Cosa Fare») | sfondo `#F4B400` (ambra), testo `#1C1C1C`, Montserrat 400; raggio 0 rilevato sul link, da confermare a vista |
| Sfondo | bianco `#FFFFFF`, superfici `#F9F9F9` |
| Link di navigazione | colore di default del browser (blu), quindi non è una scelta di stile da copiare |
| Testo dei paragrafi | 18,67 px, interlinea 28 px |

Loghi presenti sul sito:

- **Logo orizzontale «CISSONE»** (arco + scritta), petrolio `#005C68` su trasparente, PNG 2048 × 376.
- **Logo «Cissone Summer Camp»** (arco, «CISSONE», «Summer Camp» in un corsivo decorativo), nero su trasparente, PNG 1063 × 822.

Il sito è della Pro Loco di Cissone («Fatto con ❤️ da Michela e dal team della Pro Loco di Cissone»). I loghi **non** sono nel repo: il progetto è open source con licenza MIT e serve il permesso della Pro Loco, oppure una versione SVG fornita da loro, prima di includerli.

## Palette proposta per l'app

Contrasti calcolati con la formula WCAG 2.

| Token | Colore | Uso | Contrasto |
|-------|--------|-----|-----------|
| `--color-bg` | `#FFFFFF` | sfondo pagina | |
| `--color-surface` | `#F9F9F9` | schede, fieldset, tabelle a righe alterne | testo 16,2:1 |
| `--color-text` | `#1C1C1C` | testo | 17,0:1 |
| `--color-heading` | `#22383D` | titoli | 12,4:1 |
| `--color-primary` | `#005C68` | link, focus, bottoni secondari (bordo e testo), barra admin | 7,7:1 (AAA) |
| `--color-on-primary` | `#FFFFFF` | testo su petrolio | 7,7:1 |
| `--color-cta` | `#F4B400` | bottone principale (Iscriviti, Salva, Registra pagamento) | |
| `--color-on-cta` | `#1C1C1C` | testo sul bottone principale | 9,2:1 |
| `--color-border-strong` | `#757575` | bordo dei campi | 4,6:1 (minimo 3:1) |
| `--color-error`, `--color-error-bg` | `#8A1C10`, `#FBE4E1` | errori (restano quelli di oggi) | 7,7:1 |
| `--color-success-bg` | `#E3F3EC` | conferme (resta quello di oggi) | testo 14,9:1 |
| `--font-body`, `--font-heading` | Montserrat 400 / 700 | tutto il testo | |

Vincoli che ne derivano:

- L'**ambra non va mai usata per testo, bordi o anello di focus su bianco**: contrasto 1,85:1, sotto il minimo. Solo come sfondo del bottone principale, con testo scuro.
- L'**anello di focus** è petrolio `#005C68`: su bianco 7,7:1, sul bottone ambra 4,2:1, entrambi sopra il 3:1 richiesto.
- Il testo dei paragrafi del sito è nero puro; nell'app si usa `#1C1C1C`, che il sito usa già nei bottoni e nel titolo, per un aspetto meno duro.
- Montserrat è un font libero (OFL): si include con `@fontsource/montserrat`, pesi 400 e 700, senza richieste a Google Fonts.

## Rispetto a oggi

| Oggi | Proposta |
|------|----------|
| Sfondo crema `#FFFDF8` | bianco `#FFFFFF` |
| Accento verde `#0B6B57` su bottoni e link | petrolio `#005C68` su link e focus, ambra `#F4B400` sul bottone principale |
| Font di sistema | Montserrat |
| Titolo in testo «Cissonauti Summer Camp» | logo + nome, appena c'è il permesso |

## Confermato dal maintainer (2026-11-05)

1. **Nome**: nell'app resta «Cissonauti Summer Camp» (D-012), anche accanto al logo.
2. **Palette**: approvata così com'è nella tabella sopra.
3. **Bottoni**: squadrati come sul sito (`--radius: 0` sui bottoni). I campi seguono la stessa forma per coerenza.

## Ancora aperto

1. **Loghi**: chi chiede il permesso alla Pro Loco e se esiste una versione SVG. Quale dei due loghi va nell'intestazione (proposta: quello orizzontale, più adatto al telefono). Finché manca il permesso, l'intestazione mostra solo il nome in testo (US-3 lo prevede già).
2. **Spaziature**: per rilevarle servono anche `www.gstatic.com` e `ssl.gstatic.com` tra i domini consentiti, oppure due screenshot del sito. Non blocca: in mancanza si tengono le spaziature attuali dell'app.
