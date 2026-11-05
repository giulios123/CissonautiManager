# Decisioni

> Solo append. Una voce per decisione: data, decisione, motivo, alternative scartate.

## D-001 · App unica invece di frontend e backend separati

- **Data**: 2026-11-04
- **Decisione**: un solo container in cui FastAPI espone le API sotto `/api` e serve la build statica del frontend React.
- **Motivo**: un solo deploy da mantenere; niente CORS; cookie di sessione same-origin, quindi `SameSite=Lax` funziona senza eccezioni; meno risorse Azure da pagare e configurare.
- **Alternative scartate**: frontend su Azure Static Web Apps e API separata su Container Apps (due deploy, CORS, cookie cross-site); framework full stack con rendering lato server (meno familiare ai volontari, più lontano dallo stack scelto).

## D-002 · Test di integrazione su SQLite di default, SQL Server in CI

- **Data**: 2026-11-04
- **Decisione**: i test usano SQLite in un file temporaneo; con `TEST_DATABASE_URL` girano su SQL Server (usato dalla CI con un service container). Le query evitano hint specifici di un dialetto: i lock sugli slot usano `with_for_update()` di SQLAlchemy.
- **Motivo**: negli ambienti senza Docker (come la sessione cloud di sviluppo) SQL Server non parte; così la suite resta eseguibile ovunque e la CI copre il database vero.
- **Alternative scartate**: test solo su SQL Server (non eseguibili in locale senza Docker); mock del database (nasconderebbero errori di schema e di migrazione).

## D-003 · Datetime sempre timezone-aware, salvati come UTC

- **Data**: 2026-11-04
- **Decisione**: tipo `UtcDateTime` (TypeDecorator) che rifiuta datetime naive, salva UTC e restituisce valori con `tzinfo=UTC`. La conversione in Europe/Rome avviene solo in presentazione.
- **Motivo**: SQL Server `DATETIME2` e SQLite non conservano il fuso; così le scadenze non dipendono dal fuso del server.
- **Alternative scartate**: `DATETIMEOFFSET` (non portabile su SQLite); datetime naive per convenzione (errori silenziosi).

## D-004 · Password con argon2, magic link sempre disponibile

- **Data**: 2026-11-04
- **Decisione**: la password è opzionale, hashata con argon2 (`argon2-cffi`, parametri di default), minimo 10 caratteri. Si imposta da loggati (magic link o password). Il login restituisce un solo errore generico per email sconosciuta, password mancante e password errata, e verifica sempre un hash anche se l'utente non esiste.
- **Motivo**: richiesta del maintainer; il magic link resta il recupero della password, quindi non servono reset separati.
- **Alternative scartate**: bcrypt (argon2 è il default consigliato oggi); flusso "password dimenticata" dedicato (duplica il magic link).

## D-005 · Email già iscritta: risposta esplicita

- **Data**: 2026-11-04
- **Decisione**: se l'email ha già una prenotazione attiva, `POST /api/public/registrations` risponde `already_registered` e invia il magic link, senza creare nulla.
- **Motivo**: l'utente deve capire perché non vede il riepilogo. Rivela che l'email è iscritta, ma l'evento è tra conoscenti e l'iscrizione non espone altri dati.
- **Alternative scartate**: risposta identica per tutti (utente confuso, richiederebbe di nascondere importo e scadenza anche ai nuovi iscritti).

## D-006 · Tre slot al giorno e iscrizione in due tempi

- **Data**: 2026-11-04
- **Decisione**: ogni giorno ha mattina, pomeriggio e sera (default 19-24, senza limite di posti). Si accede in due tempi: prima l'iscrizione pubblica (slot e quota), poi, dalla pagina personale, l'adesione a pranzi e cene, modificabile.
- **Motivo**: richiesta del maintainer. La sera serve per sapere chi c'è e abilita la cena; separare l'iscrizione dai pasti la tiene corta.
- **Alternative scartate**: sera come sola scelta di pasto senza slot (non darebbe la presenza serale); pasti scelti già all'iscrizione (modulo più lungo, difficile da cambiare).

