# MVP 18 · Design

Proposta esecutiva dopo la migrazione 0016 del 17; migrazione 0017 da verificare sul ramo base prima di implementare. [Requisiti](requirements.md), [task](tasks.md), [test manuali](test-manuali.md). Nessun nuovo motore prezzi o registro di pagamenti.

## Grandezze e invarianti

| Valore | Significato |
|---|---|
| `Booking.registration_fee_cents` | Quota base+giorni dell'ultimo ricalcolo del booking; snapshot non negativo, nullo soltanto per legacy non ancora valutati/archiviati. |
| `amount_due_cents` | Totale all'organizzazione già esistente: quota più extra organizzazione, senza provider. Nessun cambio di significato. |
| `paid_cents` | Somma delle righe `Payment` non annullate; nessuna riga spezzata o trasferita per imputarla alla quota. |
| `confirmation_due_cents` | Soglia applicabile: totale nella politica legacy, `registration_fee_cents` nella nuova. Non è un secondo debito da sommare al totale. |
| `confirmation_balance_cents` | Per attesa/scaduta: `max(0, confirmation_due_cents - paid_cents)`; per confermata 0; per disdetta/rimborso non applicabile (`null`). Serve alla comunicazione operativa, non al calcolo di copertura interno. |
| `balance_cents` | `amount_due_cents - paid_cents`, positivo da incassare o negativo a credito, indipendente dal residuo operativo per confermare. |

Nel dominio la copertura usa sempre `paid_cents >= confirmation_due_cents`, anche durante un annullo; non usa lo zero operativo mostrato sulle confermate. Una confermata dopo aggiunta di giorni può restare tale pur non coprendo la nuova quota, come regola D-017: mostrare stato stabile e saldo, non una scadenza. L'annullo è l'evento esplicito che può farla tornare in attesa se la quota corrente non è coperta.

Esempio dopo attivazione: base 10 € + 2 giorni × 1 € = 12 €; extra organizzazione 12 €, provider 15 €. Totale organizzazione 24 €. Versati 5 € → attesa, residuo conferma 7 €, saldo 19 €. Versati 12 € → confermata, residuo operativo 0 €, saldo 12 €, provider 15 € separato. Nessuna inclusione del primo pasto prima dell'MVP 23.

## Prezzi e consistenza

Un solo calcolo puro produce quota ed extra; `services/amounts.recompute_amount` salva quota e totale nello stesso passaggio, riusando `compute_fee`, `meal_terms` e `activity_terms`. Contare date degli slot assegnati, sera compresa, non liste. Slot vuoti non sono un booking gratuito: il caso sola lista continua a non creare booking.

Mantenere la regola D-017: un cambio alle impostazioni generali non riscrive da solo tutti i booking; il prossimo ricalcolo richiesto da un'operazione ammessa usa i prezzi correnti e salva insieme entrambi gli importi. Nessuna lettura ricava una quota nuova dalle impostazioni correnti affiancandola a un totale vecchio. L'anteprima di attivazione è l'operazione esplicita, approvata dal maintainer, che ricalcola insieme tutte le sole attive.

Se la quota effettiva è zero, un booking con posti assegnati nasce o passa confermato; nessun `Payment(amount=0)`, nessun promemoria. Le esenzioni personali non sono simulate nel 18: verranno aggiunte dal 25c come componenti esplicite del medesimo calcolo.

## Modello dati · migrazione proposta 0017

| Entità | Aggiunta | Inizializzazione conservativa |
|---|---|---|
| `Edition` | `confirmation_policy`: `legacy_total` / `registration_fee` | `legacy_total` per le edizioni presenti e nuove fino alla loro attivazione esplicita. |
| `Edition` | `confirmation_policy_activated_at`, `confirmation_policy_preview_token` nullable | Null; memorizzano il passaggio applicato per idempotenza, non identificano una credenziale. |
| `Booking` | `registration_fee_cents` nullable | Null sulle righe esistenti; quota calcolata sui nuovi booking e ai ricalcoli successivi. |
| `Booking` | `confirmation_cycle`, `confirmation_claimed_cycle` interi non negativi, `confirmation_notice_due_at` nullable | Valori neutri; nessuna email generata dalla sola migrazione. |
| `Booking` | `confirmation_notice_payment_id` intero nullable, validato dal servizio | Riferimento al pagamento che causa una conferma, se presente; non FK, per non introdurre una dipendenza circolare con Payment o percorsi di cancellazione aggiuntivi SQL Server. |

