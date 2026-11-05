# MVP 5 · Pranzi e cene

## Cosa c'è
Dopo l'iscrizione, dalla pagina personale, ognuno sceglie a quali pranzi e cene partecipa e la quota si aggiorna. Si indica anche il regime alimentare e, con un consenso apposito, allergie e intolleranze. Gli organizzatori hanno la vista «Pasti» con numeri, nomi, regimi e allergie per ogni pasto, e le colonne dei pasti in «Settimana».

## Da provare a mano (per gli organizzatori)

**Impostazioni**
- [ ] Trovi «Prezzo del pranzo» e «Prezzo della cena» (oggi 8 € e 12 €, da sostituire con gli importi veri).
- [ ] Nei testi legali c'è «Consenso per allergie e intolleranze»: scrivi il testo e pubblicalo. Finché non c'è, le persone possono indicare solo il regime.

**Pagina personale** (da telefono)
- [ ] Il modulo di iscrizione non chiede i pasti: si scelgono dopo.
- [ ] In «Pranzi e cene» premi «Scegli pranzi e cene»: il pranzo compare nei giorni in cui hai mattina o pomeriggio, la cena nei giorni in cui hai la sera (o mattina e pomeriggio insieme).
- [ ] Spuntando un pasto vedi la nuova quota e la differenza; dopo il salvataggio la quota e il saldo sono aggiornati.
- [ ] Se togli lo slot che ti dava diritto a un pasto (per esempio la sera), il pasto sparisce e il messaggio lo dice.
- [ ] I pasti dei giorni già passati non si possono cambiare (oggi sì).
- [ ] In «Esigenze alimentari» scegli il regime. Se scrivi un'allergia senza spuntare il consenso, ricevi un errore e non si salva nulla; con il consenso si salva.
- [ ] Togliendo la spunta del consenso e salvando, l'allergia viene cancellata.
- [ ] Le allergie non compaiono in nessuna email.

**Pannello**
- [ ] **Pasti**: per ogni giorno, pranzo e cena con il numero di persone, i regimi («4 vegetariani, 1 vegano...»), i nomi e le allergie.
- [ ] «Scarica CSV» chiede conferma perché il file contiene dati sanitari; aprilo in Excel e controlla accenti e righe.
- [ ] **Settimana**: ci sono le colonne Pranzi e Cene, con i totali in fondo, anche nel CSV.
- [ ] Nella scheda di un'iscrizione vedi pasti, regime e allergie; con «Cambia i pasti» li modifichi anche per giorni passati, e la modifica finisce nella cronologia.
- [ ] Chi ha già pagato e aggiunge un pasto resta confermato e compare in «Da verificare» con la differenza.

## Note tecniche
- Migrazione 0006: prezzi dei pasti su `edition`, tabella `booking_meal`, regime, allergie e consenso su `booking`.
- Decisioni D-029, D-030, D-031.
