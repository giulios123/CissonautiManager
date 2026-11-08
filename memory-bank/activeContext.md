# Active context

## Ora

**2026-11-08 · MVP20 implementato sul branch `feat/mvp-20-riaccettazione-privacy`, atop MVP19 in `main`.** Nuova accettazione privacy versionata, migrazione legacy `0019` dopo la migrazione profilo `0018`, blocco backend delle modifiche pendenti, UI partecipante/admin e richiesta email una tantum nel job orario. T20-1–7 completati; T20-8 aperto: suite backend completa, SQL Server e prove organizzatori. Verificati 30 test backend mirati, 401 frontend completi e 3 test mirati aggiuntivi sulla versione finale, Ruff, ESLint/Prettier, TypeScript/build e guida bilingue. Il runner backend completo è stato fermato al 19% dopo dieci minuti; in questa sessione non sono disponibili TEST_DATABASE_URL né accesso al socket Docker. Nessun deploy, email reale o testo legale definitivo.

**MVP 19** implementato e ora presente in `main`: profilo annuale e contatti social, cataloghi locali ISTAT/ISO, campi obbligatori anche per sola lista, API personali/admin e richiamo legacy non bloccante; guide IT/EN e spec in `specs/mvp-19-profilo-completo/`. Restano le prove visuali e la verifica SQL Server CI della sessione precedente. Nessun deploy o email reale.

MVP18 resta implementato: backend 1083 test, frontend 394, prove SQL confermate dal maintainer; le procedure manuali e l'attivazione reale sono ancora aperte. Per MVP17 restano collaudo visivo e testi legali definitivi.

**2026-11-07 · Spec esecutive MVP 17 e 18 pronte e in implementazione (B1).** Richiesta esplicita del maintainer di preparare entrambe: [17 · Consensi e riservatezza](../specs/mvp-17-consensi-riservatezza/requirements.md) con 8 task, design, microtesti IT/EN e prove manuali; [18 · Conferma con la sola quota](../specs/mvp-18-conferma-quota/requirements.md) con 10 task, design e prove manuali. Il codice 17 è in lavorazione; nessun deploy o invio reale eseguito.

La scelta aggiuntiva confermata preparando la spec è D-105, ricalcolo dei due importi con anteprima e applicazione admin, versamenti intatti e variazioni di saldo/credito esplicite. Proposte tecniche D-106–D-109 registrate; le regole di prodotto restano quelle confermate. La migrazione additiva 0016 è in lavorazione e ha lasciato intatti i documenti legali legacy.

Materiale aperto del 17: testi legali effettivi IT/EN e destinazioni media da validare prima della produzione; lo sviluppo può usare fixture esplicite. Il 18 seguirà dopo la chiusura tecnica del 17 e userà lo schema aggiornato. L'attivazione effettiva della nuova quota resterà un passaggio admin distinto dalla distribuzione.

MVP 16 risulta implementato/task completati ma conserva le verifiche reali pendenti in `progress.md`; nessun merge/deploy dedotto dal checkout. Il [dossier A–F](../specs/revisione-2026-11-07/README.md) e il [registro risposte/residui](../specs/revisione-2026-11-07/domande-aperte.md) restano allineati. Calendario D3 accantonato, F valutazione con direzione scelta; nessuna implementazione delle altre proposte.

## Contesto storico delle implementazioni precedenti