I campi di notifica rappresentano il ciclo di conferma, non il pagamento. Il servizio verifica che il riferimento appartenga allo stesso booking; nessuna cancellazione di booking con righe pagamento viene introdotta. La scelta del riferimento senza FK è analoga al collegamento dell'audit e va coperta dai test di integrità applicativa, non lasciata implicita nel mapping.

Non riempire i booking storici con una quota «originale» ricostruita dai prezzi di oggi. La quota delle attive viene calcolata dall'anteprima al passaggio; quelle chiuse/scadute rimangono intatte fino a una futura riattivazione esplicita ammessa, che ricalcola secondo il flusso attuale. Nessun seed di nuovi prezzi.

## Matrice delle transizioni

| Percorso | Criterio nella nuova politica | Stato / effetti |
|---|---|---|
| Nuova registrazione / booking da promozione | Quota positiva o zero | Attesa se quota non coperta, confermata se coperta; sola lista senza booking. |
| Pagamento dalla scheda o Da incassare | Somma non annullata rispetto alla quota salvata | Attesa valida coperta → confermata; niente nuova conferma per pagare soli extra di una già confermata. |
| Cambio slot, pasti, attività | Ricalcolo atomico quota+totale | Attesa coperta → confermata; confermata rimane tale anche con differenze da versare. |
| Cambio prezzo/modalità attività o singolo pasto | `pricing.reprice` sulle sole attive interessate | Come sopra; provider mai negli importi evento. |
| Annullo pagamento | Copertura quota dopo annullo | Conserva conferma se coperta, altrimenti nuovo blocco; motivo e riga intatti. |
| Riattivazione scaduta | Prima capienza/duplicati/attività, poi ricalcolo | Conferma sulla quota solo dopo riattivazione riuscita; nessun nuovo posto se pieno. |
| Promozione su attesa esistente | Nuova quota e scadenza secondo regole waitlist | Conferma se coperta; confermata già esistente stabile. |
| Job promemoria | Stato effettivo attesa, scadenza futura, quota residua > 0 | Importo della sola quota; stessi orari e marcature dei promemoria. |
| Report / Da incassare | Saldo sul totale | Extra e crediti restano; lo stato confermato non equivale a saldo zero. |

Aggiornare tutti i punti verificati: `registration._new_booking`, `payments.record_payment/void_payment/revive_expired`, `booking_admin.reactivate`, `booking_changes.change_slots`, `meals.change_meals`, `activities.change_activities`, `pricing.reprice`, `waitlist._new_booking/_add_slot`, `jobs/send_reminders`, serializzazioni e template email. Funzioni di copertura condivise, non condizioni riscritte in ogni pagina. Scadenze effettive valutate **prima** di confermare: nessuna conferma tardiva implicita di una scaduta da un semplice ricalcolo.

## Transizione legacy con anteprima

### Lettura

`GET /api/admin/edition/confirmation-policy/preview`, `require_admin`, `Cache-Control: no-store`. Sessione di lettura coerente sotto lock dell'edizione; nessuna chiamata a servizi che fanno commit o scrivono le scadenze. Usare gli stati effettivi per classificare:

- solo `in_attesa_pagamento` ancora valida e `confermata` nell'edizione attiva;
- quota e totale proposti dai prezzi/selezioni correnti, versamenti validi letti senza modificarli;
- per riga: id/nome admin, stato, quota disponibile, totale, pagato, saldo/credito prima e dopo, stato proposto e motivo della differenza;
- conteggi escluse/scadute/chiuse/solo lista e nuove email di conferma previste;
- `preview_token` fingerprint del contenuto rilevante: politica, impostazioni prezzi, selezioni, stati/scadenze, pagamenti/annulli e notifiche pendenti.

Il token non autorizza l'azione e non contiene importi da fidarsi dal client: i permessi e il ricalcolo sono sempre server. Una scadenza che passa fra preview e apply cambia l'insieme ammissibile e invalida l'anteprima. Dati insufficienti o incoerenza non producono un'assegnazione arbitraria: evidenziare la riga e impedire il passaggio finché risolta.

