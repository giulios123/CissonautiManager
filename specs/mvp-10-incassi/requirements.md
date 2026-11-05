# MVP 10 · Incassi (controllo del conto) · Requisiti

**Obiettivo**: chi fa l'admin controlla il conto e segna le quote come incassate in fila, da una sola pagina, senza aprire ogni scheda.

## Storie

1. **Elenco da incassare**. Come admin voglio una pagina «Da incassare» con le iscrizioni che aspettano un pagamento.
   - Quando apro `/admin/da-incassare` allora vedo le iscrizioni in attesa di pagamento e le confermate con un saldo da versare, ordinate per scadenza (prima la più vicina).
   - Quando una iscrizione è scaduta ma ha ancora il posto da recuperare allora compare in fondo, con l'etichetta «scaduta», perché un bonifico può arrivare in ritardo.
   - Quando non c'è nulla da incassare allora leggo «Nessun pagamento da incassare».
   - Ogni riga mostra persona, causale (il codice personale), stato, dovuto, versato, saldo e scadenza.
2. **Trova il bonifico**. Come admin voglio cercare la riga che corrisponde a un movimento del conto.
   - Quando scrivo nel campo di ricerca allora l'elenco si restringe a nome, cognome, email o causale che contengono il testo (senza maiuscole e senza spazi ai bordi).
   - Quando nessuna riga corrisponde allora leggo «Nessun risultato».
3. **Canale per la sessione**. Come admin voglio scegliere il canale una volta sola.
   - Quando apro la pagina allora in cima c'è un selettore con i quattro canali; la scelta vale per tutti i pagamenti che segno da lì e il browser se la ricorda per la volta dopo.
   - Quando non ho mai scelto allora il canale preselezionato è il primo disponibile.
4. **Segna come pagato**. Come admin voglio un tasto per riga che registra il saldo intero.
   - Quando premo «Segna pagato» allora si registra un pagamento pari al saldo, sul canale scelto, con data di oggi (ora di Roma), a mio nome.
   - Quando il saldo è coperto allora l'iscrizione diventa `confermata` subito, ma l'email di conferma parte dopo 30 secondi, per lasciare il tempo di annullare (dalla scheda l'email resta immediata).
   - Quando l'iscrizione era scaduta e si riattiva (o non si riesce) allora vedo l'avviso che la scheda già mostra.
   - Quando il pagamento fallisce allora la riga resta com'era e leggo l'errore accanto alla riga.
5. **Annulla subito**. Come admin voglio rimediare a un clic sbagliato senza aprire la scheda.
   - Quando ho appena segnato una riga allora per 10 secondi vedo «Pagato 11,00 € · Annulla».
   - Quando premo «Annulla» allora il pagamento è annullato con il motivo «Annullato subito dalla vista Da incassare», la riga torna da incassare e, se la prenotazione era stata confermata, torna in attesa con un nuovo blocco (regola già in `domain.md`). L'email di conferma non parte mai.
   - Quando passano i 10 secondi allora la riga esce dall'elenco; l'annullo resta possibile dalla scheda, ma dopo 30 secondi l'email di conferma è già partita e non si ritira (lo dice la guida).
   - Quando l'app si ferma o si riavvia prima dei 30 secondi allora l'email parte comunque al passaggio successivo del job orario, se il pagamento non è stato annullato.
6. **Importo diverso dal saldo**. Come admin voglio gestire un bonifico di importo diverso.
   - Quando l'importo sul conto non è il saldo allora un link «Altro importo» porta alla scheda dell'iscrizione, dove il pagamento libero esiste già.
7. **Accessibile e da telefono**. Come admin voglio usarla dal telefono.
   - Gli esiti si annunciano con `aria-live`, il tasto ha il nome della persona nell'etichetta («Segna pagato per Giulio Sciarappa»), i controlli sono alti almeno 44 px e non c'è scorrimento orizzontale a 390 px.
8. **Solo per admin**. Un partecipante non vede la pagina e l'API risponde 403.

## Fuori scope (Backlog)

- Importare l'estratto conto (CSV della banca) e abbinare i movimenti da solo.
- Pagamenti con importo parziale dal tasto rapido (si usa la scheda).
- Sollecito ai non paganti da questa pagina.
- Ritardare l'email di conferma anche per i pagamenti registrati dalla scheda.
- Ritirare un'email già partita.
