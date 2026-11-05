# MVP 6 · Attività e contributi · Requisiti

Riferimento: `memory-bank/domain.md`. In caso di conflitto vince `domain.md`. Dipende dall'MVP 5 (calcolo unico dell'importo, regola «cade se perdi il titolo») e dall'MVP 3 (scheda admin, viste, CSV).

Scelta del maintainer (2026-11-05): per aderire a un'attività serve essere presenti in quella fascia del giorno.

## US-1 · Gestione delle attività

Come admin voglio creare le attività del camp, così i partecipanti possono aderire.

- Quando apro «Attività», allora vedo l'elenco per giorno con titolo, fascia, prezzo, capienza e iscritti.
- Quando creo un'attività, allora indico titolo, descrizione, giorno dell'edizione, fascia (mattina, pomeriggio o sera), orario indicativo facoltativo (testo, es. «10:30-12»), prezzo (0 vuol dire gratuita) e capienza facoltativa (vuota vuol dire senza limite).
- Quando il giorno è fuori dalle date dell'edizione, allora ricevo un errore.
- Quando modifico titolo, descrizione e orario indicativo, allora si aggiornano sempre.
- Quando ci sono già iscritti, allora non posso cambiare prezzo, giorno o fascia, e la capienza non può scendere sotto il numero di iscritti; la pagina spiega perché.
- Quando l'attività non ha iscritti, allora posso eliminarla; con iscritti no.
- Ogni creazione, modifica ed eliminazione finisce nella cronologia.

## US-2 · Adesione dalla pagina personale

- Quando apro la pagina personale, allora vedo le attività dei giorni e delle fasce in cui sono presente, con prezzo e posti liberi.
- Quando la fascia è la sera, allora conta anche la sera derivata dall'intero giorno (D-009).
- Quando aderisco e c'è posto, allora l'attività si aggiunge, l'importo si ricalcola (solo se a pagamento) e valgono le regole di D-017: in attesa coperta diventa confermata, confermata resta tale con il saldo aggiornato.
- Quando l'attività è piena, allora non posso aderire e lo vedo scritto («piena»).
- Quando due persone aderiscono nello stesso istante all'ultimo posto, allora entra una sola.
- Quando non sono presente in quella fascia, allora l'attività non mi viene proposta e l'API rifiuta l'adesione.
- Quando mi ritiro, allora il posto si libera e l'importo si ricalcola.
- Quando il giorno dell'attività è passato, allora non posso aderire né ritirarmi; oggi sì.
- Quando la prenotazione non è `in_attesa_pagamento` né `confermata`, allora non posso cambiare le attività.

## US-3 · Attività e cambi della prenotazione

- Quando tolgo lo slot che mi dava titolo a un'attività, allora l'attività cade, l'importo si ricalcola e la conferma me lo dice (stessa regola dei pasti).
- Quando la prenotazione scade, viene disdetta o rimborsata, allora i suoi posti nelle attività si liberano.
- Quando una prenotazione scaduta viene riattivata (dall'admin o con un pagamento), allora le attività che nel frattempo si sono riempite cadono, l'importo si ricalcola e la scheda lo segnala con un avviso; la cronologia lo registra. (Cambiato in implementazione rispetto a «l'admin decide se forzare»: stessa regola dei pasti, D-031, e vale anche per la riattivazione da pagamento.)

## US-4 · Attività dalla scheda admin

- Quando apro la scheda di una persona, allora vedo le sue attività.
- Quando aggiungo o tolgo un'attività dalla scheda, allora valgono le stesse regole, ma posso scegliere anche giorni passati e, con «Forza oltre la capienza» e conferma, superare il limite; la scheda lo segnala.
- La regola della presenza vale anche per l'admin: per dare un'attività a chi non è presente in quella fascia si aggiunge prima lo slot.
- Ogni modifica finisce nella cronologia.

## US-5 · Vista per attività

- Quando apro una attività dal pannello, allora vedo iscritti con nome, email, telefono e stato, posti occupati e liberi.
- Le prenotazioni `scaduta`, `disdetta_richiesta` e `rimborsata` non contano.
- Quando premo «Scarica CSV», allora ottengo una riga per attività e persona; dall'elenco «Attività» scarico tutte le attività insieme.

## US-6 · Contributi offerti

Come partecipante voglio proporre un talk, un tema per l'unconference o una competenza da condividere.

- Quando apro la sezione «Cosa porti al camp», allora aggiungo un contributo scegliendo il tipo (talk, tema per l'unconference, competenza), un titolo e una descrizione facoltativa.
- Quando salvo un contributo senza titolo, allora ricevo un errore.
- Quando modifico o tolgo un mio contributo, allora la modifica vale subito.
- Posso avere più contributi, senza limite.
- Il campo «cosa puoi portare al camp?» dell'iscrizione resta com'è e si vede accanto ai contributi.
- Quando la prenotazione viene rimossa, allora spariscono anche i suoi contributi.

## US-7 · Vista dei contributi

- Quando apro «Contributi», allora vedo tutti i contributi con tipo, titolo, descrizione, nome della persona e data, filtrabili per tipo.
- Quando premo «Scarica CSV», allora scarico le righe filtrate.
- I contributi di prenotazioni `scaduta`, `disdetta_richiesta` o `rimborsata` compaiono a parte, segnati come tali, perché la proposta può restare utile.

## US-8 · Settimana aggregata

- Quando apro «Settimana», allora vedo anche la colonna «Attività» con il numero di adesioni per giorno; il CSV la include.

## Modifiche a domain.md

Proposte, da approvare prima di applicarle alla chiusura dell'MVP:

1. **Attività**: legate a un giorno e a una fascia (mattina, pomeriggio, sera); si aderisce solo se presenti in quella fascia, sera derivata compresa.
2. **Importo**: il totale dovuto comprende le attività a pagamento, al prezzo corrente (come D-017).
3. **Modifiche alle attività**: con iscritti non cambiano prezzo, giorno e fascia, la capienza non scende sotto gli iscritti e l'attività non si elimina.
4. **Cambio degli slot**: togliere uno slot fa cadere le attività a cui non si ha più titolo.
5. **Contributi**: legati all'iscrizione dell'edizione, più di uno per persona, di tre tipi (talk, tema per l'unconference, competenza).

## Fuori scope (Backlog)

- Lista d'attesa per le attività piene.
- Annullare un'attività con iscritti (pioggia, imprevisti) togliendola a tutti e ricalcolando gli importi.
- Cambiare il prezzo di un'attività con iscritti.
- Attività su più fasce o su tutto il giorno (escursioni).
- Meccanismo dell'unconference (votazioni, calendario dei talk).
