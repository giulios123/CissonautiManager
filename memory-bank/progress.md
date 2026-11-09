# Progress

## Chiusura MVP 20 · T20-8

Il maintainer ha confermato l'8 novembre 2026 il completamento delle verifiche SQL Server e del collaudo degli organizzatori. Nella sessione corrente la suite backend completa ha superato 1103 test (3 warning di deprecazione). T20-8 è chiusa; la chiusura non dichiara eseguiti deploy o invii email reali.

## MVP 21 e 22 · PR #24 unita a main

Implementati sul branch `feat/mvp-21-storico-cancellazioni` e uniti a `main` con PR #24 il 2026-11-08. Registro admin delle nuove disdette con conservazione annuale e pulizia oraria; modale d'incasso rapido con snapshot, retry idempotente, annullo ed email differita; guide IT/EN e migrazioni `0020`/`0021`. La PR riporta suite locale, CI, SQL Server e collaudi manuali completati. Nessun deploy dichiarato.

## MVP 23 e 24 · Implementati su branch separati

- **MVP 23**, branch `feat/mvp-23-composizione-quota`, commit `433bc89`: policy disattivata dalla migrazione, primo pasto idoneo coperto e riassegnato con il ricalcolo, preview/apply admin con fingerprint e retry idempotente, catalogo benefit minimale, interfacce e guida IT/EN. Task T23-1–8 implementati. Backend 1115 test, frontend 410 test, Ruff, formattazione, lint, typecheck, build, controllo Guide e migrazione SQLite passati. Restano la prova SQL Server e il collaudo manuale organizzatori (`specs/mvp-23-composizione-quota/test-manuali.md`).
- **MVP 24**, branch separato `feat/mvp-24-dettagli-attivita`, commit `ce64510`: testi IT/EN con fallback legacy, schede attività e note admin con cronologia e CSV admin. Task T24-1–8 implementati. Backend 1114 test, frontend 410 test e gli stessi controlli statici/build e migrazione SQLite passati. Restano la prova SQL Server e il collaudo manuale (`specs/mvp-24-dettagli-attivita/test-manuali.md`).

Le spec B1 restano separate; il 24 è rilasciabile indipendentemente dal 23. Le modifiche proposte a `domain.md` non sono state applicate. Nessun deploy eseguito. La pubblicazione del 23 e l’attivazione della policy per un’edizione sono passaggi distinti.

## MVP 20 · Nuova accettazione privacy — implementato sul branch

La migrazione `0019` trasforma gli snapshot legali legacy in prove versionate con lingua sconosciuta e crea il vincolo per il singolo tentativo email, dopo la migrazione `0018` del profilo partecipante già presente in `main`. Accettazione autenticata e storico sono disponibili per partecipanti e organizzatori; le scritture limitate vengono protette anche lato API. Nuovi account accettano durante la registrazione; gli account noti restano in sospeso finché non confermano dopo il login. Il job orario invia una richiesta IT/EN per versione e non la ripete.

Verificati 30 test backend mirati (privacy, migrazioni SQLite con upgrade/downgrade, registrazione e consensi), 401 test frontend completi e 3 test mirati sulla versione finale del pannello; Ruff, formattazione, ESLint/Prettier, TypeScript, build e controllo guide IT/EN passati. ESLint segnala il warning preesistente in `ConfirmDialog.tsx`; Vite segnala il bundle principale sopra 500 kB. La suite backend completa è stata interrotta al 19% dopo circa dieci minuti per la lentezza del runner nel sandbox. SQL Server non è configurato nella sessione e il socket Docker non è accessibile; la checklist manuale per gli organizzatori è in [`pr-description.md`](../specs/mvp-20-riaccettazione-privacy/pr-description.md). Nessun deploy, email reale o pubblicazione dei testi legali definitivi eseguiti.

## MVP 19 · Profilo completo e iscritti precedenti — presente in main

Branch `feat/mvp-19-profilo-completo`; implementati i requisiti in `specs/mvp-19-profilo-completo/`. Migrazione 0018 aggiuntiva; profili annuali separati dai contatti; ricerca locale di 7.893 comuni italiani e 249 paesi; iscrizione e sola lista richiedono il profilo; account esistenti non si aggiornano anonimamente; API di completamento autenticato e correzione admin con audit; guide IT/EN aggiornate.

