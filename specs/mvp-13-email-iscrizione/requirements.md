# MVP 13 · Email di iscrizione personalizzabile · Requisiti

**Obiettivo**: l'admin modifica il testo della mail di conferma iscrizione (in italiano e in inglese) e aggiunge un'immagine con il nome del partecipante.

## Storie

1. **Testo modificabile**. Come admin voglio scrivere oggetto e testo della conferma di iscrizione per lingua.
   - Quando salvo allora i segnaposto `{first_name}`, `{last_name}`, `{event}`, `{start_date}`, `{end_date}` vengono sostituiti all'invio; un segnaposto sconosciuto è rifiutato con un messaggio.
   - Quando non ho scritto nulla allora vale il testo attuale.
   - Il blocco essenziale (slot, quota, causale, scadenza, come pagare, link personale) resta sempre in fondo e non è modificabile.
2. **Immagine di sfondo**. Quando carico una foto (JPEG, PNG o WebP fino a 5 MB) allora il server la riduce e la ricodifica in PNG; un file non valido è rifiutato.
3. **Immagine personalizzata**. Quando una persona si iscrive con una prenotazione allora la mail contiene un PNG con lo sfondo e il testo «I'm *nome* *cognome* and I'll be at *evento* from *data inizio* to *data fine*» (in italiano «Sono ... e sarò a ... dal ... al ...»), nella lingua della persona.
   - Il testo della card è modificabile per lingua, con colore e posizione (alto, centro, basso); un riquadro semitrasparente garantisce la leggibilità.
   - La sola iscrizione in lista d'attesa non riceve la card.
4. **Anteprima e prova**. Come admin voglio vedere l'anteprima con un nome d'esempio e ricevere una mail di prova.
5. **Mail HTML**: la mail ha parte testo e parte HTML (contenuto escapato) con la card in alto; l'immagine è inline.
6. **Bilingue**: sezione delle Impostazioni, messaggi e guida in italiano e in inglese.

## Fuori scope

Altre email modificabili; card scaricabile dalla pagina personale (Backlog).
