# F · Nuova edizione e storico · Valutazione

**Documento di valutazione, non spec di implementazione.** Aggiornato con le risposte del maintainer: scelta dello stesso DB, una sola edizione aperta, riuso account, archivio per admin attuali/precedenti e chiusura esplicita confermati. Le opzioni restano come confronto delle alternative scartate per ora; nessun reset, export reale, clonazione, risorsa o migrazione autorizzato da questa valutazione. Dettagli residui nel [registro](domande-aperte.md).

## F1 · Quanto il modello è già legato all'edizione

Il modello non è un database privo di edizioni: `Edition` esiste. Il limite attuale è soprattutto operativo: `get_active_edition` sceglie l'attiva con id più alto e `save_edition` modifica quella, senza un ciclo di creazione/chiusura/consultazione storica. Non esiste una garanzia applicativa completa di isolamento tra edizioni né una modalità di archivio immutabile.

| Area | Legame attuale e limiti |
|---|---|
| Date, orari, capienze, quote, prezzi | Colonne su `Edition`; `Slot` e `MealSetting` hanno `edition_id`. Dati già separabili, ma editor sincronizza gli slot e protegge solo alcuni casi d'uso in presenza di prenotazioni/liste. Cambiare le date dell'edizione corrente non equivale ad aprirne una nuova. |
| Canali di pagamento | `PaymentChannel.edition_id`, univocità edizione+codice. I movimenti salvano il codice canale e dipendono dalla prenotazione; descrizioni e istruzioni storiche vanno conservate nell'edizione chiusa. |
| Attività e adesioni | `Activity.edition_id`; `BookingActivity` collega booking e attività. Serve validare la stessa edizione nelle associazioni, non solo nelle pagine che selezionano l'attiva. |
| Iscrizioni e pasti | `Booking.edition_id`; `BookingSlot` e `BookingMeal` ereditano il contesto dal booking. Esistono più prenotazioni successive per la stessa persona; non trattarle come un unico record storico. |
| Pagamenti, annulli, rimborsi | `Payment.booking_id`; rimborso sul booking, autore come account globale. Gli incassi non vanno ricopiati né riallocati alla nuova edizione. |
| Lista d'attesa | `WaitlistEntry` lega persona e slot; l'edizione viene dallo slot. Conserva chiusure e documenti accettati; riferimento al booking promosso non è FK. Nessuna lista va trasferita automaticamente. |
| Privacy e consensi | `LegalDocument.edition_id`, finalità e versione. Booking/waitlist referenziano privacy/scarico; sanitario sul booking. Manca il registro A2/A5 e la sua conservazione quando un booking è cancellato. Il testo legale oggi è un solo corpo, non due versioni linguistiche collegate. |
| Account iscritti | `Participant` globale: email unica, nome, telefono, lingua, password, ruolo, causale; anche invitante, `can_bring` e verifica +1 sono globali pur descrivendo spesso una sola edizione. Le modifiche del nome possono cambiare ciò che si vede nei report passati. |
| Autenticazione | Token e sessioni collegati a `Participant`, senza edizione; riuso account possibile concettualmente, ma non significa iscrizione o consenso nuovo. Ruoli admin globali: permessi di archivio da decidere. |
| Proposte | `Contribution.booking_id`: eredita edizione, viene eliminato con booking rimosso. La conversione C4 dovrà conservare almeno il legame utile senza dipendere dalla sopravvivenza del testo personale. |
| Benefit | Nessun modello attuale. Catalogo e consegne C5 devono nascere riferiti all'edizione. |
| Testi e immagini | Introduzioni IT/EN e logo sull'edizione; `EmailTemplate.edition_id` + tipo + lingua, `RegistrationCard.edition_id`. Contenuti e copyright non si copiano senza verifica dell'uso. |
| Report e viste | `services/views.py` legge principalmente l'edizione attiva; report a lettura senza snapshot. La scomposizione dei dovuti usa prezzi correnti e scarto, non un libro storico di prezzi per riga. Occorre congelare le condizioni di una chiusura oppure dichiarare la data/versione del report. |
| Audit | `AuditLog` ha autore e `booking_id` facoltativo non FK, nessun `edition_id`/persona stabile; alcune righe restano solo testo con nome/email. Non è sufficiente per uno storico per edizione né per anonimizzazione mirata. |
| Job ed email differite | Promemoria percorre i booking pending; promozioni leggono l'attiva. Non esiste una politica completa che escluda le edizioni chiuse da tutti gli effetti automatici. |

