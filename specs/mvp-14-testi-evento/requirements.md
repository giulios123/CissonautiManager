# MVP 11 · Testi dell'evento e accesso · Requisiti

Richiesta del maintainer (2026-11-06). Piano approvato; magic link riusabile 10 minuti, senza pagina «Entra».

## US-1 · Nome dell'evento ovunque
Come partecipante, voglio vedere il nome dell'edizione in intestazione e nell'oggetto delle email.
- Quando l'edizione attiva ha un nome, allora intestazione (anche compatta in iframe), titolo della scheda e home mostrano quel nome.
- Quando non c'è un'edizione attiva, allora si usa «Cissonauti Summer Camp».
- Quando parte un'email, allora l'oggetto contiene il nome dell'edizione.

## US-2 · Testi delle email modificabili
Come admin, voglio modificare oggetto, apertura e chiusura di ogni email dal pannello.
- Quando salvo un testo, allora la prossima email di quel tipo lo usa; il blocco con i dati (slot, quota, causale, scadenza, istruzioni di pagamento, link) resta automatico e invariato.
- Quando lascio un campo vuoto o premo «Ripristina», allora si usa il testo predefinito.
- Quando scrivo `{nome}` o `{evento}`, allora vengono sostituiti con il nome della persona e dell'edizione.
- Quando un partecipante apre la pagina dei testi, allora riceve 403.

## US-3 · Testo del modulo modificabile
Come admin, voglio modificare il paragrafo sopra il modulo di iscrizione.
- Quando lo salvo, allora `/iscrizione` lo mostra (a capo rispettati); vuoto = testo di oggi.
- Il riquadro «posto bloccato per N giorni» resta automatico.

## US-4 · Atterraggio sulla propria pagina
Come admin iscritto, voglio vedere la mia pagina dopo il login.
- Quando entro (password o link), allora arrivo sempre a `/io`; in alto c'è il link al pannello.
- Dal pannello, «La mia pagina» porta a `/io`.

## US-5 · Magic link senza clic in più
- Quando apro il link entro 10 minuti dall'invio, allora entro subito, senza pagina «Entra».
- Quando riapro lo stesso link entro 10 minuti, allora entro ancora (gli scanner di posta non lo bruciano).
- Quando sono passati 10 minuti, allora vedo «Link non valido o scaduto» e «Richiedi un nuovo link».

## Modifiche a domain.md (da applicare in chiusura, già approvate dal maintainer a parole)
- Email: oggetto, apertura e chiusura modificabili dall'admin; dati della prenotazione sempre automatici.
- Dopo il login tutti arrivano alla pagina personale; gli admin hanno il link al pannello.
- Magic link: da «monouso, 30 minuti» a «riusabile per 10 minuti, si entra all'apertura».
