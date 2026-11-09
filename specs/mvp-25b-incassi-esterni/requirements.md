# MVP 25b · Incassi degli esterni

**Stato:** implementata sul branch `feat/mvp-25b-incassi-esterni` (sopra il 25a); restano CI SQL Server e collaudo organizzatori. P2, C2. Decisioni di riferimento D-087, D-088 e D-113–D-116. Dipende dal [25a](../mvp-25a-presenze-esterne/requirements.md) (anagrafica e adesioni degli esterni). Non dipende dal 25c.

## US-25b.1 · Dovuto di un esterno pagante

- Quando un esterno è «pagante», allora il suo dovuto è la somma dei prezzi correnti dei pasti e delle attività a cui aderisce, solo per le voci incassate dall'organizzazione.
- Quando una voce è pagata direttamente al fornitore, allora resta visibile con costo e istruzioni ma vale zero nel dovuto.
- Quando l'esterno non ha quota, allora non c'è nessuna quota base, nessun importo per giorno e nessun pasto compreso: il dovuto è solo la somma delle voci.
- Quando l'esterno è «non pagante», allora il dovuto è zero e nessun importo gli viene richiesto.
- Quando cambia un prezzo o un destinatario, o l'admin aggiunge o toglie una voce, allora il dovuto dell'esterno si aggiorna subito, perché è calcolato alla lettura dai prezzi correnti. I movimenti già registrati non cambiano.
- Quando cambia la categoria da pagante a non pagante dopo un versamento, allora il versato resta e il saldo diventa un credito, visibile e restituibile (US-25b.3).

## US-25b.2 · Registrare un incasso

- Quando l'admin registra un pagamento da un esterno, allora indica importo, canale (tra quelli dell'edizione), data e nota. Il pagamento è riferito all'esterno e all'edizione.
- Quando il pagamento è registrato, allora compare nell'elenco dei movimenti dell'esterno e il saldo si aggiorna. Nessun `Payment` di prenotazione e nessuna quota di iscritto viene creata o modificata.
- Quando lo stesso invio arriva due volte (doppio clic o nuovo tentativo), allora il pagamento è registrato una sola volta.
- Quando un pagamento è stato registrato per errore, allora l'admin lo annulla scrivendo un motivo. Il movimento resta in elenco, barrato, e non conta più. Non si cancella mai.
- Quando l'esterno versa più del dovuto, allora l'eccedenza è un credito. Non partono rimborsi automatici.
- Quando non è admin, allora nessuna di queste azioni è consentita.
- Agli esterni non parte nessuna email: non hanno un indirizzo.

## US-25b.3 · Restituire un credito

- Quando c'è un credito (versato attivo superiore al dovuto), allora l'admin può registrare una restituzione con importo, canale, data e nota.
- Quando l'importo supera il credito disponibile in quel momento, allora è rifiutato.
- Quando una restituzione è registrata per errore, allora si annulla con un motivo, come i pagamenti.
- Quando esistono movimenti, anche annullati, allora l'esterno non si può eliminare; si possono togliere le sue voci.

## US-25b.4 · «Da incassare»

- Quando consulto «Da incassare», allora una sezione separata «Esterni» elenca gli esterni paganti con saldo da versare, con nome, voci, dovuto, versato e saldo, e ricerca per nome.
- Quando incasso un esterno da quella lista, allora una finestra propone il saldo intero con canale e data, e posso cambiare l'importo. Non c'è attesa né annullo a 10 secondi, perché non parte nessuna email.
- Quando un esterno non ha saldo da versare o non è pagante, allora non compare nella lista.
- Quando la lista degli iscritti è filtrata o cercata, allora la sezione esterni non cambia i loro totali.

## US-25b.5 · Conti dell'evento

- Quando consulto il report, allora vedo una sezione «Incassi esterni» con dovuto, versato, restituito, da incassare e crediti, distinta dalle quote degli iscritti.
- Quando leggo il totale incassato dell'evento, allora è la somma del netto delle quote degli iscritti e del netto degli esterni; una stessa somma non compare in entrambi.
- Quando un costo è pagato al fornitore, allora non compare in nessuna delle due sezioni.
- Quando scarico i CSV (report e movimenti degli esterni), allora i movimenti sono righe distinte con tipo, esterno, importo, canale, data, stato di annullo e autore, e le intestazioni sono tradotte.

## US-25b.6 · Lingue e guida

- Quando uso l'italiano o l'inglese, allora pagine, errori, CSV e guida sono disponibili in entrambe le lingue.

## Modifiche a domain.md

Proposta da approvare, non applicata:

- Nuovo paragrafo «Incassi degli esterni»: registro separato dai pagamenti delle prenotazioni, con dovuto calcolato ai prezzi correnti sulle sole voci incassate dall'organizzazione, senza quota né pasto compreso.
- Movimenti annullati e mai cancellati; restituzione al massimo pari al credito; nessuna email.
- Totale incassato dell'evento = netto delle quote degli iscritti + netto degli esterni.

## Fuori perimetro

Esenzioni e rimborsi degli iscritti (25c); ricevute o email agli esterni; importazione di estratti conto; pagamenti al fornitore; chiusura dell'edizione e rettifiche tardive (F, Q-F4); unione di un esterno con un iscritto.