Evidenze: `backend/app/models.py`, `services/edition.py`, `booking_changes.py`, `views.py`, `report_export.py`, `audit.py`, `registration.py`, `jobs/send_reminders.py` e specifiche MVP 7/14/16. Questo è un rilievo sul codice, non un controllo sui dati reali.

## F2 · Opzioni

Stime orientative per un manutentore già pratico del progetto, in giornate persona; includono verifica di isolamento e recuperabilità, escludono le nuove funzioni A–E, pareri sulla conservazione e tempi d'attesa esterni. Non sono un preventivo: dimensione dell'archivio e gestione account possono cambiarle.

| Opzione | Vantaggi | Svantaggi/costi | Rischi e contromisure da valutare |
|---|---|---|---|
| **A. Stesso database, edizioni isolate** | Riusa molte relazioni già presenti, un deploy e account riusabili; storico consultabile con UX unica; report per edizione. | Impegno medio/alto, circa 8–15 giorni più 1–2 di prova chiusura/ripristino; ampliare selezione edizione e controlli in ogni scrittura, job, export. Costi Azure inizialmente simili, crescita storage da misurare. | Fuga tra edizioni, modifica involontaria dello storico e consensi attribuiti all'anno sbagliato. Mitigare con contesto edizione esplicito, archivio in sola lettura, prove di isolamento e procedura di chiusura. |
| **B. Export CSV + snapshot DB, poi reset** | Più vicino al funzionamento mono-edizione; avvio nuovo semplice dopo archivio verificato. | Circa 3–6 giorni per export completo documentato, verifica restore e reset controllato; costo ricorrente di gestione archivi. CSV non basta per relazioni, consensi, immagini o audit; snapshot richiede codice/versione di schema compatibili. | Perdita per export incompleto/reset prematuro, ripristino difficile, ritorno di dati già cancellati. Richiede prova di ripristino prima di qualsiasi reset, accessi limitati e scadenza anche degli snapshot. Storico meno comodo, spesso fuori dall'app. |
| **C. Deploy separato per edizione** | Separazione forte dei dati se anche DB/segreti sono separati; conservazione iniziale dell'app com'era. | Circa 2–4 giorni di preparazione, poi almeno 0,5–1 giorno per edizione e manutenzione continua; moltiplica DB, risorse, aggiornamenti e controlli. Account/credenziali normalmente separati. | Edizioni vecchie diventano app non aggiornate con dati personali. Per un archivio preferire accesso privato/sola lettura, disattivare invii; evitare di lasciare pubblici deploy abbandonati. Always-on e dominio dedicato restano esclusi. |
| **D. Archivio strutturato separato, app attiva singola** | Variante B con archivio consultabile dedicato, meno esposizione del DB operativo. | Circa 6–10 giorni: nuovo formato e lettore/versionamento; duplica logiche di report e verifica completezza. | Formati divergenti e controlli privacy in due luoghi; utile solo se lo storico deve essere molto ridotto e separato. |

## F3 · Direzione confermata dal maintainer

**Confermata A: stesso database, una sola edizione aperta e precedenti in sola lettura.** Il modello ha già molti riferimenti necessari; B rende i controlli dipendenti dal ripristino e C aumenta il carico operativo. Snapshot protetti restano backup, non l'unica interfaccia storica. La scelta architetturale è chiusa; la spec esecutiva di F non è ancora stata richiesta.

Account riusati con nuova iscrizione e nuovi consensi; dettagli dei campi da riproporre ancora aperti. Obiettivo richiesto: supporto delle edizioni **prima del prossimo evento, se fattibile**. La stima di F2 è orientativa: la data del prossimo evento e i dettagli di archivio/conservazione servono per la sequenza concreta; non introdurre una riscrittura implicita dentro i P1.

Flusso prodotto desiderato, da valutare:

1. L'organizzazione preme **CHIUDI EDIZIONE nelle Impostazioni**: è il comando che chiude, non il calendario. Prima si propone un riepilogo dei conti, comprese voci esterne, rimborsi e liste; debiti o rimborsi aperti non vengono cancellati. Si fissa il report e si fermano gli effetti automatici dell'edizione chiusa, incluse richieste privacy A5. Rettifiche/rimborsi tardivi o riapertura restano Q-F4.
2. Un comando «Nuova edizione» prepara una bozza con nuovo nome/date. L'anteprima elenca cosa sarà copiato; l'apertura richiede revisione e nuovi testi/versioni pertinenti, senza riusare accettazioni.
3. **Copie confermate come bozza da rivedere:** struttura degli orari, capienze, durata blocco, quote/prezzi/politica B4, catalogo benefit, canali/istruzioni, introduzioni e template IT/EN; sfondi/logo nel diritto d'uso confermato. Date specifiche di pasti delegati e attività non si spostano automaticamente.
4. **Da non copiare:** iscrizioni, presenze, pagamenti, rimborsi, consegne, liste, proposte, preferenze alimentari, prove di consenso, verifica +1 e risposte annuali. I testi legali possono essere una bozza da rivedere, mai un'accettazione trasferita.
5. **Account:** riuso confermato dello stesso account verificato, con nuova iscrizione per edizione. Il maintainer non ha ancora scelto quali contatti precompilare e quali campi annuali richiedere: suggerimenti dopo login con conferma restano una proposta Q-F2. Nessuna adesione o pubblicazione automatica; password/sessioni non sono un consenso. Precedente partecipazione derivata quando lo storico lo permette, fallback ancora da definire.
6. **Consultazione:** archivio soltanto per **admin attuali e precedenti**, con intestazione dell'edizione chiusa e nessuna scrittura. Il ruolo passato non abilita le modifiche dell'edizione attiva. Resta da decidere se un ex admin legga solo l'edizione amministrata o ogni archivio e come revocarne l'accesso; nessuna schermata storica ordinaria per partecipanti e nessun archivio pubblico.
7. **Report per edizione:** filtro e titolo con edizione/data; importi e condizioni di chiusura coerenti con quote, extra e incassi esterni separati, annulli e rimborsi. Lo storico non usa prezzi, contatti o consensi correnti per ricostruire retroattivamente il passato. Confronto tra anni soltanto aggregato e futuro.

Questi sono comportamenti del ciclo di edizione scelto da consolidare, non endpoint, schema o task esecutivi.

## F4 · Conservazione e privacy

Su richiesta del maintainer, usare termini normativi espliciti dove esistono e non trasformare stime di prodotto in obblighi legali. Il [riscontro normativo con fonti ufficiali](conservazione-normativa.md) distingue **10 anni per scritture contabili soggette all'art. 2220 c.c., se applicabile**, dalle durate da determinare per finalità ai sensi del GDPR. Le vecchie ipotesi 30/90 giorni e revisione a 12 mesi non sono confermate come default e vengono ritirate.

| Dati | In chiaro / cancellazione / anonimizzazione nello storico |
|---|---|
| Contatti e account riusabile | Necessari all'accesso e alla finalità dell'account, con termine o criterio dichiarato nell'informativa; nessuna durata pluriennale numerica imposta in generale. Definire cessazione/inattività e dati riproposti Q-F2/F5. Il riuso non giustifica conservare tutte le risposte annuali. |
| Salute | Solo per la necessità specifica dell'edizione e con condizione idonea; cessata tale necessità, eliminare salvo concreta esigenza documentata. Nessun trasferimento alla nuova edizione o al report durevole. Non chiamare «termine di legge» un margine operativo inventato. |
| Provenienza/città, lavoro, aspettative, proposte, invitante, logistica e consegne | In chiaro finché necessari alle finalità dichiarate; poi eliminare identificativi e testi o anonimizzare statistiche, proteggendo celle sotto 5 e possibili inferenze. Non mantenere la città nello storico pubblico per una mappa soltanto regionale. |
| Pagamenti ordinari/esterni, annulli e rimborsi | Se ricadono nell'obbligo dell'art. 2220, dieci anni dall'ultima registrazione delle scritture pertinenti; applicabilità al soggetto che incassa da verificare. Altri dati si conservano solo per finalità e obblighi effettivi, non automaticamente per dieci anni. Identità minima e note pertinenti, senza profilo completo. |
| Prove di privacy/consensi | Versione e testo immutabili, edizione, esito, lingua e istante; legame personale minimo per provare il trattamento nel periodo giustificato, non «dieci anni per tutto». A2/A5 non si ereditano nella nuova edizione. |
| Audit / accessi degli ex admin | Minimo necessario e accessi autorizzati per lo storico, soggetti alla stessa minimizzazione. L'accesso di admin passati non autorizza conservazione illimitata o contenuti sanitari non più necessari. Anonimizzazione anche nei testi liberi di audit, non solo nella tabella account. |
| Foto/video | Politica e destinatari nei testi effettivi, inclusi media fuori dall'app; nessuna rimozione automatica promessa da servizi terzi. Il consenso prova la scelta ma non determina una durata universale. |
| Report aggregati / copie | Aggregati durevoli solo se non ragionevolmente reidentificanti; pseudonimi reversibili non bastano. Backup/export protetti e con scadenza; il restore riapplica cancellazioni e non riattiva vecchie sessioni/invii. |