Verifica: 1091 test backend completi passati prima degli ultimi cambi specifici; poi 71 test backend mirati, inclusa migrazione e derivazione dello storico, e altri 16 test profilo/migrazione dopo la normalizzazione finale del catalogo. 399 test frontend completi passati; 72 test mirati di registrazione/profilo/inglese ripetuti dopo gli ultimi cambi. Ruff, TypeScript, ESLint/Prettier, build e controllo guide passati. Rimane un warning ESLint preesistente in `ConfirmDialog.tsx`, l'avviso Vite per bundle oltre 500 kB e un warning deprecazione `httpx` nei test.

Da collaudare manualmente: elenco `specs/mvp-19-profilo-completo/test-manuali.md` (telefono, desktop, tastiera, iframe, omonimie e profili esteri/non censiti). La migrazione SQLite è coperta; SQL Server va verificato nella CI. Nessun deploy o invio reale eseguito. Descrizione per la revisione: [`pr-description.md`](../specs/mvp-19-profilo-completo/pr-description.md).

## MVP 18 · Conferma con la sola quota — implementato sul branch

Branch `feat/mvp-18-conferma-quota`; task T18-1–10 completati. L'edizione resta sulla regola legacy finché un admin non applica una nuova anteprima; con la nuova regola la prenotazione si conferma alla copertura della quota base+giorni, mantenendo separati saldo totale, extra e costi del fornitore. L'attivazione include anteprima/applicazione atomiche, cicli email, UI admin, guide e testi IT/EN.

Validazione: suite completa backend 1083 test, suite frontend 394 test; TypeScript, lint, build, Ruff e formattazione passati. Il maintainer ha confermato superate tutte le prove SQL. I test automatizzati usano dati sintetici; le procedure manuali in `specs/mvp-18-conferma-quota/test-manuali.md` e quelle visive del 17 restano aperte. Nessun deploy, email reale o attivazione sui dati dell'edizione esistente è stato eseguito. Descrizione per la revisione: [`specs/mvp-18-conferma-quota/pr-description.md`](../specs/mvp-18-conferma-quota/pr-description.md).

## MVP 17 · Consensi facoltativi — implementato, collaudo aperto

Branch `feat/mvp-17-consensi-riservatezza`. T17-1–6 implementati: schema, regole, pubblicazione IT/EN, registrazione/lista atomica, gestione autenticata e lettura admin. Gli account esistenti non modificano le scelte anonimamente e il codice personale non appare nella risposta. Test mirati T17-3: 104 backend/25 frontend; T17-4: 62 backend/21 frontend; T17-5: 50 backend; T17-6: 2 test dedicati e 19 frontend. Il maintainer conferma superate tutte le prove SQL. Restano CI della PR e prove manuali telefono/desktop/iframe; informative definitive IT/EN da validare prima della produzione. Descrizione PR in `specs/mvp-17-consensi-riservatezza/pr-description.md`.

## Revisione documentale del 7 novembre 2026

Spec A–E, procedure manuali (A6 esclusivamente manuale), piano rilasci, valutazione F e [registro risposte/residui](../specs/revisione-2026-11-07/domande-aperte.md) aggiornati con le risposte del maintainer e gli incassi esterni separati. Decisioni iniziali D-050–D-075 e precisazioni prevalenti D-076–D-104 in `decisions.md`. **Nessun nuovo MVP implementato.** Calendario D3 accantonato e mockup/anteprima rimossi; mappa A7 documentale aggiornata. F resta valutazione, con scelta dello stesso DB e account riusati confermata. Aggiunto [riscontro normativo conservazione](../specs/revisione-2026-11-07/conservazione-normativa.md), distinguendo termini condizionati e criteri GDPR; nessuna cancellazione di dati.

Controlli della revisione limitati a coerenza, collegamenti, struttura e artefatti documentali. D5 verificato staticamente nel repository, esecuzione/recapito in produzione ancora non verificati. Suite applicative non eseguite per modifiche soltanto documentali; non dichiarare completati i test futuri descritti nelle spec.

