# MVP 1 · Parte 1a: iscrizione base in locale

## Cosa c'è
Iscrizione pubblica incorporabile, accesso con link via email o password, impostazioni dell'edizione, elenco iscrizioni, registrazione pagamenti con conferma automatica. Il deploy su Azure è la parte 1b.

## Da provare a mano (per gli organizzatori)

**Preparazione**
- [ ] Entra in `/accedi` con l'email e la password dell'organizzatore: arrivi al pannello.
- [ ] In Impostazioni inserisci nome, primo e ultimo giorno e salva: compare il numero di slot (2 per giorno).
- [ ] Attiva almeno un canale di pagamento e scrivi le istruzioni; pubblica informativa privacy e scarico di responsabilità.

**Iscrizione (provala da telefono)**
- [ ] Apri `/iscrizione`: vedi i giorni, mattina e pomeriggio con i posti liberi.
- [ ] Scegli mattina e pomeriggio dello stesso giorno: la quota conta quel giorno una volta sola.
- [ ] Scegli giorni non consecutivi: la quota cresce di 1 € per giorno.
- [ ] Prova a inviare senza le due caselle di consenso o senza «cosa puoi portare»: ti dice cosa manca.
- [ ] Iscriviti: vedi riepilogo, importo, causale (es. `CSC-7K3P`), istruzioni e scadenza.
- [ ] Controlla l'email (in locale compare nel log del programma): ha riepilogo, causale e link personale.
- [ ] Iscriviti di nuovo con la stessa email: non crea un doppione, ti arriva solo un nuovo link.

**Pagina personale**
- [ ] Dal link dell'email premi «Entra»: vedi slot, quota, saldo, scadenza e istruzioni.
- [ ] Riusa lo stesso link: ti dice che non è più valido e ti fa chiederne uno nuovo.
- [ ] Imposta una password ed esci; rientra con email e password.

**Pagamenti**
- [ ] Nel pannello trovi l'iscrizione; filtra per stato e cerca per nome o codice.
- [ ] Registra un pagamento parziale: resta «In attesa di pagamento» e il saldo scende.
- [ ] Registra il resto («Metti il saldo»): diventa «Confermata» e la persona riceve un'email.
- [ ] Con la scadenza superata (prova portando i giorni di blocco a 1 e aspettando) l'iscrizione risulta «Scaduta» e i posti tornano liberi.
- [ ] Se paghi una iscrizione scaduta e c'è ancora posto, si riattiva; se uno slot è pieno, il pagamento resta registrato e compare un avviso.

**Incorporamento**
- [ ] (Solo dopo il deploy) La pagina `/iscrizione` si vede dentro Google Sites; le altre pagine no.
