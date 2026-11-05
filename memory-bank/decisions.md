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
