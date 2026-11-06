# MVP 14 · Testi dell'evento e accesso diretto · Requisiti

Richiesta del maintainer (2026-11-06). Riallineata a `main` dopo gli MVP 11-13: i testi delle altre email usano l'editor per lingua dell'MVP 13.

## US-1 · Nome dell'evento ovunque
- Quando l'edizione attiva ha un nome, allora intestazione (anche compatta in iframe), titolo della scheda e home mostrano quel nome; senza edizione attiva, «Cissonauti Summer Camp».
- Quando parte un'email, allora l'oggetto standard contiene il nome dell'edizione, nella lingua del destinatario.
- Quando l'admin rinomina l'edizione dalle Impostazioni, allora intestazione e titolo cambiano senza ricaricare.

## US-2 · Testi delle altre email modificabili
- Quando l'admin salva oggetto e testo iniziale di una delle 8 email (lista d'attesa, già iscritto, link di accesso, pagamento ricevuto, promemoria a metà e finale, posto liberato, disdetta) per una lingua, allora la prossima email di quel tipo a una persona in quella lingua li usa; i segnaposto `{first_name}`, `{last_name}`, `{event}`, `{start_date}`, `{end_date}` sono sostituiti.
- La parte con i dati della prenotazione (slot, quota, causale, scadenza, istruzioni di pagamento, link, frasi finali) resta automatica.
- Quando un campo è vuoto, allora vale il testo standard; un segnaposto sconosciuto è rifiutato con un messaggio; oggetto max 200 e testo max 5000 caratteri.
- Quando due primi salvataggi dello stesso testo arrivano insieme, allora nessuno dà errore.
- Un partecipante non può leggere né scrivere i testi (403).

## US-3 · Testo del modulo modificabile
- Quando l'admin scrive il paragrafo sopra il modulo (per lingua), allora `/register` lo mostra nella lingua della pagina, con gli a capo; vuoto = testo standard. Il riquadro «posto bloccato per N giorni» resta automatico.

## US-4 · Atterraggio sulla propria pagina
- Quando entro (password o link), allora arrivo sempre a `/me`; in alto, se sono admin, c'è «Vai al pannello organizzatori»; nel pannello c'è «La mia pagina».

## US-5 · Magic link senza clic in più
- Quando apro il link entro 10 minuti, allora entro subito, senza pagina «Entra».
- Quando lo riapro entro 10 minuti, allora entro ancora.
- Quando sono passati 10 minuti, allora vedo «Link non valido o scaduto» e «Richiedi un nuovo link».

## Modifiche a domain.md (approvate dal maintainer, applicate)
- Altre email: oggetto e testo iniziale modificabili per lingua, dati sempre automatici; nome edizione negli oggetti.
- Dopo il login tutti arrivano alla pagina personale; magic link riusabile 10 minuti, senza clic.