CHIUDI EDIZIONE limita le scritture operative, **non sospende cancellazione o anonimizzazione dovute** e non azzera i movimenti. La futura progettazione dovrà consentire interventi di conservazione anche su archivi in sola lettura per gli utenti. Finalità, soggetto che incassa e criteri non numerici ancora mancanti sono Q-F5. Nessuna cancellazione/anonimizzazione eseguita in questa fase.

## F5 · Impatto sulle spec A–E e sugli MVP

Prevedere l'appartenenza all'edizione **nel disegno dei nuovi dati** riduce future migrazioni. Non aggiungere però un `edition_id` ridondante a ogni tabella già determinata dal booking senza controlli di coerenza: il rischio è avere due valori discordanti. Riferimento diretto per dati senza booking, contesto derivato e validato per quelli già collegati.

| Spec / rilasci proposti | Accorgimento da considerare ora, senza implementare F |
|---|---|
| A1/A2, MVP 17 | Prove consensi persona+edizione, non booleani globali. Coprire sola lista e cancellazione. Questa scelta locale è necessaria prima del P1; non serve il selettore multi-edizione. |
| B1/B2, MVP 18 | Soglia e politica riferite alla prenotazione/edizione; non usare un'impostazione globale. Decidere se congelare il valore prima di una chiusura, evitando una nuova migrazione contabile arbitraria. |
| A4/A5/A6, MVP 19–21 | Risposte annuali per edizione; prove versionate e riferimenti stabili dello storico anche senza booking. Decisione account/precedente partecipazione prima di questi schemi. |
| B3, MVP 22 | Pagamenti già collegati al booking; validare l'edizione, nessuna nuova colonna globale. |
| B4/B5, MVP 23 | Politica pasti/benefit per edizione; catalogo minimo benefit nel 23, condizioni storiche preservabili. |
| C1/C3, MVP 24 | Note sulla Activity già riferita all'edizione; non serve una seconda associazione. |
| C2, MVP 25a/25b/25c | Esterni senza account e incassi separati legati all'edizione, esenzioni degli iscritti sulle sole voci pertinenti. |
| D1, MVP 26; E3, MVP 27 | Filtri per edizione/stato attivo e nome condizionato al consenso; proposta anonima altrimenti, contesto dal booking. |
| E1/E2, MVP 28; D2, MVP 31 | Nessun nuovo dato; contesto date e grandezze coerente con l'edizione mostrata. |
| C4/C5, MVP 29–30 | Fonte e attività nella stessa edizione; benefit/catalogo/consegne con edizione esplicita anche senza booking. |
| A7/D4, future bozze | Aggregati e futuri gruppi/invii per edizione, senza contatti o scelte globali ereditati; D3 calendario accantonato. |

## Domande aperte

Scelta dello stesso DB, riuso account, archivio per admin attuali/precedenti, comando di chiusura e copie selettive sono confermati. Restano campi da riproporre, ambito degli ex admin, rettifiche dopo chiusura, applicabilità contabile/criteri di conservazione e data del prossimo evento: [registro dei dettagli residui](domande-aperte.md#domande-aperte-residue). Nessuna implementazione F o modifica allo schema è avviata da questa valutazione.