### Applicazione

`POST /api/admin/edition/confirmation-policy/activate`, `require_admin`, body `{preview_token}`. Dopo il lock edizione verificare **prima** se la stessa operazione è già stata applicata: in quel caso 200 con `already_applied=true`, nessun nuovo effetto, senza confrontare il fingerprint ormai cambiato dalla propria applicazione. Altrimenti lock booking in ordine id, rilettura e ricalcolo dell'anteprima con orologio corrente. Se fingerprint diverso: 409 localizzato, nessuna scrittura. Una politica già attivata con un altro token non viene riapplicata.

Una sola transazione aggiorna quota/totale delle attive, conferma le sole attese coperte, conserva le confermate, scrive audit con differenze e commuta la politica. Incassi/rimborsi non sono modificati; scadenze delle attese non confermate restano. Conservare token e istante di attivazione. Non richiamare i servizi esistenti che fanno `commit()` per ogni riga: estrarre il calcolo e la mutazione senza commit per questo caso; commit unico e notifiche solo dopo.

UI Impostazioni: spiegazione prima/dopo, tabella differenze con saldo e credito, conteggio delle notifiche e comando «Applica nuova regola / Apply new rule». Nessun toggle reversibile che ripristini automaticamente il vecchio criterio; eventuale rollback del codice mantiene i dati e richiede una correzione esplicita. Cambi di tariffe ordinari restano nel loro editor e non attivano da soli il passaggio.

## Conferme email e concorrenza

Centralizzare la prenotazione della notifica sul **passaggio di stato**, non sull'esistenza di un nuovo pagamento:

1. Ogni transizione effettiva attesa→confermata incrementa `confirmation_cycle`, assegna `confirmation_notice_due_at` (ora oppure +30 s per incasso rapido) e l'eventuale pagamento causante. Per nuova registrazione già confermata a quota zero usare solo l'email di iscrizione, marcando il ciclo già gestito senza inviare una ricevuta.
2. Sulla transazione di attivazione accodare soltanto le nuove conferme. Una già confermata non riceve un'altra email per il solo ricalcolo.
3. Timer/job reclamano il ciclo con UPDATE condizionato sotto l'ordine di lock edizione→booking, verificando ciclo/due time/stato e, se collegato, pagamento non annullato; salvano `confirmation_claimed_cycle = confirmation_cycle` e svuotano il due time, poi fanno commit **prima** dell'invio, secondo D-016. Un annullo che invalida il pagamento causante cancella quella notifica; una nuova conferma successiva è un nuovo ciclo. Il timer di un vecchio ciclo non anticipa o reclama un ciclo diverso.
4. Conservare il recupero nel job orario esistente; non introdurre un'altra infrastruttura. Un fallimento è loggato e non ritentato automaticamente, come oggi: «reclamato» non significa consegnato.

Adattare `send_due_confirmations` al ciclo per le edizioni attivate. I campi `Payment.confirmation_email_*` restano compatibili come metadati del flusso esistente, **non una seconda autorità di invio**: trasferire al ciclo le conferme differite ancora valide al momento dell'attivazione, lasciando identiche le date già previste e senza duplicare un invio già reclamato. Il job/timer deve prendere lo stesso lock anche nel tratto legacy durante il passaggio; un invio concorrente invalida la preview o viene visto prima di applicare. Storico dei pagamenti già notificati non viene rigenerato.

Template: mantenere `payment_confirmation` dove c'è davvero un pagamento e introdurre `booking_confirmation` IT/EN per conferma senza nuovo incasso. Testo automatico con stato, quota coperta, saldo extra e accesso personale; l'editor email esistente può gestire la nuova introduzione con gli stessi segnaposto. Nessuna email di sollecito extra aggiunta. Controllare che template personalizzati esistenti non alterino il blocco automatico degli importi; segnalarli nell'anteprima come testi da rivedere se contengono istruzioni ormai superate, senza riscriverli in silenzio.

Promemoria: usare soglia persistita della politica, residuo quota e `_claim` coerente con quota/politica/pagato correnti, ricontrollati sotto lock. Il job non deve confermare o sollecitare con un dato vecchio mentre un admin paga, annulla o attiva la politica. Conservare metà/24h, caso blocco corto, proroga e riattivazione.