## Spec esecutive 17 e 18 · 7 novembre 2026

Preparate su richiesta esplicita entrambe le spec B1: [17](../specs/mvp-17-consensi-riservatezza/requirements.md), 8 task e microtesti IT/EN; [18](../specs/mvp-18-conferma-quota/requirements.md), 10 task e transizione con anteprima confermata in D-105. Design, migrazioni proposte, API, percorsi interessati e procedure manuali sono documentati. **Nessun task applicativo eseguito e nessun test funzionale dichiarato passato.** Verifiche di questa fase: coerenza documentale, link/ancore, limiti dei task e perimetro senza modifiche applicative; suite/lint applicativi da eseguire durante lo sviluppo.

## Piano operativo 17–18 · 7 novembre 2026

Preparato il [piano comune](../specs/piano-mvp-17-18.md) con sequenza, dipendenze, risultati per fase, verifiche e passaggio di produzione separato. Collegati gli 8 task del 17 e i 10 del 18 senza nuove checklist applicative; nessuno spuntato o eseguito. Le informative definitive IT/EN rimangono necessarie per la raccolta in produzione, non per il collaudo con fixture. Controlli di questa sessione limitati a documenti, copertura/ordine dei task e collegamenti; nessuna suite applicativa o migrazione eseguita.

## Stato degli MVP

| MVP | Nome | Stato |
|-----|------|-------|
| 0 | Bootstrap (Memory Bank, AGENTS.md, roadmap, spec MVP 1) | fatto |
| 1 | Iscrizione base | fatto salvo il task 15 (verifica in Google Sites e chiusura), aperto e non bloccante |
| 2 | Pagina personale | fatto e deployato su Azure (task 1-10); restano le prove manuali in produzione: email vera e job orario |
| 3 | Pannello admin completo | fatto e deployato su Azure (task 1-13); restano le prove manuali in produzione con dati veri |
| 4 | Lista d'attesa | codice fatto e provato in locale (task 1-9), in PR verso `main` |
| 5 | Pranzi e cene | codice fatto e provato in locale (task 1-10), in PR verso `main` |
| 6 | Attività e contributi | codice fatto e provato in locale (task 1-10), in PR verso `main` |
| 7 | Inviti e report | fatto e provato in locale (task 1-9) |
| 8 | Stile del sito | fatto e provato in locale (task 1-7) |
| 9 | Guida in app e note di rilascio | fatto e provato in locale (task 1-10) |
| 10 | Incassi (Da incassare) | fatto e provato in locale (task 1-10) |
| 11 | Lingue e indirizzi | fatto e provato in locale (task 1-8) |
| 12 | Pannello admin in inglese | fatto e provato in locale (task 1-5) |
| 13 | Email di iscrizione personalizzabile | fatto e provato in locale (task 1-8) |
| 14 | Testi dell'evento e accesso diretto | fatto e provato in locale (task 1-9) |
| 15 | Logo dell'edizione e accesso dalla registrazione (PR #15); riepiloghi compatti delle presenze (PR #16) | Logo: CI verde, restano prove manuali. Riepiloghi: test e verifiche locali passati, restano verifiche reali post-deploy |
| 16 | Orari, telefono e pagamenti diretti | implementato sul branch `feat/mvp-16-pagamenti-diretti`; tutte le prove SQL confermate superate dal maintainer il 2026-11-07, resta la prova visiva |
| 17 | Consensi separati e riservatezza | T17-1–6 implementati; T17-7/8 e prove manuali ancora aperti; testi legali definitivi da validare prima della produzione |
| 18 | Conferma con la sola quota | T18-1–10 implementati su `feat/mvp-18-conferma-quota`; backend 1083, frontend 394 e controlli statici/build verdi; prove SQL confermate dal maintainer; restano collaudi manuali, nessun deploy/attivazione reale |

## Verifiche manuali

- **Bootstrap**: struttura del repo conforme alla Parte A; nessun codice applicativo. Nessuna verifica manuale funzionale prevista.

