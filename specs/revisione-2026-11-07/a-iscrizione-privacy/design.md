# A · Design proposto

Per A1–A3 e testi bilingui del primo rilascio vedere il [design esecutivo 17](../../mvp-17-consensi-riservatezza/design.md); gli altri contenuti sotto sono il quadro dei successivi MVP. Nessuna implementazione in questa fase.

## Flussi

Modulo pubblico → caselle distinte → validazione della versione corrente → iscrizione o sola lista d'attesa → ricevuta limitata all'invio → accesso autenticato. Il ritorno di un account esistente non autorizza il modulo anonimo a modificarne il profilo o i consensi preesistenti: completamento e revisione passano dalla sessione verificata.

Primo accesso legacy → riepilogo sempre disponibile → richiesta persistente non bloccante → salvataggio autenticato dei soli campi del proprio profilo. Pubblicazione privacy → richiesta email e rilevazione di versione pendente alla lettura autenticata → nuova scelta esplicita → nuova prova; nessuna operazione cambia il libro pagamenti. Per email già iscritta resta la risposta attuale, senza introdurre la neutralizzazione precedentemente proposta.

## Modello e migrazioni future

Riutilizzare `LegalDocument`, la sua numerazione per edizione/finalità e gli identificativi già presenti su booking e waitlist. Nuove finalità presenza e foto/video non sono nuove versioni della privacy generale. Il modello attuale limita `kind` a 16 caratteri: i futuri identificatori devono rispettare questo limite oppure una migrazione lo deve ampliare esplicitamente.

Direzione: prove append-only per persona/edizione/finalità/documento con scelta e timestamp; assenza significa non espresso, non un booleano globale. Il 17 introduce gli eventi facoltativi **senza inventare o importare consensi opzionali legacy**. La generalizzazione delle prove obbligatorie e l'eventuale importazione da booking/waitlist con istanti originali riguardano A5/A6 nei successivi rilasci, senza duplicarle per slot. Le revoche aggiungono eventi; documento/persona/edizione devono essere coerenti. Copertura della sola lista e conservazione delle nuove prove indipendenti dal booking fin dal 17.

Campi A4: nullable per migrare dati preesistenti; risposta obbligatoria nei nuovi invii e nel completamento. Telefono già esistente da riusare. Città con identificativo geografico, paese e regione derivabile. Per l'Italia si propone l'[elenco ufficiale dei comuni ISTAT](https://www.istat.it/classificazione/codici-dei-comuni-delle-province-e-delle-regioni/), in copia locale versionata: selezione/autocompletamento senza inviare ciò che digita la persona a un servizio geografico terzo. Casi esteri, città non presenti e significato della provenienza restano Q-A4. Conservare la dichiarazione di assenza di Telegram/LinkedIn come risposta distinta dal mancante, senza usarla come URL o contatto. Derivare la partecipazione precedente quando esiste uno storico attendibile.

F ha ora una direzione confermata: stesso database e account riusati, iscrizioni annuali. Proposta di profilo dell'edizione per provenienza, aspettative e lavoro; il maintainer non ha ancora scelto quali contatti precompilare. Nessun consenso o risposta annuale viene trasferito automaticamente. Non avviare il supporto operativo delle edizioni nella sola revisione documentale.

A6: non assumere che l'attuale `AuditLog` sia sufficiente. Occorrono un riferimento stabile persona/edizione anche dopo rimozione del booking e una lettura admin raggiungibile dall'elenco persone/storico. Distinguere azione autonoma da azione admin; non attribuire la prima a un amministratore fittizio. L'esatta conservazione di prove e collegamenti è proposta da approvare con F, senza copiare allergie, note o profilo completo nel log. Non ripristinare dati già cancellati che non esistono più.

## API e pagine interessate

- `GET /api/public/edition` e `POST /api/public/registrations`: testi/versioni/scelte A1–A2 e campi A4; nessuna nuova lettura nominale anonima. Risposta a email note invariata come oggi, su conferma Q-A2.
- `GET /api/me` e future operazioni autenticate di aggiornamento profilo/consensi: dati propri, campi mancanti, versioni pendenti e prove; path definitivo nella spec esecutiva dell'MVP.
- Impostazioni admin: estendere l'editor legale esistente per le finalità; non consentire un consenso a nome della persona. Una versione contiene due corpi IT/EN equivalenti; la prova conserva anche la lingua. Il corpo unico attuale richiede evoluzione conservativa, non duplicazione delle versioni per semplice traduzione. Testi concreti ancora da validare.
- Storico admin: accesso protetto anche per righe scollegate dalla prenotazione; A6 solo verifica manuale.

## Impatto e Modifiche a domain.md

Variazioni di prodotto confermate, non ancora applicate al codice/dominio operativo: due finalità facoltative soltanto in viste autenticate; campi A4 con città e gestione legacy; riaccettazione anche via email e testi IT/EN della stessa versione; traccia amministrativa della disdetta autonoma. D-018 perde la conseguenza «si perde la traccia»; D-022 non può più limitarsi alle sole azioni admin. A3 mantiene invitante libero e verifica +1; D-005 resta invariata su conferma del maintainer. A7 resta una bozza con soglia minima 5, non una pubblicazione autorizzata dalla sola soglia.

La richiesta email A5 è transazionale e riferita alla versione privacy, distinta dalle future campagne D4. Proposta: registrare l'esito/tentativo per evitare duplicati, ricontrollare versione corrente e accettazione prima di inviare, escludere edizioni chiuse e non inviare dati sensibili nel messaggio; niente accettazione automatica tramite link. L'esecuzione tecnica e i ritentativi saranno definiti nell'MVP 20.

Regressioni da verificare nei futuri MVP: registrazione, sola lista, promozione, modifica dati admin, consensi sanitari, cambio lingua, annullo pagamento e account con booking scaduti. A6 non aggiunge test automatici in questo piano.
