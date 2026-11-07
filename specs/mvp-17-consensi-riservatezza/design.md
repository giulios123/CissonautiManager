# MVP 17 · Design

Proposta esecutiva sul checkout con migrazione corrente `0015`. Nessun file applicativo modificato nella preparazione di questa spec. [Requisiti](requirements.md), [task](tasks.md), [procedure manuali](test-manuali.md).

## Punti di innesto verificati

| Codice attuale | Evoluzione del 17 |
|---|---|
| `models.py:LegalDocument`, `services/edition.py:publish_legal_document` | Stessa entità/versione; due corpi IT/EN per i nuovi testi. |
| `api/public.py:RegistrationIn`, `services/registration.py:register` | Due scelte facoltative, controllo versioni e salvataggio nella transazione della registrazione. |
| `WaitlistEntry`, `services/waitlist.py` | Consenso per persona/edizione, senza duplicazione per lista/promozione. |
| `api/me.py`, `Personal.tsx` | Lettura/scrittura delle sole scelte proprie anche senza booking. |
| `admin_edition.py`, `AdminSettings.tsx` | Pubblicazione bilingue delle finalità usando l'editor esistente. |
| `db.py:get_db`, `services/seats.py:lock_edition` | Le scritture HTTP acquisiscono già il lock edizione: riusarlo per pubblicazione e modifica, con ricontrollo dopo il lock. |

## Flussi

1. Testi pubblicati → modulo con caselle indipendenti → verifica server di documenti/versioni → creazione persona/booking o liste → eventi facoltativi → commit unico → email di iscrizione esistente. Ogni rifiuto annulla l'intera transazione.
2. Account già presente → percorso di iscrizione attuale → nessuna scrittura anonima delle sue scelte → accesso verificato → gestione consensi. La risposta `already_registered` resta esplicita, come richiesto.
3. Login → pagina personale → due schede con testo corrente e stato → salvataggio di una finalità → evento aggiunto → stato restituito. I consensi non richiedono un booking attivo, ma un'associazione reale all'edizione tramite booking/lista/eventi esistenti; un account admin seed senza associazione vede «nessuna scelta per questa edizione», senza creare iscrizioni fittizie.

## Modello dati · migrazione proposta 0016

### Testi

Conservare `legal_document.body` come corpo originale immutabile per la compatibilità e aggiungere `body_it` e `body_en`, nullable **solo per le righe legacy**. Una nuova pubblicazione compila entrambi e mantiene `body = body_it` per i lettori di compatibilità; i lettori aggiornati scelgono dai corpi espliciti. Non copiare il testo originale nella colonna inglese né assegnargli una lingua senza prova.

Le finalità nuove sono `attendance` e `media` (entro i 16 caratteri attuali). Privacy, scarico e sanitario mantengono identificativi/versioni/riferimenti esistenti. L'editor generico richiede IT/EN per ogni nuova pubblicazione delle cinque finalità; il flusso sanitario cambia solo la lettura del testo e non i requisiti o la cancellazione delle allergie.

### Eventi facoltativi

Nuova tabella `consent_event`, senza relazione al booking:

| Campo | Tipo e regola |
|---|---|
| `id` | Chiave primaria progressiva; rompe la parità degli istanti. |
| `edition_id`, `participant_id` | FK obbligatorie; nessuna cascata dalla rimozione di un booking. |
| `kind` | `attendance` o `media` per gli endpoint del 17. |
| `action` | `granted`, `declined`, `withdrawn`. Il caso senza eventi resta `not_expressed`. |
| `document_id` | FK alla versione pertinente; richiesta per sì/no con testo presentato. In revoca riferimento alla precedente concessione, senza imporre il testo corrente. |
| `locale` | `it`/`en`, lingua del testo mostrato o della richiesta di revoca. |
| `recorded_at` | `UtcDateTime`, generato dal server. |
| `source` | `public_registration` oppure `self_service`; nessuna scelta concessa dall'admin. |

Indice `(edition_id, participant_id, kind, id)`; ordinamento dello stato per `id`, evento più recente per finalità. Validare nel servizio che documento, finalità ed edizione coincidano e che la persona sia quella autorizzata; FK separate da sole non garantiscono questa integrità. Nessun IP, user-agent, allergia o dato professionale necessario nel registro.

Non creare eventi per gli iscritti legacy: assenza significa non espresso. Non duplicare ora le prove privacy/scarico/sanitarie nel nuovo registro: i riferimenti esistenti restano autoritativi e la generalizzazione per A5/A6 verrà specificata nei rilasci pertinenti. Il 17 conserva le proprie prove indipendenti dal booking senza anticipare il nuovo storico A6.

### Stato effettivo

Ultimo evento per persona/edizione/finalità → scelta storica; per nuovi usi del testo corrente serve `action=granted` e `document_id` uguale alla versione corrente. Se è stato pubblicato un testo diverso, mostrare «scelta riferita a una versione precedente» e non autorizzare nuovi usi automaticamente. Non aggiungere un evento di revoca fittizio alla pubblicazione. La revoca è sempre consentita senza accettazione preventiva del testo nuovo.

Una scelta ripetuta con stessa azione/documento è un no-op; non cambia l'istante della prova. Per modifiche concorrenti il client invia l'id dell'ultimo evento osservato (`null` se assente); dopo il lock si restituisce 409 se è cambiato e la richiesta non è già soddisfatta identicamente. Una revoca non è respinta per sola versione legale vecchia; il controllo di concorrenza protegge invece da una scelta realmente modificata in un'altra sessione.

## Contratti API proposti