- **MVP 1a**, provato end to end in locale con browser (DB nuovo da migrazioni): login admin con password, creazione edizione e testi legali, iscrizione da telefono (10 € + 2 giorni = 12 €), magic link dall'email in console, pagina personale, registrazione pagamento con conferma, cookie httpOnly/Lax di 14 giorni, header CSP.
- **Slot serale (task 13)**: provato in browser su DB nuovo da migrazioni 0001 e 0002; la sera si prenota senza limite di posti e la sola sera costa 11 €.
- **CI su SQL Server**: ha trovato 4 problemi che SQLite nascondeva (D-011), tutti corretti. Immagine Docker: costruita dalla CI.
- **Deploy Azure (task 14)**: chiuso con successo dal maintainer, l'app parte su Container Apps e il login funziona.
- **Non verificato**: embed reale in Google Sites (task 15), email reali (MVP 2).

- **MVP 2**, provato end to end in locale con browser da telefono (DB nuovo da migrazioni, edizione 3-9 novembre con email in console): iscrizione dal modulo pubblico, magic link, cambio slot con anteprima della quota (12 € a 13 €), giorni passati bloccati e oggi modificabile, selezione vuota rifiutata, dialogo di disdetta (focus sul tasto sicuro, Esc lo chiude e riporta il focus), disdetta senza pagamenti con email e prenotazione rimossa. Il job `python -m app.jobs.send_reminders` parte da riga di comando su un database migrato.
- **Non verificato (MVP 2)**: email vere nella casella e fuori dalla posta indesiderata; il job che gira davvero ogni ora con l'app a zero repliche (il deploy lo crea, ma nessuna esecuzione è ancora stata osservata); disdetta con pagamenti provata solo nei test automatici.