## D-007 · Azure SQL tier Basic

- **Data**: 2026-11-04
- **Decisione**: database Azure SQL tier Basic al posto del serverless con free offer.
- **Motivo**: costo fisso basso (circa 5 € al mese, da verificare) coperto dai crediti Azure; niente limite di ore di calcolo, niente risveglio dalla pausa. Il carico è minimo (al massimo 20 utenti contemporanei).
- **Alternative scartate**: serverless free offer (100.000 vCore-secondi al mese, rischio di superarli in settimana di evento e di fermare l'app); Neon o Firestore (fuori dallo stack Azure, Firestore non è relazionale).

## D-008 · Esiti della call del team

- **Data**: 2026-11-04
- **Decisione**: (1) due promemoria di pagamento, a metà blocco e 24 ore prima della scadenza; (2) accesso solo con magic link o password, il codice `CSC-XXXX` resta la sola causale; (3) pranzi e cene restano nell'app (MVP 5), dopo l'iscrizione; (4) il +1 resta il campo testuale «chi ti ha invitato?», l'MVP 7 si riduce alla priorità in lista d'attesa e al report; (5) stack confermato su Azure.
- **Motivo**: indicazioni del maintainer dopo il confronto con la call. Il codice come credenziale sarebbe debole perché compare nelle causali dei bonifici.
- **Alternative scartate**: promemoria periodici illimitati; accesso con identificativo numerico; pranzi gestiti fuori dall'app; link con referral per i +1; Cloud Run con Firestore o Neon.

## D-009 · Sera di chi prenota l'intero giorno: regola derivata

- **Data**: 2026-11-04
- **Decisione**: la sera non viene aggiunta in automatico alle prenotazioni di chi prenota mattina e pomeriggio. La presenza serale si ricava dalle regole: ha la sera chi ha lo slot serale oppure chi ha entrambi gli slot di giorno. La regola si applica dove serve (cena nell'MVP 5, viste di presenza nell'MVP 3).
- **Motivo**: tenere i dati reali di ciò che la persona ha scelto, senza prenotazioni scritte al posto suo, e non cambiare la quota.
- **Alternative scartate**: aggiungere in automatico lo slot serale (dati gonfiati, difficili da distinguere dalle scelte esplicite).

## D-010 · Scelte di deploy dell'MVP 1

- **Data**: 2026-11-04
- **Decisione**: una sola replica al massimo e zero a riposo; migrazioni Alembic all'avvio del container; autenticazione SQL con password in un segreto della Container App; immagine su GitHub Container Registry; login di GitHub Actions su Azure con OIDC, senza chiavi salvate.
- **Motivo**: con una replica le migrazioni non possono correre in parallelo e 20 utenti contemporanei bastano; la password SQL è la strada più semplice per volontari; GHCR e OIDC evitano costi e segreti da ruotare.
- **Alternative scartate**: più repliche (race sulle migrazioni); Azure Container Registry (costo); identità gestita verso SQL (più configurazione, evoluzione possibile).

## D-011 · Correzioni emerse dalla prima CI su SQL Server

- **Data**: 2026-11-05
- **Decisione**: (1) il lock sugli slot usa anche l'hint esplicito `WITH (UPDLOCK, HOLDLOCK)` per SQL Server, perché `with_for_update()` di SQLAlchemy su SQL Server non genera nessun blocco (corregge quanto scritto in D-002); (2) i confronti booleani usano `== true()`, perché `IS 1` non è SQL valido; (3) le colonne di testo sono Unicode (NVARCHAR), così nomi non latini o con emoji non diventano `?`; (4) nei test il database condiviso viene azzerato comprese le tabelle di Alembic e gli inserimenti non usano id espliciti.
- **Motivo**: SQLite nascondeva tutti e quattro i problemi. Il punto 1 avrebbe permesso due iscrizioni contemporanee sull'ultimo posto. Il modello e la migrazione 0001 sono stati modificati direttamente perché non erano ancora stati distribuiti.
- **Alternative scartate**: migrazione 0003 per cambiare il tipo delle colonne (inutile prima del primo deploy, richiederebbe di ricreare i vincoli unici).

## D-012 · Il nome è «Cissonauti» (due s)

- **Data**: 2026-11-05
- **Decisione**: nei testi visibili (interfaccia, email, documentazione, licenza) il nome è «Cissonauti Summer Camp», con due s. Il codice personale resta `CSC-XXXX` (Cissonauti Summer Camp).
- **Motivo**: indicazione del maintainer. Il nome con una sola s era un errore di battitura nel prompt iniziale, propagato ovunque.
- **Da decidere**: i nomi tecnici già creati su Azure (gruppo `cisonauti-rg`, app `cisonauti-booking`, identità `cisonauti-deploy`, login SQL) hanno ancora una sola s. Rinominarli richiede di ricreare le risorse e cambia l'indirizzo dell'app.

## D-013 · Risorse Azure ricreate con il nome corretto

- **Data**: 2026-11-05
- **Decisione**: i nomi tecnici passano a due s: gruppo `cissonauti-rg`, app `cissonauti-booking`, identità `cissonauti-deploy`, login SQL `cissonautiadmin`, database `cissonauti`. Il gruppo vecchio (`cisonauti-rg`) e la vecchia identità vengono eliminati. Cambiano anche il nome dei pacchetti e i file di lock.
- **Motivo**: scelta del maintainer, quando l'app ancora non aveva dati. Risolve la D-012 sui nomi tecnici.
- **Alternative scartate**: tenere i vecchi nomi (indirizzo dell'app con il nome sbagliato).

## D-014 · Promemoria da un Container Apps Job orario

- **Data**: 2026-11-05
- **Decisione**: i promemoria di pagamento partono da un Container Apps Job che gira ogni ora (`0 * * * *`, UTC) con la stessa immagine dell'app e il comando `python -m app.jobs.send_reminders`.
- **Motivo**: l'app scala a zero e a riposo non può inviare nulla; il job è in Bicep, senza endpoint pubblici in più, senza segreti nuovi su GitHub e con costo trascurabile.
- **Alternative scartate**: cron di GitHub Actions che chiama un endpoint protetto (ritardi del cron, disattivazione dopo 60 giorni di inattività del repo, endpoint in più da proteggere).

## D-015 · Email con Azure Communication Services e dominio gestito

- **Data**: 2026-11-05
- **Decisione**: `EMAIL_PROVIDER=acs` usa un dominio gestito Azure (mittente `DoNotReply@<id>.azurecomm.net`). L'invio usa `begin_send` senza attendere l'esito: un rifiuto viene scritto nei log e non annulla l'operazione già salvata.
- **Motivo**: gratuito e pronto subito; con poche decine di iscritti i limiti d'invio bastano. Rendere la richiesta indipendente dall'email evita che un problema di posta blocchi iscrizioni o pagamenti.
- **Alternative scartate**: dominio proprio (serve un dominio e l'accesso al DNS; resta l'evoluzione se il recapito dà problemi); attendere l'esito di consegna nella richiesta (rallenta e non cambia cosa si può fare in caso di errore).

## D-016 · Ogni promemoria si segna prima di inviarlo

- **Data**: 2026-11-05
- **Decisione**: il job fa un UPDATE condizionato (`reminder_*_sent_at IS NULL`) e invia l'email solo se ha vinto lui. Un invio fallito non viene ritentato.
- **Motivo**: garantisce «una sola volta» anche con riesecuzioni o due esecuzioni sovrapposte; perdere un promemoria è meno grave che mandarne due.
- **Alternative scartate**: segnare dopo l'invio (rischio di doppio invio se il segno fallisce); coda con ritentativi (complessità non giustificata).

## D-017 · Modifica degli slot da parte del partecipante

- **Data**: 2026-11-05
- **Decisione**: la scadenza del blocco non cambia; una prenotazione confermata resta confermata anche se l'importo sale (il saldo mostra la differenza); una in attesa il cui nuovo importo è già coperto diventa confermata; l'importo si ricalcola con le quote correnti dell'edizione; gli slot di giorni passati li cambia solo l'admin.
- **Motivo**: indicazioni del maintainer. Tornare in attesa avrebbe fatto scadere, e liberare i posti, a chi ha già pagato quasi tutto. La conferma automatica evita che una prenotazione già pagata scada.
- **Alternative scartate**: tornare `in_attesa_pagamento` con un nuovo blocco; rifiutare le modifiche sulle confermate; mantenere le quote del momento dell'iscrizione (richiederebbe di salvarle per ogni prenotazione).

## D-018 · Disdetta senza pagamenti: la prenotazione si rimuove

- **Data**: 2026-11-05
- **Decisione**: senza alcun pagamento registrato la disdetta elimina la prenotazione (e i suoi slot); con pagamenti passa a `disdetta_richiesta`. La persona resta registrata e può iscriversi di nuovo. In entrambi i casi parte l'email di conferma.
- **Motivo**: indicazione del maintainer («si rimuove e basta»): non c'è nulla da rimborsare, quindi nessun passaggio dall'admin.
- **Conseguenza accettata**: si perde la traccia dei testi legali accettati per quella prenotazione, perché non è mai stato versato nulla.
- **Alternative scartate**: uno stato finale dedicato (stato in più da gestire nelle viste e nei CSV); passare comunque da `disdetta_richiesta` (lavoro inutile per l'admin).

## D-019 · Dopo il deploy il workflow sveglia l'app per far partire le migrazioni

- **Data**: 2026-11-05
- **Decisione**: `deploy.yml` chiama `/api/health` con ritentativi dopo l'applicazione del Bicep. Le migrazioni restano all'avvio dell'app (D-010) e il job non migra.
- **Motivo**: con zero repliche nessuno avvierebbe l'app, e quindi le migrazioni, fino alla prima visita; il job orario girerebbe con il codice nuovo su uno schema vecchio. Far migrare anche il job riaprirebbe la gara sulle migrazioni che D-010 evita.
- **Alternative scartate**: migrazioni nel job; controllo dello schema dentro il job (più codice per lo stesso risultato).

## D-020 · CSV pensati per Excel in italiano

- **Data**: 2026-11-05
- **Decisione**: separatore `;`, UTF-8 con BOM, importi con la virgola decimale (negativi con il segno), date e ore in Europe/Rome. Le celle di testo che iniziano con `=`, `+`, `-` o `@` hanno un apice davanti (anti formule), tranne i numeri di telefono, che restano come scritti.
- **Motivo**: Excel con impostazioni italiane apre il file senza passaggi di importazione e senza rovinare accenti e importi; le iscrizioni contengono testo libero scritto dai partecipanti.
- **Alternative scartate**: `,` come separatore (Excel italiano non lo riconosce); niente BOM (accenti rotti); nessuna protezione dalle formule (rischio con testo libero); apice anche sui telefoni (resterebbe visibile in Excel).

## D-021 · Pagamenti annullati, non cancellati

- **Data**: 2026-11-05
- **Decisione**: un pagamento sbagliato si annulla con un motivo obbligatorio (`voided_at`, `void_reason`). Resta in elenco e in cronologia ma non conta nel pagato, in nessun punto (saldo, promemoria, rimborso). Una prenotazione `confermata` non più coperta torna `in_attesa_pagamento` con un nuovo blocco; l'importo non cambia mai da solo il suo stato in altri casi.
- **Motivo**: i soldi non devono sparire senza traccia; il blocco nuovo evita di far scadere subito chi aveva pagato.
- **Alternative scartate**: cancellare la riga (nessuna traccia); lasciare la prenotazione confermata senza i soldi.

## D-022 · Cronologia delle modifiche manuali in una tabella a parte

- **Data**: 2026-11-05
- **Decisione**: tabella `audit_log` (chi, quando, azione, testo). `booking_id` non è una chiave esterna: la cronologia deve sopravvivere a una prenotazione rimossa, e per questo il testo riporta nome ed email della persona. Si scrive solo per azioni dell'admin.
- **Motivo**: «chi ha cambiato cosa» serve agli organizzatori tra loro; un campo per ogni modifica sulle tabelle esistenti sarebbe sparso e incompleto.
- **Alternative scartate**: campi `modified_by` sparsi; chiave esterna con cancellazione a cascata (perderebbe la traccia delle disdette senza pagamenti).

## D-023 · Rimborso, disdetta e riattivazione da parte dell'admin

- **Data**: 2026-11-05
- **Decisione**: (1) il rimborso registra importo (da 0 a quanto versato), data e nota e non manda email; con importo 0 si chiude una disdetta in cui non è mai stato versato nulla (succede se i pagamenti sono stati tutti annullati); (2) la disdetta a nome della persona segue le regole di quella del partecipante; (3) la riattivazione manuale richiede posto in tutti gli slot e, se i pagamenti coprono già la quota, conferma subito; (4) l'admin può sempre modificare giorni passati, mentre «forza» riguarda solo gli slot pieni.
- **Motivo**: indicazioni di `domain.md` (rimborso fuori dal sistema) e della spec; una disdetta aperta deve poter sempre essere chiusa.
- **Alternative scartate**: email automatica di rimborso (lo scrive l'admin); impedire la riattivazione quando c'è un solo slot pieno (la scelta resta all'admin con «forza» sugli slot).

## D-024 · Regole di rimozione degli admin e proroga del blocco

- **Data**: 2026-11-05
- **Decisione**: non si rimuove se stessi, l'admin definito da `ADMIN_EMAIL` (verrebbe ripromosso all'avvio) né l'ultimo admin; chi perde il ruolo lo perde subito, anche con una sessione già aperta, e la sua iscrizione resta. La proroga del blocco vale solo per `in_attesa_pagamento` e solo in avanti; dopo la proroga si azzerano solo i promemoria la cui nuova soglia è ancora futura (altrimenti uno già ricevuto partirebbe due volte).
- **Motivo**: evitare di restare senza admin e modifiche che non reggono al riavvio; i promemoria devono restare «una volta sola».
- **Conseguenza accettata**: due admin che si rimuovono a vicenda nello stesso istante potrebbero lasciare zero admin (se `ADMIN_EMAIL` è impostata, il primo admin torna al riavvio).

## D-025 · Correzioni dalla revisione della PR #4

- **Data**: 2026-11-05
- **Decisione**: (1) quando una prenotazione viene rimossa, le sue voci di cronologia si staccano dall'id (`booking_id` diventa `NULL`, il testo conserva nome ed email): un id liberato, che SQLite riusa, non fa ereditare la cronologia a una prenotazione nuova (corregge D-022); (2) pagamenti e annullamenti di una prenotazione bloccano la riga (`lock_booking`, con `WITH (UPDLOCK, HOLDLOCK)` su SQL Server) per non applicare due modifiche in parallelo; (3) riattivare una prenotazione scaduta, a mano o con un pagamento, è rifiutato se la persona ha un'altra iscrizione attiva nella stessa edizione (il pagamento resta registrato, con avviso); (4) il promemoria si segna solo se la prenotazione è ancora identica a quando è stata valutata (stato, scadenza, importo).
- **Motivo**: tutti difetti reali emersi dalla revisione: (2) richiede due admin sulla stessa prenotazione nello stesso istante, improbabile ma con effetti gravi (confermata senza soldi); (3) valeva già per i pagamenti dell'MVP 1.
- **Limite noto**: la corsa del punto 2 non è riproducibile in modo deterministico nei test (SQLite non sa fare lock di riga): il test controlla che la query contenga l'hint per SQL Server.
