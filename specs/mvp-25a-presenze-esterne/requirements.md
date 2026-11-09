# MVP 25a · Presenze esterne

**Stato:** implementata sul branch `feat/mvp-25a-presenze-esterne`; restano CI SQL Server e collaudo organizzatori. P2, C2. Decisioni di riferimento D-063, D-087, D-088 e D-113–D-116. Dipende dalla base dell'MVP 16 (destinatari di pasti e attività); non dipende da 25b e 25c. Gli incassi degli esterni sono il [25b](../mvp-25b-incassi-esterni/requirements.md): in questo MVP l'esterno è solo una presenza logistica, senza importi.

## US-25a.1 · Inserire un esterno

- Quando un admin aggiunge un esterno, allora indica nome, cognome e se è «pagante» o «non pagante»; telefono, riferimento libero (es. «accompagna Maria») e nota interna sono facoltativi.
- Quando l'esterno viene salvato, allora non nascono account, email, `Participant`, prenotazione, slot coworking o consensi. L'esterno appartiene all'edizione corrente.
- Quando nome e cognome coincidono (senza distinguere maiuscole e spazi) con un altro esterno dell'edizione o con un iscritto che ha una prenotazione attiva, allora il salvataggio è rifiutato con un avviso. L'admin può procedere solo confermando esplicitamente che si tratta di una persona diversa.
- Quando chi non è admin tenta di leggere o scrivere un esterno, allora l'operazione è negata. Nessuna lista pubblica o visibile ai partecipanti viene creata.
- Quando l'admin modifica o elimina un esterno, allora l'azione è tracciata nella cronologia.

## US-25a.2 · Adesione a pasti e attività senza coworking

- Quando l'admin assegna un pasto a un esterno, allora può scegliere qualsiasi pranzo o cena dei giorni dell'edizione, anche passati, senza che l'esterno abbia slot. Questa eccezione vale solo per gli esterni, non per gli iscritti.
- Quando l'admin assegna un'attività a un esterno, allora l'esterno occupa un posto della sua capienza. Se l'attività è piena, l'operazione è rifiutata a meno che l'admin confermi esplicitamente di superare il limite, come per gli iscritti.
- Quando un'attività ha esterni aderenti, allora non si può portare la capienza sotto il numero totale degli aderenti, né cambiare giorno e fascia o eliminarla, come già avviene con gli iscritti.
- Quando un'attività è piena anche per effetto degli esterni, allora i partecipanti la vedono come piena; non vedono chi occupa i posti.
- Quando l'admin toglie un pasto o un'attività a un esterno, allora le viste si aggiornano e l'azione è tracciata.

## US-25a.3 · Regime alimentare e allergie degli esterni

- Quando l'admin registra un esterno, allora può indicare il regime (onnivoro, vegetariano, vegano); senza indicazione vale «nessuna indicazione» come per gli iscritti.
- Quando l'admin vuole salvare allergie o intolleranze, allora deve spuntare «consenso raccolto dalla persona», e il sistema registra data e admin. Senza la spunta le allergie non si salvano.
- Quando l'admin toglie la spunta, allora le allergie vengono cancellate. Quando l'esterno è eliminato, allora spariscono con lui.
- Quando si leggono le allergie, allora le vedono solo gli admin; non compaiono in email, CSV non riservati o payload dei partecipanti. Nei report restano soltanto un conteggio, come per gli iscritti.

## US-25a.4 · Conteggi coerenti

- Quando consulto «Pasti», allora vedo una riga per ogni persona, iscritto o esterno (con etichetta «Esterno»), e il totale del giorno e del tipo conta ciascuna persona una sola volta.
- Quando consulto «Attività» e il dettaglio di un'attività, allora gli aderenti comprendono gli esterni, distinguibili dall'etichetta, e `posti liberi` tiene conto di entrambi.
- Quando consulto «Settimana», allora pranzi, cene e attività comprendono gli esterni. Il coworking resta quello degli iscritti.
- Quando consulto il report, allora pasti e attività mostrano una colonna «Esterni» accanto a confermate e in attesa; il totale è la somma delle tre. Quote, incassi e saldi non cambiano: in questo MVP gli esterni non generano importi.
- Quando scarico i CSV di pasti, attività e settimana, allora gli esterni sono righe distinte con una colonna «Tipo» (Iscritto/Esterno) e le intestazioni sono tradotte come per gli altri CSV.
- Quando il dettaglio e il conteggio di una vista si confrontano, allora coincidono.

## US-25a.5 · Lingue e guida

- Quando uso l'interfaccia in italiano o in inglese, allora pagina, messaggi di errore, CSV e guida admin sono disponibili in entrambe le lingue.

## Modifiche a domain.md

Proposta da approvare, non applicata:

- Nuovo paragrafo «Esterni»: l'esterno è una persona con identità minima per edizione, gestita solo da un admin, senza account, email, prenotazione o coworking. Aderisce a pasti e attività e occupa la capienza delle attività. Il passaggio da esterno a iscritto non è automatico.
- Dati sanitari dell'esterno: allergie salvate solo con consenso dichiarato dall'admin, visibili solo agli admin, cancellate con l'esterno o togliendo la spunta.
- Viste e report contano gli esterni come persone distinte, mai come prenotazioni.

## Fuori perimetro

Incassi, dovuto e saldo dell'esterno (25b); esenzioni degli iscritti (25c); importazione di elenchi; conversione di un esterno in iscritto; presenza serale o coworking per gli esterni; email o link per gli esterni; archivio e chiusura edizione (F).