- **MVP 3**, provato end to end in locale con browser da telefono (DB nuovo da migrazioni, edizione 3-9 novembre, tre iscritti con pagamenti diversi): voci del pannello; elenco Persone con telefono e sere e CSV scaricato (BOM, `;`, importi con la virgola, fuso di Roma); «Giorni e slot» con la sera dell'intero giorno marcata; «Settimana» con totale delle persone diverse; «Da verificare» con credito e pagamento parziale; aggiunta di un admin nuovo e rimozione con dialogo di conferma (focus sul tasto sicuro); admin attuale non rimovibile con spiegazione; proroga del blocco letta in ora di Roma; modifica dati e di slot (anche un giorno passato) con cronologia; annullamento di un pagamento che riporta la prenotazione in attesa; disdetta a nome della persona e rimborso (parte dall'importo versato); «Da verificare» che si svuota da sola.
- **Non verificato (MVP 3)**: CI su SQL Server (le query nuove sono semplici, ma la CI non è ancora girata sul branch); apertura dei CSV in Excel o Numbers veri (provato solo il contenuto dei file); uso con molti iscritti.
- **Deploy su Azure di MVP 2 e MVP 3 (PR #4, 2026-11-05)**: CI verde su tutti i controlli, compreso SQL Server con le migrazioni da zero. Il primo Deploy è fallito per `MissingSubscriptionRegistration` (provider `Microsoft.Communication` non registrato, `bootstrap.sh` non lo registrava: corretto). Dopo `az provider register --namespace Microsoft.Communication --wait` il rilancio dello stesso run è riuscito: Bicep applicato (servizio email, dominio gestito, servizio di comunicazione, job orario) e `GET /api/health` a 200 (il primo avvio a freddo con le migrazioni 0003 e 0004 ha richiesto circa 4 minuti, con un 503 iniziale). App: `https://cissonauti-booking.wonderfulbush-cbda30f0.italynorth.azurecontainerapps.io`. Task 9 dell'MVP 2 validato.
- **MVP 4**, provato end to end in locale con browser da telefono (DB nuovo da migrazioni 0001-0005, capienza 1 e lista al 100%): Ada prende l'ultimo posto; Bea trova lo slot «completo, spunta per entrare in lista», si iscrive solo in lista (nessuna quota), riceve l'email e vede «1° in lista» nella pagina personale; Ada disdice e Bea riceve «Si è liberato un posto» con quota, causale e scadenza, e la sua pagina mostra la prenotazione in attesa; pannello con «Persone», «Giorni e slot» e percentuale nelle Impostazioni. Downgrade e upgrade della 0005 senza errori.
- **Non verificato (MVP 4)**: CI su SQL Server; promozione dopo una scadenza con il job che gira davvero su Azure; due promozioni concorrenti sullo stesso slot (lock provato solo su SQLite); email vere.
- **MVP 5**, provato end to end in locale con browser da telefono (DB nuovo da migrazioni 0001-0006, prezzi 8 € e 12 €, consenso sanitario pubblicato): il modulo pubblico non chiede i pasti; dalla pagina personale pranzo e cena di lunedì con anteprima (11 € → 31 €); allergie rifiutate senza consenso e salvate con il consenso; togliendo la sera cade la cena con avviso; vista «Pasti» con regimi, allergie e CSV; colonne Pranzi e Cene in «Settimana». Downgrade e upgrade della 0006 senza errori.
- **Non verificato (MVP 5)**: CI su SQL Server; CSV dei pasti aperto in Excel vero; importi definitivi dei pasti.
- **MVP 6**, provato end to end in locale con browser da telefono (DB nuovo da migrazioni 0001-0007): l'admin crea dal pannello un'escursione a 15 € con 2 posti; Ada e Bob aderiscono (quota 12 € → 27 €), per Cid la casella è bloccata con «completo»; Ada toglie lo slot del lunedì mattina e l'attività cade con avviso; Bob propone un tema per l'unconference; dettaglio attività con iscritti e posti, vista «Contributi», CSV di attività e contributi, colonna Attività in «Settimana». Downgrade e upgrade della 0007 senza errori.
- **Non verificato (MVP 6)**: CI su SQL Server (lock sulle attività provato solo sul testo della query); due adesioni contemporanee all'ultimo posto; CSV aperti in Excel vero.
- **B0**: l'MVP 2 non era completo (task 9 aperto) quando sono partiti MVP 3-6; il maintainer ha chiesto di procedere. Il task 9 è stato poi validato con il deploy della PR #4.

- **MVP 8**, provato in locale con Chromium (telefono iPhone 13 e computer a 1280 px, DB nuovo da migrazioni, edizione di prova con due iscritti): iscrizione, accesso, pagina personale, pannello (Persone, Giorni e slot, scheda). Iscrizione dentro un iframe ospitato su un finto `sites.google.com` con la CSP vera: classe `in-frame`, sfondo trasparente, intestazione ridotta senza logo, Montserrat caricato. Nessuno scorrimento orizzontale, controlli alti almeno 44 px, nessun errore in console. Gli script di prova sono rimasti fuori dal repo (servono un backend con dati), contrariamente a quanto previsto dal design.
- **MVP 8, rifinitura** (richiesta del maintainer dopo la prova): «Esci» della pagina personale diventa secondario; gli stati della prenotazione sono etichette colorate (`StatusBadge`), con il testo sempre presente e contrasti AA controllati da `theme.test.ts`. Provato in browser con iscrizioni in attesa, confermate, disdette e rimborsate.
- **MVP 8, audit** (2026-11-05, dopo l'unione con gli MVP 4-6): 15/20 prima, 18/20 dopo; 12 problemi corretti (titoli di pagina, menu admin su telefono, numerazione doppia, tabelle senza nome, anello di focus sui campi data, bordi laterali colorati, aree di tocco, dettagli). Report in `specs/mvp-08-stile-sito/audit.md`. Il rilevatore di Impeccable non è stato eseguito (binario esterno negato dalla sessione): i controlli sono misurati con Playwright.
- **MVP 7**, provato end to end in locale con browser (DB nuovo da migrazioni 0001-0008, edizione con capienza 2, due persone in lista): Luca 1° e Sara 2°; verificato il +1 di Sara da «Giorni e slot» e le posizioni si scambiano subito (anche nella pagina personale di Luca: 2°); la scheda mostra chi ha verificato e quando, la cronologia lo registra; disdetta di un iscritto: Sara riceve l'email del posto liberato e Luca passa 1°. Report: sezioni e numeri coerenti con le altre viste (test di integrazione), nessuno scorrimento laterale da telefono, stampa su 4 pagine A4 senza menu né pulsanti.
- **Non verificato (MVP 7)**: CI su SQL Server con la migrazione 0008; apertura del CSV del report in Excel o Numbers veri; report con dati veri di un'edizione.
- **Non verificato (MVP 8)**: embed nel sito Google vero; Safari e Firefox; spaziature del sito (CSS di Google Sites non raggiungibile dalla sessione).
- **Design system Cissone** (2026-11-05): token, font e componenti dell'intera interfaccia, nuovo selettore giornate (D-038). Audit con `npx impeccable detect` sull'iscrizione: kicker, schede annidate e riga orfana corretti; resta solo `cream-palette`, voluta. **Da verificare a mano**: pagine admin, pagina personale e stampa del report con la nuova grafica; Safari e Firefox; logo SVG del design system (qui resta il PNG).

- **MVP 9**, provato in locale con Chromium (DB nuovo da migrazioni, app costruita come in produzione con `APP_VERSION` e `BUILT_AT`, note generate dalla storia vera, 10 rilasci): partecipante a 390 px vede 9 sezioni, nessuna scheda, nessun testo admin, versione in fondo, API delle note 403; admin a 1280 px vede le tre schede, dal link «Guida» di «Giorni e slot» arriva alla sezione giusta, frecce e Fine spostano tra le schede, «Novità» elenca i rilasci; nessuno scorrimento orizzontale a 390 px su tutte e tre le schede, schede alte 45 px, nessun errore in console. Il controllo `check-guide.sh` provato su quattro casi (pagina senza guida, con guida, solo test, label).
- **Non verificato (MVP 9)**: build dell'immagine Docker con le build args (il demone Docker non c'era nella sessione); il workflow `guide.yml` e il deploy con `fetch-depth: 0` (si vedono solo su GitHub); le note di rilascio dopo un deploy vero; Safari e Firefox. **Da verificare a mano**: dopo il deploy «Novità» mostra i rilasci veri e la versione in fondo coincide con l'ultimo commit su `main`; leggere i testi della guida con gli organizzatori e correggere cosa non torna.

- **MVP 10**, provato in locale con Chromium a 390 px (iPhone 13, DB nuovo da migrazioni 0001-0010, tre iscrizioni in attesa): ricerca per causale (`g8ax` lascia una riga), canale Bonifico, «Segna pagato» registra 19,00 € e la riga mostra «Pagato · Annulla»; esce dall'elenco dopo 10,4 secondi; annullo di un'altra riga che la riporta da incassare; l'email di conferma è partita solo per il pagamento non annullato; nessun errore in console, nessuno scorrimento laterale della pagina (la tabella scorre dentro il suo riquadro).
- **Non verificato (MVP 10)**: CI su SQL Server con la migrazione 0010 e l'UPDATE condizionale; il timer da 30 secondi su Azure con l'app che scala a zero (la rete di sicurezza è nel job orario); email vera nella casella; due admin sulla stessa riga. **Da verificare a mano**: dopo il deploy segna un pagamento vero, aspetta 30 secondi e controlla l'email; annulla entro 10 secondi e controlla che non arrivi.

- **MVP 11**, provato in locale con Chromium a 390 px (lingua del browser inglese, DB nuovo da migrazioni 0001-0011, build di produzione servita dal backend): `/iscrizione` porta a `/register`, `/accedi?x=1` a `/login?x=1`, `/guida` a `/guide`; iscrizione in inglese con riepilogo «1 shift · 1 day», pagina di conferma, email in console in inglese con il link `/login/verify` e «Bank transfer (IBAN)»; accesso dal link, pagina personale in inglese con titolo e pulsanti tradotti; cambio in italiano che ricarica le etichette degli slot dal server («lun 09/11 mattina»), lingua che resta dopo il ricaricamento e salvata sul profilo; `?lang=it` vince sulla lingua del browser; guida partecipante in inglese; nessuno scorrimento laterale, nessun errore in console. Trovato e corretto in prova: le etichette del server non si aggiornavano al cambio di lingua.
- **Non verificato (MVP 11)**: CI su SQL Server con la migrazione 0011; embed reale in Google Sites con `/iscrizione` (redirect dentro l'iframe) e `?lang=en`; email vere in inglese nella casella; Safari e Firefox; il pannello admin resta in italiano (MVP 12). **Da verificare a mano**: leggere i testi inglesi con una persona madrelingua o di fiducia.

- **MVP 12**, provato in locale con Chromium a 1280 px (lingua del browser inglese, DB nuovo da migrazioni, una iscrizione fatta in inglese, admin con password): menu, «People» con intestazioni e importi in inglese; link CSV con `lang=en` che scarica `people-2026-11-05.csv` con intestazioni inglesi; «To collect» con tasti «Mark as paid» e «Other amount»; scheda con sezioni e slot («Mon 9 Nov morning»); Impostazioni; cambio in italiano dal pannello che ricarica i dati e il titolo; guida organizzatori in italiano e in inglese con la stessa sezione. Nessun errore in console.
- **Non verificato (MVP 12)**: CSV aperti in Excel o Numbers veri (il contenuto è provato nei test); lettura dei testi inglesi da una persona di fiducia; Safari e Firefox. La cronologia delle schede resta in italiano (D-044).

- **MVP 13**, provato in locale con Chromium a 390 px (DB nuovo da migrazioni 0001-0012, console): dalle Impostazioni caricato uno sfondo JPEG (ricodificato in PNG, anteprima 1600×900), oggetto e testo in inglese con segnaposto, salvataggio, anteprima con «Ada Lovelace» e «I'm Ada Lovelace and I'll be at Cissonauti Summer Camp 2027 from 10 July 2027 to 16 July 2027»; «Send me a test» recapitata all'admin; iscrizione di una persona in inglese: oggetto «Welcome Grace, see you at Cissonauti Summer Camp 2027!», testo scritto dall'admin seguito dal blocco fisso (slot, quota, causale, scadenza, istruzioni con «Bank transfer (IBAN)», link `/login/verify`), parte HTML e allegato inline; nessun errore in console. Le immagini generate sono state guardate a occhio.
- **Non verificato (MVP 13)**: la email vera in Gmail, Outlook e Apple Mail (immagine inline con `contentId` di Azure Communication Services: i test controllano il payload, non il recapito); come appare nello spam; CI su SQL Server con la migrazione 0012 (`varbinary(max)`); un file molto grande caricato su Azure (limite di richiesta del proxy). **Da verificare a mano**: dopo il deploy, carica uno sfondo vero, premi «Inviami una prova» e guarda la email nei client che usate di più.

- **MVP 14**, test automatici: backend e frontend verdi (testi delle altre email per lingua e loro effetto nelle email, testo sopra il modulo, link da 10 minuti riusabile, redirect a `/me`, nome edizione in header e titoli, barra admin sulla pagina personale), lint e `tsc` puliti, migrazione 0013 su e giù da zero. Prova in browser con DB nuovo (login admin che atterra su «Ciao …!», rinomina dell'edizione che cambia intestazione e titolo, testi salvati e email in console con testo nuovo e dati intatti, link aperto senza clic e riaperto).
- **Non verificato (MVP 14)**: CI su SQL Server con la migrazione 0013; email vere con i testi personalizzati; embed in Google Sites con il nome dell'edizione. **Da verificare a mano**: rinominare l'edizione e controllare intestazione, scheda del browser e oggetto delle email; cambiare il testo di un'email in italiano e in inglese e iscriversi nelle due lingue; entrare da admin e trovarsi sulla propria pagina; aprire il link di accesso senza clic e riaprirlo entro 10 minuti.

- **MVP 15**, completato in locale: suite completa backend 1000 test passati; suite completa frontend 363 test passati. Dopo le ultime rifiniture, i test mirati riepilogo, API e email sono passati. Build, lint, Ruff e guida verdi. In Chromium sono stati verificati il riepilogo desktop, il layout stretto e la barra fissa al 200%, il focus visibile da tastiera e il ritorno al calendario con selezioni conservate (test automatico); nessuna migrazione.
- **Non verificato (MVP 15)**: prova su telefono fisico, iframe reale in Google Sites e resa in client di posta reali. Il contenuto HTML e il testo equivalente sono coperti dai test automatici.

## Bug corretti fuori MVP

- 2026-11-07 (D-110): riprodotto con `npm audit` l'avviso `GHSA-g3hv-75wg-m249` / `CVE-2026-118764` su `minimatch@10.2.6`, dipendenza di sviluppo di ESLint e TypeScript ESLint. Override temporaneo alla versione corretta `11.0.1` e lockfile rigenerato: audit completo senza vulnerabilità. Con Node 22: `npm ci`, 378 test frontend, lint e build superati; confronto ESLint prima/dopo sugli stessi 103 file e con gli stessi messaggi (resta l'avviso preesistente in `ConfirmDialog.tsx`). Nessun cambiamento al comportamento dell'app o allo schema dati.
- 2026-11-06 (review della PR #13, D-046): il downgrade della migrazione 0011 falliva su SQL Server (vincolo di default della colonna `locale`); il modulo pubblico poteva cambiare la lingua salvata di una persona già registrata; i vecchi link alla guida con ancora italiana non portavano alla sezione; cambiando lingua in «Da incassare» si perdeva l'annullo dei pagamenti appena segnati. Corretti, con test (l'ultimo provato rosso senza la correzione). La prova su SQL Server è la CI.
- 2026-11-04: nel riepilogo e nelle email il pomeriggio compariva prima della mattina (ordinamento per nome del periodo). Corretto ordinando per orario di inizio, con test di regressione.

## MVP 15 · Logo dell'edizione e accesso dalla registrazione

Richiesto il 2026-11-06. Implementato sul branch `feat/mvp-15-logo-accesso` (D-048), in PR #15. Passati 996 test backend, 358 test frontend, Ruff, lint/build frontend e upgrade/downgrade 0013↔0014 su SQLite. Anche la CI GitHub è verde: backend SQLite, migrazioni e test backend su SQL Server, frontend e build dell'immagine. Per i test backend locali il runner ha richiesto un piccolo shim in `/tmp` per compensare il selettore asyncio che non si sveglia tra thread; non ha modificato il repository. Da verificare a mano la checklist per gli organizzatori in `specs/mvp-15-logo-accesso/pr-description.md`.

## MVP 16 · Orari, telefono e pagamenti diretti

Implementato sul branch `feat/mvp-16-pagamenti-diretti` (D-049), spec e descrizione PR in `specs/mvp-16-pagamenti-diretti/`. Telefono obbligatorio, selettori ore/minuti e intervalli UTC, attività e pasti delegati con costo/istruzioni, ricalcolo delle prenotazioni attive interessate, crediti e conferme, report/CSV e guida IT/EN.

Validazione: suite SQLite completa (1.021 test) e 34 test mirati successivi comprendenti l’ultima verifica della cronologia oraria; 366 test frontend; Ruff, ESLint/Prettier, build e controllo guida. Migrazione 0015 da zero, confronto metadata, upgrade/downgrade con attività legacy; SQL compilato per SQL Server. Per pytest, come nell’MVP 15, runner temporaneo in `/tmp/cissonauti_pytest.py` che limita l’attesa epoll per il problema di risveglio tra thread del sandbox, senza modificare codice o asserzioni.

Prova HTTP reale su database migrato temporaneo: login, istruzioni visibili a quota saldata, attività 21:35–mezzanotte, pranzo provider→organizer→provider con quota 11→19→11 €, report coerente. Il server dimostrativo è stato fermato.

SQL Server: il maintainer ha confermato superate tutte le prove il 2026-11-07; vista nel browser ancora da verificare. Checklist manuale in `pr-description.md`; nessun deploy eseguito.

## Correzione riepiloghi e quota in alto · 2026-11-07

Feedback del maintainer: durante la registrazione la quota deve rimanere in alto; i riepiloghi della pagina personale e della scheda organizzatori devono restare compatti. La pagina personale già usa `PresenceSummary`; nella scheda organizzatori era rimasta la lista di ogni fascia (come nello screenshot). La scheda ora riusa il riepilogo per giorno; quota e invio restano in una barra superiore che si ferma sotto l'intestazione sticky. Guide aggiornate in italiano e inglese. Verificati 369 test frontend, lint, build e controllo guide; in Chromium la barra resta sotto l'intestazione su desktop e in cima su telefono e iframe, e l'iscrizione di prova si completa.