| Metodo e percorso | Contratto / autorizzazione |
|---|---|
| `GET /api/public/edition` | Aggiunge `attendance_consent` e `media_consent` con `{id,version,texts:{it,en}}` quando completi; nessun dato o scelta personale. Privacy/scarico espongono anche i corpi espliciti e l'indicazione legacy. |
| `POST /api/public/registrations` | Mantiene campi esistenti; aggiunge `optional_consents` con scelta e `document_id/version` per ogni finalità effettivamente presentata e `consent_locale`. Campi omessi per client vecchi = non espresso, mai sì. |
| `GET /api/me/consents` | `current_user`; edizione attiva risolta dal server, due stati con ultimo evento, versione accettata e testo corrente/pertinente. Nessun parametro per un'altra persona. `Cache-Control: no-store`. |
| `PUT /api/me/consents/{kind}` | `current_user`; `{granted,document_id,version,locale,expected_event_id}`. Un sì richiede il testo corrente; un no dopo un sì è revoca. Restituisce stato aggiornato; 401 anonimo, 404 finalità/associazione inesistente, 409 conflitto, 422 documento incoerente. |
| `POST /api/admin/legal-documents` | `require_admin`; `{kind,body_it,body_en}` entrambi non vuoti, limite 50.000 caratteri ciascuno. Pubblicazione sotto lock e ricontrollo del massimo numero prima del commit. |
| `GET /api/admin/participants/{id}/consents` | `require_admin`; lettura per persona nell'edizione attiva, valida anche per sola lista; nessuna controparte admin di scrittura. |

`GET /api/admin/edition` include le nuove finalità per l'editor. Le risposte storiche mantengono il corpo originale se manca la traduzione, marcandolo esplicitamente; `body` resta disponibile per i lettori esistenti. La richiesta admin precedente con solo `body` non crea nuovi documenti monolingui: risposta 422 localizzata; backend e frontend sono distribuiti nello stesso container.

Nel POST anonimo controllare il caso account esistente prima di aggiungere eventi. Per persona nuova salvare al massimo una coppia di eventi; per account noto ignorare le scelte facoltative dell'invio senza modificare le prove e indicare nella ricevuta che si gestiscono dopo login. Anche un account scaduto che torna dal modulo resta un account già noto. Non restituire il suo nome archiviato, le scelte, i contatti o la causale personale già memorizzata: per quel caso `personal_code` diventa nullable/omesso nella ricevuta anonima e le istruzioni personali arrivano nell'email esistente. Giorni/importo dell'invio appena creato restano riepilogabili; il frontend gestisce l'assenza della causale con l'indicazione di controllare la propria posta, senza mostrare un codice fittizio. L'esito esplicito per un'iscrizione già attiva resta confermato. Nessuna modifica al meccanismo di autenticazione o ai token.

## UI, errori e guida

`Registration.tsx`: caselle con etichette separate e link al testo, stato non disponibile se incompleto, dati compilati conservati al cambio lingua. Un 409 dovuto ai testi non deve eseguire l'attuale reset globale della selezione slot: distinguere il codice di errore legale dal conflitto di capienza.

`Personal.tsx`: sezione «Consensi / Consents» fuori dal blocco condizionato alla presenza di booking, accessibile a sola lista e legacy. Mostrare non espresso/rifiutato/concesso/revocato/versione precedente con testo, data di Roma e comando per singola finalità. Nessuna casella obbligatoria di profilo A4 aggiunta qui.

`AdminSettings.tsx`: editor per lingua e finalità con pubblicazione unica, versioni precedenti immutabili e assenza di traduzione ben visibile. Scheda persona o dettaglio lista: sola lettura dei consensi via API admin. Non costruire una nuova lista nominale.

Testi in `frontend/src/i18n/{it,en}.ts`, errori backend nel catalogo i18n, guide omonime IT/EN: partecipante `01-signing-up.md`, nuova sezione `10-consents.md`; admin `10-settings.md` e `01-people.md` dove pertinente. [copy.md](copy.md) raccoglie i microtesti; le informative complete sono materiale da validare e caricare, non seed automatici.

## Compatibilità, rollout e verifiche

Migrazione additiva 0015→0016: eventi vuoti e corpi legacy intatti, nessuna modifica a `Booking`, `Payment`, `WaitlistEntry`, salute o capienze. Upgrade da zero e da database popolato, metadata coerenti, prove su SQLite e SQL Server. Downgrade solo in test o prima di raccogliere nuovi consensi; dopo la raccolta un rollback non deve distruggere le prove, quindi privilegiare una correzione in avanti e backup verificato.

L'interfaccia può essere distribuita senza testi facoltativi pronti: non concede né pubblica niente e lascia operativi i flussi esistenti. Prima di dichiarare completato il P1 per la nuova apertura verificare entrambi i testi IT/EN e le procedure manuali. Non attivare E3 o pubblicazione media: il 17 prepara la prova e i controlli che useranno i futuri consumer.

## Modifiche a domain.md

Da applicare all'approvazione/chiusura del 17, senza modificare qui le regole operative:

1. Aggiungere le finalità facoltative attendance/media e il registro per persona/edizione, distinto dai consensi obbligatori e sanitario.
2. Nessun consenso facoltativo predefinito o inferito per legacy; gestione autenticata e prova conservata quando sparisce il booking.
3. Solo viste autenticate, invitante libero, nessuna scrittura anonima delle scelte di account noti; D-005 confermata.
4. Nuovi testi con corpi IT/EN della stessa versione e precedenti immutabili; preservare i corpi legacy senza traduzioni fittizie.

Non includere la riaccettazione generale/email del 20 né la cronologia A6 del 21 in queste modifiche. Non presentare le proposte tecniche di questa spec come già implementate.
