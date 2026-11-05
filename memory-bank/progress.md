# Progress

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

## Bug corretti fuori MVP

- 2026-11-04: nel riepilogo e nelle email il pomeriggio compariva prima della mattina (ordinamento per nome del periodo). Corretto ordinando per orario di inizio, con test di regressione.
