# MVP 5 · Pranzi e cene · Requisiti

Riferimento: `memory-bank/domain.md`. In caso di conflitto vince `domain.md`. Dipende dagli MVP 2 (pagina personale, cambio slot) e 3 (scheda admin, viste, CSV). Non dipende dall'MVP 4, ma la promozione dalla lista usa il calcolo dell'importo introdotto qui.

Scelte del maintainer (2026-11-05): due prezzi separati (pranzo e cena); regime alimentare senza consenso più allergie e intolleranze con consenso specifico; i pasti si cambiano con la stessa regola degli slot (oggi sì, giorni passati solo l'admin).

## US-1 · Adesione ai pasti dalla pagina personale

Come partecipante voglio dire a quali pranzi e cene ci sono, così chi cucina sa quanti siamo.

- Quando apro la pagina personale, allora vedo per ogni giorno in cui sono presente le caselle «Pranzo» e «Cena» con il prezzo.
- Quando ho la mattina o il pomeriggio di un giorno, allora posso aderire al pranzo di quel giorno.
- Quando ho la sera di un giorno, esplicita o derivata dall'intero giorno (D-009), allora posso aderire alla cena di quel giorno.
- Quando non sono presente nella fascia giusta, allora la casella non c'è e l'API rifiuta l'adesione.
- Quando salvo, allora vedo l'anteprima e poi il nuovo importo: quota più pranzi per il prezzo del pranzo più cene per il prezzo della cena.
- Quando la prenotazione è `in_attesa_pagamento` e il nuovo importo è già coperto dai pagamenti, allora diventa `confermata` (come D-017).
- Quando la prenotazione è `confermata`, allora resta tale e il saldo mostra la differenza o il credito.
- Quando la prenotazione non è `in_attesa_pagamento` né `confermata`, allora non posso cambiare i pasti.
- Quando il giorno è passato (Europe/Rome), allora non posso aggiungere né togliere quel pasto; oggi sì.
- I pasti non si scelgono all'iscrizione: il modulo pubblico non cambia.

## US-2 · Pasti e cambio degli slot

- Quando tolgo uno slot e per quel giorno non ho più titolo a un pasto (niente mattina né pomeriggio per il pranzo, niente sera per la cena), allora il pasto cade, l'importo si ricalcola e la conferma me lo dice («Tolto anche il pranzo di martedì»).
- Quando tolgo la sera esplicita ma ho mattina e pomeriggio, allora la cena resta (sera derivata).
- Quando l'admin cambia gli slot dalla scheda, allora vale la stessa regola e la cronologia registra i pasti tolti.

## US-3 · Regime alimentare

- Quando apro la sezione «Esigenze alimentari», allora scelgo il regime: onnivoro, vegetariano, vegano (oppure lo lascio vuoto).
- Il regime non è un dato sanitario: si salva senza consenso specifico e lo vedono solo gli admin.

## US-4 · Allergie e intolleranze con consenso

- Quando scrivo allergie o intolleranze, allora devo spuntare il consenso specifico, che mostra il testo configurato dall'admin.
- Quando non spunto il consenso, allora le allergie non si salvano e ricevo un errore chiaro.
- Quando salvo con il consenso, allora sono salvate la versione del testo, la data e l'ora.
- Quando tolgo il consenso, allora le allergie si cancellano subito.
- Quando l'admin non ha ancora pubblicato il testo del consenso, allora il campo allergie non è disponibile e la pagina lo dice; il resto funziona.
- Le allergie le vedono solo la persona stessa e gli admin: non compaiono nel modulo pubblico, nelle email o in qualunque altra vista.
- Quando una prenotazione viene rimossa (disdetta senza pagamenti), allora si cancellano anche regime e allergie.

## US-5 · Pasti dalla scheda admin

- Quando apro la scheda di una persona, allora vedo i suoi pasti, il regime e le allergie.
- Quando cambio i pasti dalla scheda, allora valgono le stesse regole del partecipante ma posso cambiare anche giorni passati; la cronologia registra chi, quando e cosa.
- L'admin non scrive allergie a nome di altri: le inserisce solo la persona, con il suo consenso.

## US-6 · Vista per pasto

- Quando apro «Pasti», allora per ogni giorno vedo pranzo e cena con: numero di persone, nomi, conteggio per regime (es. 18 onnivori, 4 vegetariani, 1 vegano, 2 senza indicazione) e l'elenco delle allergie con il nome.
- Quando una prenotazione è `scaduta`, `disdetta_richiesta` o `rimborsata`, allora i suoi pasti non contano.
- Quando premo «Scarica CSV», allora ottengo una riga per giorno, pasto e persona, con regime e allergie; il pulsante avvisa che il file contiene dati sanitari.

## US-7 · Settimana aggregata

- Quando apro «Settimana», allora vedo anche le colonne «Pranzi» e «Cene» per ogni giorno, con il totale; il CSV le include.

## US-8 · Impostazioni

- Quando apro le Impostazioni, allora trovo il prezzo del pranzo e quello della cena e il testo del consenso per i dati sanitari, versionato come privacy e scarico.
- Quando cambio un prezzo, allora vale per i ricalcoli successivi (come D-017 per le quote): gli importi già salvati non cambiano da soli.

## Modifiche a domain.md

Proposte, da approvare prima di applicarle alla chiusura dell'MVP:

1. **Prezzi**: due prezzi flat configurabili, uno per il pranzo e uno per la cena (oggi «prezzo flat per pasto»).
2. **Pranzo**: serve almeno uno slot di giorno (mattina o pomeriggio) in quel giorno.
3. **Esigenze alimentari**: il regime (onnivoro, vegetariano, vegano) si salva senza consenso; allergie e intolleranze solo con consenso specifico, con testo configurabile e versione salvata; togliere il consenso cancella le allergie.
4. **Cambio degli slot**: togliere uno slot fa cadere i pasti a cui non si ha più titolo, con ricalcolo dell'importo.
5. **Pasti nei giorni passati**: solo l'admin li cambia, come gli slot.

## Fuori scope (Backlog)

- Importi definitivi di pranzo e cena.
- Capienza dei pasti o chiusura delle adesioni a un'ora fissa.
- Menu, scelta dei piatti, ospiti esterni ai pasti.