## Contratti e pagine

`BookingView`, `BookingSummary` pubblico limitato al nuovo invio, elenco/dettaglio admin e vista Da incassare aggiungono `registration_fee_cents`, `confirmation_due_cents`, `confirmation_balance_cents`, `confirmation_policy`; mantengono `amount_due_cents`, `paid_cents`, `balance_cents` dove già presenti. Quote/residui sono `int | null` per i casi storici non ricostruibili o non applicabili; per una attesa attivata i valori sono sempre disponibili. Le sole liste hanno importi zero senza booking e nessuna soglia operativa. Sulle chiuse soglia/residuo sono non applicabili, senza ricostruire prezzi storici.

`Personal.tsx`, ricevuta `Registration.tsx`, scheda admin e `AdminCollect.tsx` mostrano quota e saldo distinti senza introdurre la modale B3. Il tipo `Summary` del frontend deve consumare lo `status` già restituito dal backend: una ricevuta confermata a quota zero non mostra un blocco in scadenza. Dopo conferma il vecchio avviso «saldo da versare» resta, con testo che non minaccia il posto. Gli editor slot/pasti/attività devono usare la stessa proiezione dei due importi; nessuna anteprima di conferma basata sul totale. Se i dati prezzo non permettono l'anteprima esatta, indicarlo e mostrare il risultato server al salvataggio, senza un calcolo contraddittorio.

Report: quote delle attive dalla quota salvata, extra secondo i dati del ricalcolo e scarto esplicito dove già previsto, totale/saldo riconciliati con il registro. Il CSV Persone aggiunge quota e residuo conferma con intestazioni IT/EN in `admin_texts.py`; il report aggregato distingue la somma dei residui per conferma dalla somma dei saldi positivi, senza sommarle come debiti diversi. Da incassare conserva l'assenza di CSV del suo MVP originale. Nessun costo provider negli incassi; nessun export storico reinterpretato o incasso esterno anticipato.

## Microtesti proposti

| Uso | Italiano | English |
|---|---|---|
| Residuo quota | Dovuto per confermare la prenotazione: {amount} | Amount due to confirm your booking: {amount} |
| Rinvio extra | Pranzi, cene e attività possono essere pagati dopo. | Lunches, dinners and activities can be paid later. |
| Totale | Totale dovuto all'organizzazione | Total due to the organisers |
| Confermata con saldo | La prenotazione è confermata. Resta da saldare {amount}. | Your booking is confirmed. The remaining balance is {amount}. |
| Conferma senza pagamento nuovo | La quota richiesta è coperta: la tua prenotazione è confermata. | The required registration fee is covered: your booking is confirmed. |
| Preview cambiata | I dati sono cambiati. Ricarica l'anteprima prima di applicare. | The data has changed. Refresh the preview before applying. |

Errori backend/i18n e template email nei cataloghi esistenti. Guide IT/EN partecipante `03-paying.md`, `04-changing-slots.md`, `05-meals.md`, `06-activities.md`, `08-waitlist.md` se cambia la spiegazione; admin `01-people.md`, `08-to-review.md`, `10-settings.md`, `12-to-collect.md`, report/email pertinenti. Non serve ritoccare ogni file se il suo contenuto resta corretto; aggiornare quelli delle funzioni visibili cambiate.

## Rilascio, test e Modifiche a domain.md

La migrazione 0016→0017 è additiva e non attiva la politica. Test upgrade da zero/legacy con incassi, annulli e conferme differite pendenti; schema/metadata, SQLite e SQL Server. L'app con nuove regole resta nella politica legacy finché l'admin non applica la preview. Verificare entrambe le politiche prima di considerare pronto il rilascio; applicazione reale non inclusa nella sola preparazione della spec.

Da riportare in `domain.md` solo con approvazione/chiusura: conferma sulla quota base+giorni, snapshot quota/totale coerenti, residuo operativo distinto dal saldo, annullo sulla quota e adeguamento promemoria, zero senza pagamento fittizio, transizione amministrativa con anteprima. Conservare D-017 sulle confermate e ricalcoli, D-021 sugli annulli, D-049 sui provider e i vincoli di riattivazione. Non aggiungere inclusioni B4, esenzioni, calendario o nuovo supporto edizioni.
