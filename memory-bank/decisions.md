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

## D-026 · Lista d'attesa: voci chiuse, mai cancellate

- **Data**: 2026-11-05
- **Decisione**: ogni voce in lista ha `closed_at` e un motivo (`promoted`, `left`, `removed`, `cancelled`, `booked`); non si cancella mai. I testi legali accettati stanno anche sulla voce, così chi è solo in lista può ricevere una prenotazione nuova senza ripassare dal modulo. Chi entra dalla pagina personale riusa i testi della sua ultima prenotazione. Un giorno che ha avuto voci in lista non si toglie dalle Impostazioni.
- **Motivo**: la storia serve al report dell'MVP 7 e alla cronologia; la promozione deve poter creare una prenotazione valida.
- **Alternative scartate**: cancellare le voci (nessuna traccia); prenotazione «vuota» per chi è solo in lista (stato nuovo da gestire ovunque).

## D-027 · Promozione dopo il commit, dallo strato API e dal job orario

- **Data**: 2026-11-05
- **Decisione**: `promote_freed` gira dopo il commit dell'operazione che libera i posti, uno slot alla volta, ciascuno in una transazione propria con il lock sullo slot. La chiamano gli endpoint di disdetta e cambio slot (partecipante e admin) e il salvataggio delle Impostazioni; le scadenze le gestisce il job orario dei promemoria, che fa un passo in più. Il limite della lista si arrotonda per difetto. Dopo una promozione su una prenotazione in attesa i promemoria si ricalcolano come dopo una proroga (D-024).
- **Motivo**: i servizi esistenti restano invariati e non dipendono dalla configurazione; la lettura non manda email, quindi una scadenza la nota solo il job (entro un'ora, accettato dal maintainer).
- **Alternative scartate**: promozione alla lettura (email inviate da una GET); un job dedicato (un'altra risorsa Azure per lo stesso orario).
- **Limite noto**: se l'operazione riesce e la promozione fallisce (errore improvviso), il posto resta libero finché il job orario non lo assegna.

## D-028 · Persone solo in lista nel pannello

- **Data**: 2026-11-05
- **Decisione**: in «Persone» chi è solo in lista compare con stato «Solo in lista d'attesa», senza scheda (la scheda è per prenotazione); la lista si gestisce da «Giorni e slot», dove l'admin può togliere una voce senza email, con cronologia.
- **Motivo**: evita una seconda scheda per persona per un caso raro.
- **Alternative scartate**: scheda per persona (nuova pagina e nuovi endpoint, fuori dalla dimensione dell'MVP).

## D-029 · Un solo punto calcola l'importo dovuto

- **Data**: 2026-11-05
- **Decisione**: `services/amounts.recompute_amount` scrive `amount_due_cents` da slot e pasti, ai prezzi correnti dell'edizione (come D-017). La usano iscrizione, cambio slot, pasti e promozione dalla lista; l'MVP 6 vi aggiungerà le attività. Prezzi segnaposto: pranzo 8 €, cena 12 €.
- **Motivo**: con più voci di costo, calcoli sparsi divergerebbero.
- **Alternative scartate**: salvare un importo per riga (pasto, slot) e sommarlo (più dati per lo stesso risultato).

## D-030 · Dati sanitari sulla prenotazione, consenso che non blocca l'iscrizione

- **Data**: 2026-11-05
- **Decisione**: regime, allergie e consenso stanno su `booking`, non su `participant`. Il consenso è un testo legale versionato (`health`) ma fuori dai testi che aprono le iscrizioni: senza testo pubblicato si indica solo il regime. Il CSV dei pasti chiede conferma prima del download perché contiene dati sanitari.
- **Motivo**: i dati valgono per un'edizione e spariscono con la prenotazione rimossa (minimizzazione); i pasti non devono fermare le iscrizioni.
- **Alternative scartate**: dati sulla persona (resterebbero da un anno all'altro); consenso obbligatorio per iscriversi (non tutti hanno allergie).

## D-031 · I pasti cadono da soli quando cambia la presenza

- **Data**: 2026-11-05
- **Decisione**: togliere uno slot fa cadere i pasti a cui non si ha più titolo; la risposta e la cronologia lo dicono. Vale anche per l'admin, che per dare un pasto deve prima dare la presenza.
- **Motivo**: bloccare il cambio di slot finché non si tolgono i pasti a mano sarebbe un passaggio in più senza vantaggi.
- **Alternative scartate**: rifiutare il cambio di slot; lasciare pasti senza presenza (conteggi sbagliati per la cucina).

## D-032 · Attività legate a giorno e fascia, con presenza obbligatoria

- **Data**: 2026-11-05
- **Decisione**: un'attività ha un giorno, una fascia (mattina, pomeriggio, sera) e un orario indicativo libero. Si aderisce solo se presenti in quella fascia (sera derivata compresa, D-009); la regola vale anche per l'admin, che può però superare la capienza con «forza» e cambiare giorni passati. Il conteggio dei posti e il lock sulla riga seguono gli slot (D-011).
- **Motivo**: scelta del maintainer; la fascia riusa la regola di presenza dei pasti senza confrontare orari liberi.
- **Alternative scartate**: orario libero di inizio e fine (confronti con gli slot più fragili); attività su tutto il giorno (Backlog).

## D-033 · Attività bloccate dopo la prima adesione e riattivazione senza le attività piene

- **Data**: 2026-11-05
- **Decisione**: con iscritti non si cambiano prezzo, giorno e fascia e non si elimina (conta ogni prenotazione che la tiene, anche scaduta); la capienza non scende sotto chi occupa un posto. Quando una prenotazione scaduta torna attiva (riattivazione o pagamento), le attività nel frattempo piene cadono con avviso e cronologia: cambia la spec, che diceva «l'admin decide se forzare».
- **Motivo**: gli importi non devono cambiare alle spalle delle persone; la riattivazione da pagamento non ha nessuno che possa forzare, e la regola è la stessa dei pasti (D-031).
- **Alternative scartate**: ricalcolare gli importi di tutti al cambio di prezzo; rifiutare la riattivazione per un'attività piena.

## D-034 · Contributi sulla prenotazione

- **Data**: 2026-11-05
- **Decisione**: tabella `contribution` legata alla prenotazione, tre tipi (talk, tema, competenza), più contributi per persona, modificabili solo da chi li ha scritti. Nella vista admin quelli di prenotazioni non attive restano, segnati. Si aggiungono solo con un'iscrizione in attesa o confermata.
- **Motivo**: valgono per un'edizione e spariscono con la prenotazione rimossa; il meccanismo dell'unconference resta da definire (Backlog).
- **Alternative scartate**: estendere il campo libero «cosa puoi portare» (non filtrabile né esportabile per tipo).

## D-035 · Stile del sito: token CSS, font self-hosted e modalità iframe

- **Data**: 2026-11-05
- **Decisione**: (1) tutti i colori sono token su `:root` in `frontend/src/styles.css`, con la palette del sito Cissone Eventi (petrolio `#005C68` per link e focus, ambra `#F4B400` solo come sfondo del bottone principale); un test vitest controlla i contrasti AA e che non ci siano colori fuori da `:root`; (2) Montserrat è incluso nella build con `@fontsource/montserrat` (pesi 400, 600, 700); (3) dentro un iframe la pagina aggiunge la classe `in-frame` a `<html>`, ha lo sfondo trasparente e un'intestazione ridotta al solo nome; (4) bottoni e campi squadrati (`--radius: 0`); (5) il logo di Cissone è nel bundle con il permesso della Pro Loco e non rientra nella licenza MIT (nota nel README).
- **Motivo**: indicazioni del maintainer; il modulo di iscrizione deve sembrare parte del sito che lo incorpora. I font serviti dall'app evitano richieste a Google Fonts (privacy dei visitatori) e cambi alla CSP. L'ambra su bianco ha contrasto 1,85:1, quindi non può fare da testo, bordo informativo o focus.
- **Alternative scartate**: Google Fonts dal CDN (richieste a terzi, CSP da allargare); framework CSS (dipendenza in più per un foglio di stile piccolo); nascondere del tutto l'intestazione nell'iframe (il maintainer ha scelto quella ridotta); modalità scura (esclusa dal maintainer).

## D-036 · Titolo per pagina e menu admin scorrevole

- **Data**: 2026-11-05
- **Decisione**: (1) ogni rotta ha un `document.title` proprio («Pagina · Cissonauti Summer Camp»), calcolato in `frontend/src/pageTitle.ts`; (2) il menu del pannello è una riga che scorre di lato e porta in vista la voce corrente, invece di andare a capo su più righe; (3) gli stati delle prenotazioni sono etichette colorate senza bordo laterale; un test impedisce bordi laterali spessi.
- **Motivo**: emersi dall'audit dell'MVP 8: il titolo uguale ovunque non rispetta WCAG 2.4.2; con 10 voci il menu occupava più di metà schermo su telefono.
- **Alternative scartate**: menu a tendina (un tocco in più per ogni cambio di vista, per chi usa il pannello tutto il giorno); due righe di menu (non bastano per 10 voci con aree di tocco da 44 px).

## D-037 · Priorità +1 calcolata alla promozione, verifica sul partecipante, report a lettura

- **Data**: 2026-11-05
- **Decisione**: (1) l'ordine della lista si calcola ogni volta (`queue(entries, priority_ids)`): prima i +1 verificati, poi gli altri, dentro ogni gruppo per ordine di arrivo; nessuna posizione è salvata, quindi una verifica fatta dopo l'ingresso vale subito; (2) la verifica sta sul partecipante (`plus_one_verified_at`, `plus_one_verified_by_id`) e si imposta per id partecipante, perché chi è solo in lista non ha una prenotazione né una scheda (D-028); cade da sola se «invitato da» si svuota; (3) il report non ha tabelle: `load_report` legge tutto e `edition_report` conta, con presenze, pasti e attività divisi in confermate e in attesa e il dovuto scomposto in quota, pasti e attività con una riga «differenza» che assorbe i prezzi cambiati dopo le iscrizioni (D-017); (4) CSV del report in formato lungo (`sezione;voce;confermate;in attesa;totale`); (5) allergie solo come numero; (6) «promossi che erano +1» legge `waitlist_entry.promoted_as_plus_one`, salvato al momento della promozione (migrazione 0009), così verificare o togliere la verifica dopo non riscrive il passato; (7) `load_report` carica le collezioni delle prenotazioni in blocco (`selectinload`), un test controlla che le query non crescano con le prenotazioni.
- **Motivo**: indicazioni del maintainer; la priorità non deve dipendere da una posizione salvata che andrebbe riscritta a ogni cambio; il report deve coincidere con le altre viste e non esporre dati sanitari.
- **Alternative scartate**: posizione salvata (da ricalcolare a ogni verifica e uscita); verifica sulla prenotazione (esclude chi è solo in lista); posti riservati ai +1 (scelta del maintainer: nessun posto riservato); tabella di snapshot del report (due fonti di verità).
- **Limiti noti**: con più edizioni la verifica andrebbe spostata (Backlog); chi scende di posizione non riceve avvisi (Backlog dell'MVP 4).


## D-038 · Design system Cissone al posto dello stile del sito Google

- **Data**: 2026-11-05
- **Decisione**: (1) tutta l'app usa il design system «Cissone Summer Camp» (README del design system): carta crema, petrolio `#335c67`, ambra `#ffbc42` solo come riempimento, mattone `#a84c4c` per enfasi ed errori, Montserrat 800 maiuscolo per i titoli, Figtree per il testo, JetBrains Mono per orari e codici, pulsanti a pillola, schede bianche con raggio 12-20 px e ombre calde; sostituisce la palette dell'MVP 8 (D-036 resta valida per il resto); (2) la scelta delle giornate è il componente condiviso `DayPicker` (iscrizione, pagina personale, scheda admin): tessere cliccabili ovunque, «Tutta la giornata» per giorno, selezione rapida per fascia; le azioni di gruppo non aggiungono mai uno slot completo; (3) l'iscrizione ha un riepilogo laterale (barra in basso su telefono).
- **Motivo**: feedback del maintainer sul mockup; stessa configurazione, colori del design system.
- **Alternative scartate**: percorso in 3 passi del mockup (cambia il flusso e i test, nel Backlog); accordion per giorno su telefono (l'elenco di tessere è già compatto).
- **Nota audit**: Impeccable `detect` segnala solo `cream-palette`: la carta crema è prescritta dal design system, quindi accettata.


## D-039 · Guida in app nel repo, note di rilascio dai commit

- **Data**: 2026-11-05
- **Decisione**: (1) la guida sono file Markdown in italiano in `frontend/src/guide/{partecipante,admin}/`, inclusi nella build con `import.meta.glob`: ogni deploy pubblica la guida del codice; quella admin si carica a richiesta, così i partecipanti non la scaricano; (2) il filtro per ruolo è in due strati: la pagina `/guida` mostra al partecipante solo la sua guida, e le note di rilascio passano da `GET /api/admin/release-notes` (`require_admin`); il testo della guida admin è nel bundle e non è un segreto, per questo non c'è un'API dedicata; (3) le note le genera `scripts/release_notes.py` al deploy dalla storia git: ogni merge su `main` è un rilascio fatto dei commit `feat`, `fix`, `perf` del ramo unito; il JSON finisce in `backend/release_notes.json` (fuori da git) dentro l'immagine; (4) versione e data di build arrivano dalle build args `APP_VERSION` e `BUILT_AT` e si leggono da `GET /api/version`; (5) il controllo che la guida segua le modifiche è un workflow a parte (`guide.yml`) che guarda il diff, test esclusi, e si salta con la label `senza-guida`; (6) il Markdown si rende con `marked`, perché i testi sono del repo e non input degli utenti.
- **Motivo**: richiesta del maintainer: guida filtrata per ruolo, aggiornata a ogni deploy, note solo per gli admin. Tenere i testi nel repo li fa rivedere nelle PR insieme al codice.
- **Alternative scartate**: guida salvata nel database o modificabile dal pannello (due fonti di verità, nessuna revisione); note scritte a mano (lavoro in più a ogni PR); API che serve la guida admin solo agli admin (complessità senza segreti da proteggere); controllo di CI dentro `ci.yml` (la label non rilancerebbe solo quel controllo).
- **Limiti noti**: il controllo di CI verifica che la guida sia stata toccata, non che sia giusta; le note sono in inglese perché lo sono i commit (Backlog); la prima volta le note compaiono dopo il primo deploy con questa versione.

## D-040 · Vista «Da incassare» con email di conferma differita e salvata nel database

- **Data**: 2026-11-05
- **Decisione**: (1) pagina `/admin/da-incassare` con tasto «Segna pagato» che registra il saldo intero e annullo visibile per 10 secondi, riusando registrazione e annullo dei pagamenti; (2) con il flag `defer_confirmation_email` la prenotazione si conferma subito ma l'email parte dopo 30 secondi: la scadenza sta su `payment` (`confirmation_email_due_at`, `confirmation_email_sent_at`, migrazione 0010); (3) la esegue un timer in processo (`app.state.run_later`), con rete di sicurezza nel job orario; l'invio è reclamato con un UPDATE condizionale, come i promemoria; (4) dalla scheda l'email resta immediata.
- **Motivo**: richiesta del maintainer: controllare il conto e segnare le quote in fila, con rimedio a un clic sbagliato. L'app scala a zero, quindi un timer solo in memoria può perdere l'email.
- **Alternative scartate**: solo timer in memoria (email perse a ogni riavvio); coda o job ogni minuto (infrastruttura in più); ritardare l'email anche dalla scheda (scelta del maintainer: solo dalla vista); conferma con dialogo a ogni riga (più lento per chi controlla il conto).
- **Limiti noti**: se il timer si perde l'email arriva al passaggio orario successivo; un errore di consegna non si ritenta; con due admin sulla stessa riga il tasto registra l'importo mostrato.


## D-041 · Due lingue senza libreria: dizionari tipizzati e lingua in una variabile di contesto

- **Data**: 2026-11-05
- **Decisione**: (1) frontend: dizionari piatti `i18n/it.ts` e `i18n/en.ts`, con `en` tipizzato su `keyof typeof it` (una chiave mancante non compila) e un test sui segnaposto; hook `useT()`/`useI18n()`, plurali con le chiavi `.one`/`.other` e `Intl.PluralRules`; lingua da `?lang`, poi scelta salvata, poi lingua del browser (`it*` → italiano, altrimenti inglese); (2) backend: catalogo `app/i18n.py` con `t(chiave, **parametri)` che legge la lingua da una variabile di contesto impostata da un middleware ASGI su `Accept-Language`, così i servizi non si passano la lingua; email e job, che non hanno una richiesta, la prendono da `participant.locale`; (3) il frontend manda `Accept-Language` a ogni chiamata, quindi anche le etichette fatte dal server (slot, pasti, attività) escono nella lingua giusta e la pagina personale ricarica i dati quando si cambia lingua; (4) l'oggetto delle email usa il nome del marchio fisso «Cissonauti Summer Camp», non `edition.name` (la spec lo prevedeva, ma cambiava l'oggetto delle email esistenti: resta all'MVP 13, dove l'oggetto diventa modificabile).
- **Motivo**: richiesta del maintainer di un'app in italiano e inglese; ogni nuova funzione deve nascere bilingue (regola in `AGENTS.md`).
- **Alternative scartate**: libreria i18n (react-i18next o simili: una dipendenza per 400 chiavi piatte, senza controllo di compilazione sulle chiavi mancanti); `AppError(chiave)` con handler (obbligava a cambiare ogni punto in cui si lancia un errore e a far passare la lingua nei servizi); rimontare le pagine a ogni cambio di lingua (farebbe perdere i campi già scritti nell'iscrizione).
- **Limiti noti**: i contenuti scritti dagli organizzatori (nomi e testi delle attività, istruzioni di pagamento, testi legali) restano come scritti (Backlog); le voci di cronologia e i testi di sistema delle viste admin si traducono con l'MVP 12; i messaggi del server nelle pagine admin dipendono dalla lingua della richiesta.

## D-042 · Indirizzi in inglese con alias italiani che reindirizzano

- **Data**: 2026-11-05
- **Decisione**: i percorsi sono definiti in `frontend/src/routes.ts` (inglese: `/register`, `/login`, `/login/verify`, `/me`, `/guide`, `/admin/days`...). La rotta `*` chiama `canonicalPath()`: se il percorso è un alias italiano (scritto a mano o da un vecchio link) fa un redirect con `replace`, conservando query e hash; la query `?scheda=organizzatori` della guida diventa `?tab=organizers`. Il backend genera solo link inglesi; la CSP `frame-ancestors` di Google Sites vale sia per `/register` sia per `/iscrizione`, perché il redirect avviene dentro l'iframe.
- **Motivo**: link leggibili in inglese, ma i magic link già nelle caselle e l'iframe già incorporato nel sito non devono rompersi.
- **Alternative scartate**: due insiemi di rotte uguali (due indirizzi per la stessa pagina, titoli e link doppi); redirect lato server (il frontend è una app a pagina singola servita con un fallback unico).
- **Limiti noti**: gli alias coprono solo i percorsi che esistevano; nessun alias per quelli nuovi.

## D-043 · Guida in due lingue con file omonimi

- **Data**: 2026-11-05
- **Decisione**: la guida sta in `frontend/src/guide/{it,en}/{participant,admin}/NN-<slug-inglese>.md`: stessa numerazione e stesso nome nelle due lingue, ancore in inglese. Un test confronta le sezioni dei due elenchi, e `check-guide.sh` chiede di toccare la guida in tutte e due le lingue. Fino all'MVP 12 la guida organizzatori inglese manca e il caricamento ricade sull'italiano.
- **Motivo**: le due versioni si rivedono insieme nella stessa PR e non si disallineano.
- **Alternative scartate**: guida inglese generata da traduzione automatica a ogni build (testi non rivisti); un solo file con le due lingue (diff illeggibili).


## D-044 · Pannello admin in due lingue: tabella di etichette per i CSV, cronologia lasciata com'è

- **Data**: 2026-11-05
- **Decisione**: (1) il pannello admin usa gli stessi dizionari dell'MVP 11 e si rimonta quando cambia la lingua (`AdminLayout`), perché le sue viste mostrano etichette scritte dal server; (2) i link «Scarica CSV» sono semplici link e non mandano `Accept-Language`: la lingua viaggia nell'indirizzo (`?lang=en`) e il middleware la preferisce all'intestazione; (3) intestazioni, nomi dei file, valori fissi e righe del report CSV restano scritti in italiano nel codice e si traducono con `tr()`, grazie alla tabella `LABELS_EN` in `app/admin_texts.py`; un test controlla che ogni intestazione di ogni CSV abbia la sua versione inglese; formato (`;`, BOM, virgola decimale, date `gg/mm/aaaa`) invariato, per Excel italiano; (4) gli avvisi che le API mostrano all'admin passano dal catalogo con `t()`; (5) la cronologia delle modifiche («Cronologia» della scheda) è un registro: le voci nuove si scrivono ancora in italiano e quelle vecchie non si toccano.
- **Motivo**: richiesta del maintainer di un'interfaccia tutta bilingue; i CSV e la scheda sono usati ogni giorno dagli organizzatori.
- **Alternative scartate**: scaricare i CSV con `fetch` per mandare l'intestazione (perde il download nativo e l'avviso sui dati sanitari); tradurre qualunque cella di un CSV (traduce anche nomi di persone uguali a una etichetta); voci di cronologia strutturate e tradotte alla lettura (richiede un cambio di schema, nel Backlog).
- **Limiti noti**: la cronologia resta in italiano; il separatore `;` e le date `gg/mm/aaaa` restano anche nei CSV inglesi; i nomi e i testi scritti dagli organizzatori non si traducono.


## D-045 · Email di iscrizione personalizzabile con immagine generata dal server

- **Data**: 2026-11-05
- **Decisione**: (1) l'admin scrive oggetto e testo iniziale per lingua (tabella `email_template`) e la frase dell'immagine, con colore e posizione (tabella `registration_card`, migrazione 0012); i segnaposto sono `{first_name}`, `{last_name}`, `{event}`, `{start_date}`, `{end_date}` e uno sconosciuto è rifiutato al salvataggio; (2) il testo scritto sostituisce solo saluto e introduzione: slot, quota, causale, scadenza, istruzioni e link restano generati dal sistema, in fondo e non modificabili; con i campi vuoti la email è identica a prima; (3) l'immagine è un PNG composto dal server con Pillow (sfondo caricato dall'admin + frase, Montserrat 800 con licenza OFL in `backend/app/assets/fonts/`): così si vede uguale in tutti i programmi di posta e la persona può salvarlo e condividerlo; (4) lo sfondo caricato non si conserva com'è: si controlla formato (JPEG, PNG, WebP), dimensione (5 MB) e numero di pixel, si corregge la rotazione, si riduce a 1600 px e si ricodifica in PNG, togliendo metadati; sta nel database come `LargeBinary`; (5) la email diventa multipart: testo semplice + HTML (tutto escapato, link cliccabili) con l'immagine inline (`cid:`) tramite gli allegati di Azure Communication Services; (6) l'immagine c'è solo se è stato caricato uno sfondo e solo per chi si iscrive con una prenotazione; (7) l'admin ha un'anteprima (con il nome «Ada Lovelace», che segue quanto scrive) e «Inviami una prova» (con il suo nome, nella lingua scelta).
- **Motivo**: richiesta del maintainer: testo della conferma modificabile e immagine con «I'm nome cognome and I'll be at evento from data to data».
- **Alternative scartate**: sfondo CSS con testo HTML sopra (Outlook e molte app ignorano gli sfondi, e non è un'immagine condivisibile); Azure Blob Storage per lo sfondo (una risorsa in più per un file solo); testo della email completamente libero (si poteva togliere il link di accesso per sbaglio); un testo unico bilingue (le persone riceverebbero tutto in due lingue).
- **Limiti noti**: alcuni client (Gmail per alcuni account, Outlook) mostrano le immagini inline solo dopo un clic su «mostra immagini»; il testo accanto resta leggibile; i caratteri non latini (cirillico, arabo, CJK) non hanno glifi in Montserrat e comparirebbero come riquadri; la prova non mostra un blocco di pagamento reale ma i canali attivi; l'oggetto personalizzato non ha un limite di lunghezza oltre i 200 caratteri.


## D-046 · Dopo la review della PR #13: lingua non modificabile dal modulo pubblico, 0011 senza default, ancore e undo

- **Data**: 2026-11-06
- **Decisione**: (1) il modulo pubblico di iscrizione non cambia mai la lingua salvata di una persona che esiste già (a differenza di quanto scritto in D-041 e nella spec dell'MVP 11): chiunque conosca un'email potrebbe farlo; le email di quella richiesta partono comunque nella lingua del modulo e la lingua salvata si cambia solo da loggati; (2) la colonna `participant.locale` nasce senza default del database (aggiunta vuota, riempita con `it`, poi resa obbligatoria): su SQL Server un default è un vincolo con nome generato che va tolto prima della colonna e il downgrade falliva; il valore `it` lo dà l'ORM; (3) i vecchi indirizzi della guida portano anche le vecchie ancore (`#giorni-e-slot` → `#days-and-slots`); (4) il cambio di lingua non rimonta «Da incassare», per non perdere i pagamenti appena segnati e i loro 10 secondi di annullo (D-040); le altre pagine admin si rimontano ancora.
- **Motivo**: review di Copilot sulla PR #13 e controllo «Backend su SQL Server» rosso.
- **Limiti noti**: sulle altre pagine admin un cambio di lingua perde i campi non salvati (per esempio un importo scritto e non registrato); la 0011 è stata riscritta prima del merge, quindi un database di sviluppo che l'aveva già applicata va riportato a `0010` e riapplicato.


## D-047 · Testi dell'evento: stesso editor per lingua di main, nome edizione ovunque, accesso diretto

- **Data**: 2026-11-06
- **Decisione**: (1) il nome nell'intestazione, nel titolo delle pagine e negli oggetti delle email è `edition.name` (contesto React `EventNameProvider` con ripiego «Cissonauti Summer Camp»; `EmailTexts.event_name` nelle email), non più una costante; (2) le altre 8 email usano la tabella `email_template` dell'MVP 13 (`kind`, `locale`, oggetto, testo) con gli stessi segnaposto: il testo scritto dall'admin sostituisce saluto e prima frase, i dati della prenotazione restano sempre in fondo e non si modificano; per questo i testi che contenevano dati (link, importo, scadenza, slot assegnato) sono stati spezzati in frase e riga di dati in `email_texts.py`; le frasi finali di cortesia («Ci vediamo presto!», «Se hai già pagato…») restano fisse; (3) il paragrafo sopra il modulo sta in due colonne dell'edizione (`registration_intro_it`, `registration_intro_en`, migrazione 0013), l'API pubblica le restituisce entrambe perché la pagina cambia lingua senza ricaricare; (4) dopo il login (password o link) si va sempre a `/me`, gli admin hanno il pulsante verso il pannello e «La mia pagina» nel menu admin; (5) il magic link vale 10 minuti ed è riusabile in quel tempo (`used_at` registra solo il primo uso), la pagina di verifica entra da sola con una guardia contro la doppia chiamata di StrictMode; (6) il primo salvataggio concorrente dello stesso testo riprova come aggiornamento invece di dare 500.
- **Motivo**: richieste del maintainer; `main` aveva già un editor per lingua della mail di iscrizione, quindi gli altri testi vi si agganciano invece di avere una seconda tabella e una seconda pagina con segnaposto diversi; il riuso del link entro 10 minuti toglie il clic «Entra» senza che gli scanner di posta lo brucino.
- **Alternative scartate**: tabella `email_text` con apertura e chiusura separate e solo italiano (prima versione, tolta dopo l'unione con l'MVP 11-13); link monouso con la pagina «Entra» (un clic in più); link monouso che entra da solo (lo scanner lo brucia); obbligare `{event}` negli oggetti (toglie libertà all'admin); riga di `email_template` per il paragrafo del modulo (non è una email).
- **Limiti noti**: un'email inoltrata dà accesso per 10 minuti; i testi cambiano solo le email future; un oggetto scritto senza `{event}` non segue la rinomina dell'edizione; la chiusura dopo i dati non è modificabile; anteprima dell'email completa e invio di prova delle altre email nel Backlog.


## D-048 · Logo personalizzato per edizione e accesso dal marchio

- **Data**: 2026-11-06
- **Decisione**: (1) il logo opzionale è una colonna binaria differita su `edition` (migrazione 0014), elaborata come PNG con le stesse protezioni d'upload dell'immagine email, conservando la trasparenza e limitando il lato massimo a 1600 px; il file in bundle resta il ripiego; (2) endpoint admin di caricamento e rimozione, endpoint pubblico solo lettura, `logo_url` con SHA-256 completo e cache immutable; (3) il clic sul marchio apre `/me`, con il redirect login già presente; (4) il modulo mostra «Accedi» in tutte le condizioni, apre il login nella stessa scheda fuori dall'iframe e in una scheda nuova dentro il frame, conservando `?lang=`.
- **Motivo**: richieste del maintainer. Il logo e il nome già esistono per ogni edizione, e memorizzare i byte normalizzati nel database segue la scelta fatta per la card email (D-045) senza una risorsa cloud aggiuntiva; il caricamento differito evita di trasferire l'immagine nelle richieste che non la usano.
- **Alternative scartate**: URL remoto per il logo (dipendenza dal server dell'immagine e origine esterna); usare il logo personalizzato dentro l'iframe (duplicazione dell'intestazione del sito ospitante).


## D-049 · Importi incassati dagli organizzatori e pagamenti diretti

- **Data**: 2026-11-06.
- **Decisione**: modalità `organizer`/`provider`, costo visibile distinto da `collectable_cents`. Le attività conservano il prezzo esistente; i pasti delegati usano configurazione per edizione/data/tipo, con ritorno ai prezzi generali per organizer. I nuovi orari sono intervalli UTC, scelti localmente nella fascia, mentre i testi preesistenti restano leggibili.
- **Ricalcolo**: modifiche economiche ricalcolano solo prenotazioni attive interessate, in transazione e con cronologia. I versamenti e le scadenze restano; crediti visibili, confermate stabili, in attesa confermate se coperte. La riattivazione di una scaduta rilegge le condizioni attuali e ricalcola anche senza attività eliminate.
- **Concorrenza**: le scritture HTTP acquisiscono il lock dell’edizione prima dei lock preesistenti; anche ogni promozione del job lo acquisisce prima di scadenze e slot, ricaricando l’edizione dopo il lock. Il volume dell’evento consente questa serializzazione semplice, con hint SQL Server UPDLOCK/HOLDLOCK.
- **Alternative scartate**: prezzo zero per simulare il pagamento esterno (nasconde il costo reale); bloccare i cambi con iscritti (il maintainer richiede il ricalcolo); migrare automaticamente testi orari ambigui (rischio di inventare orari).

## Collaudo del 7 novembre 2026 · Decisioni di prodotto

**Data comune:** 2026-11-07. **Fonte e motivo:** nuova versione di `prompt-nuovi-requisiti-cisonauti.md` fornita dal maintainer dopo il collaudo con l'organizzatrice. Le decisioni sotto sono requisiti da specificare, non funzioni già implementate; approvazione delle spec e dei singoli MVP ancora attesa. Questa tabella è il registro unico delle nuove decisioni nella Memory Bank; gli altri file vi rimandano. Le alternative non chiuse sono nel [registro delle domande](../specs/revisione-2026-11-07/domande-aperte.md), non sono considerate scartate.

| ID | Fonte | Decisione | Motivo / alternativa esclusa o limite |
|---|---|---|---|
| D-050 | Fase e vincoli generali | Preparare solo Memory Bank, spec, MVP, domande e valutazioni, preservando iscritti e pagamenti esistenti, accessi autenticati, versionamento privacy, IT/EN e logo escluso dalla MIT. | Nessun codice applicativo o implementazione prima dell'approvazione; domini, always-on, revisione magic link admin, calendario automatico e wall fisico fuori ambito. |
| D-051 | A1–A2 | Raccogliere con checkbox due consensi facoltativi distinti, presenza sul sito (nome, cognome, job title, LinkedIn) e foto/video, separati dalla privacy generale e dalle altre finalità esistenti. | Escluso un consenso unico o implicitamente concesso; portata della pubblicazione da chiarire Q-A1/A8/A9. |
| D-052 | A3 | Non offrire elenchi pubblici degli iscritti e mantenere l'invitante come testo libero verificato dall'admin. | Escluse anche tendine nominali; aggiorna il Backlog sulla relazione invitante, Q-A2 per l'esistenza dell'email. |
| D-053 | A4 | Richiedere telefono, Telegram, LinkedIn, provenienza, job title e company, aspettative e precedente partecipazione nei nuovi invii, mantenendo il flusso giorni/slot/pasti. | Telefono già presente in MVP 16 da riusare, non reimplementare. Formati e casi senza profili da chiarire. |
| D-054 | A4 / compatibilità | Gestire i campi mancanti degli iscritti precedenti senza invalidarne iscrizioni o pagamenti. | Esclusi valori fittizi e obbligatorietà retroattiva che blocchi dati validi; modalità di completamento Q-A3. |
| D-055 | A5 | Richiedere una nuova accettazione quando cambia la privacy attraverso il versionamento esistente. | Il solo salvataggio di un nuovo testo non vale come accettazione; operazioni consentite da definire. |
| D-056 | A6 | Rendere ogni cancellazione consultabile nello storico amministrativo e verificarla soltanto con la procedura manuale del maintainer. | Supera la perdita di traccia accettata in D-018 ed estende il perimetro storico di D-022/D-025, senza modificare ora il codice. |
| D-057 | B1 | Confermare il posto quando è coperta la quota di registrazione, lasciando gli extra dovuti senza bloccare la conferma. | Sostituisce come obiettivo il criterio sul totale di D-017/D-021/D-049; formula esatta e transizione Q-B1/B2. |
| D-058 | B2 | Mostrare l'importo necessario a confermare e dichiarare che pranzi, cene e attività possono essere pagati dopo. | Importo dalle impostazioni/calcolo server, non un testo o valore fisso. |
| D-059 | B3 | Registrare importi diversi dal totale attraverso una modale rapida nella lista Da incassare. | Estende MVP 10, senza obbligare ad aprire la scheda completa né duplicare il registro pagamenti. |
| D-060 | B4 | Rendere configurabili voci e quantità di pasti comprese nella quota, con default di un solo pasto, primo pranzo oppure prima cena nel calendario del partecipante. | Gli altri pasti restano dovuti ai prezzi impostati; niente default implicito di un pranzo più una cena. |
| D-061 | B5 | Mantenere due modalità, incasso dell'organizzazione e pagamento in loco al fornitore, sostituendo le diciture ambigue sull'inclusione e sul destinatario. | Riusa organizer/provider di D-049; modalità d'incasso e composizione della quota sono concetti distinti. |
| D-062 | C1 | Mostrare informazioni complete e titolo leggibile di ogni attività anche nei riepiloghi. | Un numero/identificativo da solo non descrive l'attività. |
| D-063 | C2 | Contare non paganti, esterni paganti ed esterni non paganti nella logistica di pasti/attività senza sommarli a quote e importi dell'organizzazione. | Semantica di esterno pagante, presenza e capienze da chiarire prima della spec esecutiva. |
| D-064 | C3 | Separare le note interne delle attività dai contenuti visibili ai partecipanti e renderle disponibili solo agli admin. | Esclusa la semplice omissione visiva di un campo ancora presente nelle risposte partecipante. |
| D-065 | C4 | Aprire una scheda attività precompilata da un contributo, lasciando all'organizzazione data e collocazione. | Nessun calendario o salvataggio automatico; cardinalità del collegamento da chiarire. |
| D-066 | C5 | Definire i benefit nelle impostazioni e registrarne la consegna per persona in una pagina dedicata. | Catalogo e consegne distinti, ambito edizione da considerare con F. |
| D-067 | D1 | Aprire il dettaglio dei conteggi settimanali in una modale admin tramite i numeri cliccabili. | Conteggio e dettaglio devono spiegare la stessa metrica. |
| D-068 | D2 | Portare prima il giorno corrente e i futuri, spostando i trascorsi in fondo, con rilascio lontano dalle demo. | Politica di aggiornamento e ordine finale da definire; non accorpare a una demo. |
| D-069 | D3 | Valutare prima un mockup del calendario admin con box mattina/pomeriggio/sera. | Nessuna implementazione della vista calendario in questa fase. |
| D-070 | D4 | Rinviare tratto.email preparando soltanto una bozza di MVP per comunicazioni a gruppi per stato. | Nessun dettaglio d'integrazione, configurazione o invio reale ora; D5 è verifica di ciò che esiste, non un nuovo sistema. |
| D-071 | E1 | Mantenere la barra importo/iscrizione sempre in alto durante lo scorrimento, rendendola più visibile. | Conferma la correzione del 7 novembre e supera il vecchio riferimento alla barra inferiore di D-038. |
| D-072 | E2 | Far scorrere con la pagina il recap a destra del riepilogo giorni, con fondo bianco e striscia più evidente. | Escluso un secondo pannello fisso; il resto del design system non è ridisegnato. |
| D-073 | E3 | Offrire una modale separata delle proposte altrui agli autenticati, con nome solo se coperto da consenso presenza A2, e aggiungere competenze cercate. | La visibilità del testo senza consenso resta Q-E1; non si concede accesso alle API admin. |
| D-074 | A7 | Preparare soltanto bozza e proposta grafica della mappa regionale aggregata delle provenienze, senza dati personali. | Soglie/base di pubblicazione da concordare, nessuna mappa implementata ora. |
| D-075 | F | Valutare alternative per nuova edizione e storico, inclusi account, consensi, conservazione e impatto A–E, senza spec esecutiva. | La raccomandazione dello stesso database non è ancora una scelta approvata; nessun reset o deploy autorizzato. |

Spec e confronto con le regole esistenti: [revisione del collaudo](../specs/revisione-2026-11-07/README.md). D-014/D-016 rimangono il riferimento per il sistema di promemoria già esistente; [D5](../specs/revisione-2026-11-07/d-admin-comunicazioni/promemoria-esistenti.md) ne documenta il riscontro senza dichiarare verificata la produzione.

## Risposte del maintainer · 7 novembre 2026

**Data comune:** 2026-11-07. **Fonte/motivo:** risposte dirette del maintainer alla revisione, compresa la successiva conferma «Incasso separato dell'organizzazione» per gli esterni. Queste precisazioni prevalgono sui punti ancora ambigui e sulle alternative proposte in D-050–D-075; la sezione precedente rimane come storia, non come richiesta di nuova conferma. Nessun codice applicativo è stato implementato con questo aggiornamento.

| ID | Fonte | Decisione confermata | Precisazione / alternativa superata |
|---|---|---|---|
| D-076 | A1/A2 | Limitare la presenza alle viste autenticate e mantenere la risposta attuale per email già iscritta. | Nessuna vetrina pubblica; D-005 resta valida, risposta neutra precedentemente proposta scartata. |
| D-077 | A3 | Rendere persistente e non bloccante il completamento dei campi obbligatori, accettando una dichiarazione di assenza per Telegram/LinkedIn. | «Non possiedo» o equivalente è una risposta, non un campo mancante; non bloccare pagamenti o iscrizioni legacy. |
| D-078 | A4 | Raccogliere la città da elenco e derivarne il contesto geografico per la mappa regionale. | Elenco, provenienza estera e significato operativo della città restano da definire. |
| D-079 | A5 | Usare una soglia minima di cinque persone per gli aggregati pubblicabili della mappa. | La soglia è decisa; insieme, soppressione e protezione dalle inferenze restano da definire. |
| D-080 | A6 | Derivare la partecipazione precedente quando possibile e usare `@username` Telegram e URL profilo LinkedIn, salvo dichiarazione di assenza. | Storico mancante non significa «non ha partecipato»; fallback ancora da decidere. |
| D-081 | A7 | Accompagnare la richiesta autenticata di riaccettazione privacy con un'email di richiesta. | Pagamenti e diritti già validi non vengono annullati; invio transazionale distinto da D4. |
| D-082 | A9 | Associare corpi IT/EN equivalenti alla stessa versione legale e conservare la lingua dell'accettazione. | Cambio lingua non crea una nuova versione; testi effettivi ancora da validare. |
| D-083 | B1 | Confermare il posto sulla quota base più giorni scelti, senza pranzi, cene o attività. | Gli extra mantengono il saldo separato; la sola base per i benefit è una soglia diversa, D-089. |
| D-084 | B2 | Applicare la transizione legacy con anteprima e sole iscrizioni attive ammissibili, preservando incassi e crediti. | Nessuna riattivazione indiscriminata di scadute o chiuse. |
| D-085 | B3/B4 | Coprire il primo pasto selezionato con incasso organizzazione e limitare le altre voci comprese ai benefit. | Provider fuori dal conto e solo promemoria per l'utente; nessuna attività/servizio generico compreso aggiuntivo. |
| D-086 | B5/B6 | Adottare le etichette proposte e richiedere revisione esplicita dell'importo se cambia il saldo della modale. | Sovraversamento come credito, nessun ritentativo automatico; restano due modalità di destinatario. |
| D-087 | C1 / precisazione incasso | Trattare il non pagante iscritto come esente da quota e/o singole voci e gli incassi degli esterni come incassi separati dell'organizzazione. | Supera l'esclusione indistinta dall'economia in D-063: esterni fuori dalle quote degli iscritti, ma incassi presenti nel totale evento. |
| D-088 | C2 | Inserire gli esterni con identità minima solo admin, senza account/coworking, contando le adesioni nelle capienze di pasti e attività. | Nessuna iscrizione ordinaria o presenza coworking fittizia. |
| D-089 | C3 | Attribuire i benefit a chi ha pagato la quota base oppure agli interni non paganti e consentire cambi categoria con eventuale rimborso. | Distinta dalla soglia base+giorni; rimborso amministrativo tracciato, nessun versamento automatico. Quantità/consegne pregresse da dettagliare. |
| D-090 | C4 | Consentire più attività da un contributo che resta modificabile, senza propagare automaticamente modifiche alle attività. | Supera la proposta di una sola conversione; restano riferimento fonte e protezione dal doppio salvataggio. |
| D-091 | C5 | Richiedere due testi IT/EN per i contenuti visibili delle attività e includere le note interne nei CSV admin. | Dati legacy conservati; note mai nei payload/export partecipante. |
| D-092 | D1 | Applicare i dettagli proposti anche a totali/fasce, con persone e link oppure righe di adesione con titolo attività. | Nessun nuovo calendario necessario. |
| D-093 | D2 | Aggiornare l'ordine utile al ritorno/ricaricamento, senza salti durante l'interazione e con ordine cronologico fuori evento. | Data del rilascio senza demo e ordine CSV ancora da fissare. |
| D-094 | D3 / ultima indicazione | Accantonare la vista calendario mockuppata e ritirare i relativi artefatti dal dossier. | Supera D-069; D1/D2 restano, D4 e integrazione già rinviati non vengono avviati. |
| D-095 | E1 | Mostrare la proposta anonima senza consenso al nome, sempre soltanto agli autenticati. | Scartata l'esclusione dell'intero contributo; contenuti liberi identificanti e aggiornamento dopo revoca da dettagliare. |
| D-096 | E2 | Limitare il catalogo partecipante ai contributi di prenotazioni attive. | Storico delle non attive soltanto admin, nei limiti della conservazione. |
| D-097 | F1 | Usare lo stesso database con una sola edizione aperta alla volta e precedenti in sola lettura. | Opzione A scelta; archivi offline o deploy per anno non sono la direzione corrente. |
| D-098 | F2 | Riusare gli account con nuova iscrizione e nuovi consensi per edizione. | Campi da riproporre/precompilare non ancora scelti, non inferiti dal «sì». |
| D-099 | F3 | Riservare l'archivio agli admin attuali e precedenti. | Ambito delle edizioni leggibili dagli ex admin da dettagliare; nessuna scrittura attuale implicita né consultazione ordinaria partecipante. |
| D-100 | F4 | Chiudere l'edizione tramite il comando CHIUDI EDIZIONE nelle Impostazioni. | Nessuna chiusura automatica alla data finale; rettifiche/riapertura dopo chiusura da definire. |
| D-101 | F5 | Esplicitare i termini normativi applicabili senza estendere il decennio contabile a tutti i dati personali. | Dieci anni art. 2220 c.c. se applicabile; GDPR con durata/criteri per finalità. Le ipotesi 30/90 giorni e 12 mesi non sono default approvati; [fonti](../specs/revisione-2026-11-07/conservazione-normativa.md). |
| D-102 | F6 | Copiare selettivamente impostazioni come bozza, senza iscrizioni, movimenti, consegne, risposte annuali o consensi. | Riprendere l'elenco F3; confermati riuso degli asset nei diritti esistenti e nessuna modifica al logo in bundle. |
| D-103 | F7 | Puntare al supporto operativo delle edizioni prima del prossimo evento, se fattibile. | Data evento e spec esecutiva ancora necessarie; non promettere un rilascio né avviarlo con la sola valutazione. |
| D-104 | A8 | Mantenere consensi facoltativi e revocabili separatamente senza promettere rimozione automatica di media da terzi. | Testi e destinazioni foto/video effettivi ancora da fornire; nessuna integrazione media autorizzata. |

Il [registro aggiornato](../specs/revisione-2026-11-07/domande-aperte.md) distingue risposte chiuse da dettagli residui, senza riproporre come aperte le decisioni sopra. Il piano divide l'MVP 25 in presenze esterne, incassi separati ed esenzioni/rettifiche per mantenere rilasci piccoli.

## D-105 · Attivazione della conferma su quota con ricalcolo esplicito

- **Data**: 2026-11-07.
- **Decisione del maintainer**: per il passaggio dell'MVP 18 scegliere «Ricalcolo con anteprima», usando impostazioni correnti per quota e totale delle sole attive; applicazione esplicita admin, pagamenti invariati e nessuna riattivazione indiscriminata.
- **Motivo**: il modello attuale non conserva i prezzi storici per ogni voce. Il saldo/credito risultante può variare con il dovuto: le differenze sono esposte nell'anteprima, non cancellate o presentate come nuovi versamenti.
- **Alternativa scartata per questo passaggio**: mantenere esattamente il dovuto salvato senza ricalcolo del totale. Restano confermate la stabilità delle già confermate e la separazione dei costi provider.

## Proposte esecutive delle spec 17 e 18 · da rivedere

**Data comune:** 2026-11-07. Il maintainer ha chiesto di preparare entrambe le spec, non di implementarle. Le voci seguenti registrano le scelte tecniche non banali rese concrete per la revisione: non sono un'autorizzazione di implementazione né modifiche già operative a `domain.md`.

| ID | Proposta | Motivo / alternativa scartata nella proposta |
|---|---|---|
| D-106 | Nel 17 registrare eventi facoltativi per persona/edizione/finalità senza FK al booking, con stato calcolato dall'ultimo evento e gestione autenticata degli account noti. | Evitare perdita alla rimozione del booking, duplicati per lista e booleani globali; prove privacy/scarico/salute restano nei riferimenti attuali fino ai rispettivi MVP. [Design 17](../specs/mvp-17-consensi-riservatezza/design.md). |
| D-107 | Nel 18 salvare quota e totale nello stesso ricalcolo e usare una politica di edizione attivata con preview verificata/idempotente. | Evitare quota ricavata dai prezzi nuovi accanto a totale vecchio o attivazione implicita da migrazione; mantenere D-017 sui prezzi ai ricalcoli successivi. [Design 18](../specs/mvp-18-conferma-quota/design.md). |
| D-108 | Nel 18 reclamare una sola notifica per ciclo effettivo di conferma, riusando timer/job e trasferendo le differite valide al passaggio. | Le nuove conferme senza pagamento non possono creare un Payment fittizio; evitare duplicati tra attivazione, timer e job senza altra infrastruttura. [Design 18](../specs/mvp-18-conferma-quota/design.md#conferme-email-e-concorrenza). |
| D-109 | Nel 17 conservare il corpo legale legacy e aggiungere corpi IT/EN espliciti per le nuove pubblicazioni, senza traduzioni o lingue retroattive inventate. | Nuova versione bilingue unica con compatibilità dei riferimenti accettati; testo originale ancora leggibile. [Design 17](../specs/mvp-17-consensi-riservatezza/design.md#modello-dati--migrazione-proposta-0016). |

Materiale aperto per il 17: informative effettive IT/EN e destinazioni dei media da validare prima della produzione. I dettagli di soglia zero, residuo e prezzi del 18 sono proposti nel design per revisione, senza riaprire la formula o D-105 già decise.

## D-110 · Override temporaneo di minimatch per GHSA-g3hv-75wg-m249

- **Data**: 2026-11-07.
- **Decisione**: `frontend/package.json` forza `minimatch` alla versione corretta `11.0.1` tramite `overrides`; il lockfile è rigenerato con npm. Rimuovere l'override quando ESLint, `@eslint/config-array` e `@typescript-eslint/typescript-estree` consentiranno una versione corretta nelle proprie dipendenze.
- **Motivo**: CVE-2026-118764 consente amplificazione di pattern e consumo eccessivo di CPU/memoria; le versioni da 7 a prima di 11.0.1 sono vulnerabili. Anche le ultime release dei tre pacchetti richiedono ancora la serie 10, quindi il normale aggiornamento automatico non basta. La dipendenza è solo di sviluppo: il container finale copia gli asset statici, senza Node o ESLint.
- **Compatibilità**: la serie 11 rimuove alcune API, ma i tre consumatori installati usano `Minimatch`, `match` e `minimatch`, ancora disponibili. Verificati con Node 22 installazione pulita, lint sugli stessi 103 file con diagnostica identica, suite frontend e build.
- **Alternative scartate**: ignorare l'avviso o disabilitare l'audit (la dipendenza resta vulnerabile); modificare solo il lockfile (l'installazione successiva potrebbe reintrodurre la serie 10); aggiornare indiscriminatamente le altre dipendenze (non necessario).

## D-111 · Profilo riutilizzabile e risposte annuali (MVP 19)

- **Data**: 2026-11-08.
- **Decisione**: tenere telefono/Telegram/LinkedIn sul partecipante e città/professione/azienda/aspettative/partecipazione in una riga per partecipante-edizione. Cataloghi geografici locali, con validazione comune-provincia-codice ISTAT.
- **Motivo**: riusare i contatti dopo login senza attribuire al nuovo anno risposte annuali precedenti; non inviare query geografiche a terzi.
- **Partecipazione precedente**: una prenotazione confermata nell'edizione cronologicamente precedente è prova positiva; altrimenti si conserva la dichiarazione esplicita.
- **Sicurezza**: gli invii anonimi per email già nota non scrivono i dati del profilo. Solo il partecipante autenticato o un admin può completare/correggere.
- **Spec**: [MVP 19](../specs/mvp-19-profilo-completo/design.md); l'aggiornamento delle regole prodotto è in `domain.md`.

La decisione sull'override è arrivata su `main` dopo la registrazione D-050–D-109; l'identificativo è stato aggiornato qui per non duplicare i numeri.
