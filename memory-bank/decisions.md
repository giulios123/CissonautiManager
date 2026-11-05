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