MVP 1 chiuso salvo il task 15 (verifica in Google Sites), aperto e non bloccante. MVP 2 e MVP 3 su `main` e deployati su Azure (PR #4 e #5, task 9 dell'MVP 2 validato): `https://cissonauti-booking.wonderfulbush-cbda30f0.italynorth.azurecontainerapps.io`. MVP 4, 5 e 6 implementati e provati in locale sul branch `claude/quirky-meitner-qn9hwh`, in PR verso `main`; descrizioni per gli organizzatori in `specs/mvp-0{4,5,6}-*/pr-description.md`. Modifiche a `domain.md` dei tre MVP applicate.

## MVP 9 · Guida in app (2026-11-05)

Richiesta del maintainer: guida dopo il login filtrata per ruolo, aggiornata a ogni deploy; note di rilascio solo per gli admin. Spec in `specs/mvp-09-guida/`, confermata. Scelte: note generate dai commit; testi della guida nel repo con controllo CI; l'admin vede tutto, il partecipante solo la sua guida (D-039). Completato sul branch `claude/dreamy-ride-bzr112`, descrizione PR in `specs/mvp-09-guida/pr-description.md`. Da fare: far leggere i testi agli organizzatori; creare la label `senza-guida` su GitHub.

## MVP 10 · Incassi (2026-11-05)

Richiesta del maintainer: un modo veloce per l'admin di controllare il conto e segnare le quote come coperte. «Da verificare» resta per le anomalie (con zero versato una iscrizione in attesa non vi compare, per regola). Spec in `specs/mvp-10-incassi/`, confermata. Scelte concordate: pagina nuova «Da incassare»; canale scelto una volta; tasto rapido sul saldo intero con link alla scheda per altri importi; un clic con annullo visibile per 10 secondi; email di conferma differita di 30 secondi (colonne su `payment`, migrazione 0010, rete di sicurezza nel job orario); ricerca per causale; scadute incluse in coda. Spec confermata dal maintainer, completato sul branch `claude/brave-babbage-ttfx6u` (D-040), descrizione PR in `specs/mvp-10-incassi/pr-description.md`. Da fare: provare in produzione l'email dopo 30 secondi.

## MVP 11-13 · Lingue, admin in inglese, email di iscrizione (2026-11-05)

Richiesta del maintainer: interfaccia in italiano e inglese, indirizzi in inglese (gli italiani funzionano solo se scritti a mano e reindirizzano), testo della mail di conferma modificabile e immagine di sfondo con «I'm nome cognome and I'll be at evento from data to data». Scelte: PNG generato dal server; lingua da browser e selettore, salvata sul partecipante; email nella sua lingua; guida in due lingue. Spec in `specs/mvp-11-lingue/`, `mvp-12-admin-inglese/`, `mvp-13-email-iscrizione/`. Regola nuova in `AGENTS.md`: ogni funzione futura è bilingue. Piano approvato. **MVP 11 completato** sul branch `claude/relaxed-dijkstra-9z2e5o` (D-041, D-042, D-043; descrizione PR in `specs/mvp-11-lingue/pr-description.md`). **MVP 12 completato** (D-044, descrizione PR in `specs/mvp-12-admin-inglese/pr-description.md`). **MVP 13 completato** (D-045, descrizione PR in `specs/mvp-13-email-iscrizione/pr-description.md`). Gli MVP 11-13 sono finiti: restano il passaggio su `main` e le prove manuali in produzione (checklist nelle tre `pr-description.md`).

## MVP 14 · Testi dell'evento e accesso diretto (2026-11-06)

Richiesta del maintainer: nome dell'edizione in header e oggetti email; testo delle email e del modulo modificabili da admin; dopo il login sempre la pagina personale; magic link riusabile 10 minuti senza pagina «Entra». Spec in `specs/mvp-14-testi-evento/`. Nata come «MVP 11» sul branch `feat/mvp-11-testi-evento` (PR #14), poi riallineata a `main` dopo l'unione degli MVP 11-13 (lingue, admin in inglese, email di iscrizione): i testi delle altre email usano l'editor per lingua dell'MVP 13 (D-047). Completato, descrizione PR in `specs/mvp-14-testi-evento/pr-description.md`. Da fare: provare in produzione email personalizzate e link da 10 minuti.

## MVP 15 · Logo e accesso dalla registrazione (2026-11-06)

Richiesta del maintainer: caricare e ripristinare il logo dell'edizione dalle Impostazioni; aprire la pagina personale cliccando il marchio; trovare «Accedi» dalla pagina d'iscrizione, anche nell'iframe. Spec in `specs/mvp-15-logo-accesso/`. Implementato sul branch `feat/mvp-15-logo-accesso`, in PR #15 (D-048); CI SQLite, SQL Server, frontend e build container verdi. Restano le prove manuali descritte nella checklist della PR.

## MVP 15 · Riepiloghi compatti delle presenze

Implementazione completata il 2026-11-06 sul piano concordato con il maintainer, in PR #16. Una riga per giorno; data sola se la presenza è completa (mattina+pomeriggio incluse), fasce piccole nei giorni parziali; legenda unica degli orari; lista d'attesa separata; «Modifica presenze» torna al calendario mantenendo le scelte. Intervento bilingue su modulo, pagina personale e email, senza migrazione. Suite completa backend 1000/1000 e frontend 363/363; build, lint, Ruff e guida verdi. Da provare dopo il deploy su telefono fisico, iframe reale e client email reali.

## Verifiche pendenti delle release precedenti

1. CI della PR, in particolare SQL Server con le migrazioni 0005-0007 da zero.
2. Dopo il merge il deploy applica le migrazioni 0005-0007 all'avvio: il primo avvio a freddo può essere lento (circa 4 minuti con la PR #5).
3. Prove manuali in produzione con le checklist di MVP 2-6: email vera nella casella e fuori dallo spam, il job `cissonauti-booking-reminders` che gira ogni ora (portale Azure, «Execution history»), viste e CSV con dati veri, lista d'attesa che si sblocca dopo una scadenza.
4. MVP 7 (inviti e report): fatto, vedi sotto.
5. Importi definitivi di pranzo e cena (oggi 8 € e 12 €, segnaposto).

## Scelte del maintainer per MVP 4-6 (2026-11-05)

- B0: l'MVP 4 non era fatto; il maintainer ha chiesto di pianificare 4, 5 e 6 insieme.
- MVP 4: lista d'attesa anche dal modulo pubblico, anche senza slot liberi; promozione su prenotazione confermata: resta confermata, saldo con la differenza.
- MVP 5: due prezzi (pranzo e cena); regime senza consenso, allergie e intolleranze con consenso specifico; pasti modificabili come gli slot.
- MVP 6: si aderisce a un'attività solo se presenti in quella fascia.

## Risposte del maintainer su MVP 4-6

- Prezzi di pranzo e cena: segnaposto (8 € e 12 €) finché non ci sono gli importi definitivi.
- Email di promozione ai confermati senza scadenza: va bene.
- Promozione dopo una scadenza entro un'ora con il job orario: va bene.
- Pranzo con mattina o pomeriggio: confermato.
- Attività su tutto il giorno: restano nel Backlog.

## Spec degli MVP 7 e 8 (2026-11-05)

Scritte su richiesta del maintainer mentre gli MVP 4-6 sono in lavorazione altrove: `specs/mvp-07-inviti-report/` e `specs/mvp-08-stile-sito/`. Confermate.

- MVP 7: priorità a chi è stato invitato (+1), verificata dall'admin con una spunta; ordine calcolato alla promozione. Report di edizione a video, in stampa e in CSV. Spec riallineata il 2026-11-05 sul codice reale degli MVP 4-6 (ora su `main`): la priorità si innesta in `queue` di `domain/waitlist.py`, la verifica è per id partecipante (chi è solo in lista non ha una scheda, D-028), migrazione 0008, 9 task.
- MVP 8 (nuovo): grafica ripresa da https://sites.google.com/view/cissoneeventi/welcome. Colori, font (Montserrat) e loghi rilevati in `specs/mvp-08-stile-sito/stile.md`. Confermati: nome «Cissonauti Summer Camp», palette petrolio `#005C68` e ambra `#F4B400`, bottoni squadrati. Aperto: permesso della Pro Loco per i loghi (senza, l'intestazione mostra solo il nome).

Risposte del maintainer (2026-11-05), spec confermate:

- MVP 7: un +1 verificato non entra oltre il limite della lista; il report distingue confermate e in attesa di pagamento.
- MVP 8: nessuna modalità scura; dentro l'iframe intestazione ridotta (solo il nome, senza logo).

MVP 8 completato sul branch `claude/nifty-hawking-mgu6fa` (D-035), descrizione PR in `specs/mvp-08-stile-sito/pr-description.md`. Da provare nel sito Google vero dopo il deploy. Le pagine degli MVP 4-7 devono usare i token di `styles.css`, senza colori scritti a mano (lo controlla `theme.test.ts`).

MVP 7 completato sul branch `claude/nifty-hawking-mgu6fa` (D-037), descrizione PR in `specs/mvp-07-inviti-report/pr-description.md`. Con questo la roadmap degli MVP è finita: resta il passaggio su `main` e le prove manuali in produzione (checklist delle PR degli MVP 2-8).

Scelte confermate dal maintainer sull'MVP 7: la verifica del +1 sta sul partecipante (con più edizioni andrà spostata, Backlog); la scomposizione del dovuto nel report usa i prezzi correnti, con una riga «differenza» se sono cambiati dopo le iscrizioni.

## Risolto il 2026-11-05 (conferma del maintainer)

- Spec 2 e 3 confermate, parte l'MVP 2.
- Disdetta senza pagamenti: la prenotazione si rimuove e basta. Con pagamenti: `disdetta_richiesta`.
- Giorni passati: il partecipante non può cambiare gli slot, solo l'admin.
- La proroga della scadenza resta nell'MVP 3; l'importo dovuto modificabile a mano resta nel Backlog.
- Modifiche a `domain.md` approvate (5 per l'MVP 2, 6 per l'MVP 3): si applicano in chiusura di ciascun MVP.

## Stato degli MVP 2 e 3

Sviluppo sul branch `claude/magical-gauss-vbss2u` (non `feat/...`, per il vincolo di push della sessione). Decisioni D-014 a D-019 (MVP 2) e D-020 a D-024 (MVP 3) in `decisions.md`; le modifiche a `domain.md` approvate sono applicate.

## Domande aperte

- MVP 3: l'admin non può cambiare a mano l'importo dovuto (sconti, organizzatori gratis): resta nel Backlog.
- MVP 3: se un admin cambia gli slot a una persona, a lei non parte nessuna email (Backlog).

- Il dominio gestito Azure può finire nella posta indesiderata: se succede, serve un dominio proprio (Backlog).
- La pagina pubblica di iscrizione permette di scegliere giorni già passati: bloccarli durante l'evento? (Backlog).

## Dubbi aperti ereditati

- Task 15: verifica dell'embed reale in Google Sites e chiusura dell'MVP 1.
- Finché il task 9 non è validato in produzione i magic link compaiono solo nei log (`EMAIL_PROVIDER=console`).
- Il database Basic non si mette in pausa; la Container App deve restare a `minReplicas: 0`.
- Presenza di giorno per il pranzo: la spec dell'MVP 5 propone mattina o pomeriggio (da confermare).
- Esiti della call (D-008), sera derivata (D-009), nome con due s (D-012) e risorse ricreate (D-013): già registrati in `decisions.md`.

## MVP 16 · Orari e pagamenti diretti (2026-11-06)

Piano confermato dal maintainer e implementato sul branch `feat/mvp-16-pagamenti-diretti`, spec in `specs/mvp-16-pagamenti-diretti/`. Telefono obbligatorio, orari selezionabili, attività e pasti delegati con costo specifico e ricalcolo dei saldi anche dopo le adesioni.

Completati codice, test automatici, migrazione, guida e checklist PR. Il maintainer ha confermato superate le prove SQL; resta la prova visiva mobile/desktop. Nessun deploy in questa sessione.
