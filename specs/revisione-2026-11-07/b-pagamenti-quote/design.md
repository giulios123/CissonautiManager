# B · Design proposto

Per B1/B2 e promemoria vedere il [design esecutivo 18](../../mvp-18-conferma-quota/design.md): snapshot dei due importi, regola zero e transizione con ricalcolo esplicito approvato in D-105. Modale, inclusioni e destinatari globali restano nei rilasci successivi.

## Flusso e grandezze economiche

Selezioni → unica funzione di calcolo lato server → quota necessaria per il posto, extra organizzazione e costi diretti separati → registrazione di un pagamento organizzazione → conferma in base alla sola quota → saldo complessivo ancora visibile.

Tutti gli importi restano centesimi interi. Formula confermata: **base + importo dei giorni scelti**, esclusi pasti/attività; per un non pagante applicare le sole esenzioni esplicite. Grandezze tecniche proposte:

- `confirmation_due_cents`: quota necessaria alla conferma, esclusi extra.
- `amount_due_cents`: totale all'organizzazione dopo le inclusioni B4; conserva il significato contabile attuale.
- `paid_cents`: somma pagamenti non annullati; nessuna nuova duplicazione o allocazione fittizia dei vecchi versamenti.
- `confirmation_balance_cents`: residuo operativo sulle attese/scadute; zero su una già confermata e non applicabile sulle chiuse, come precisato nel 18. Il dominio confronta comunque pagato e soglia, senza usare lo zero operativo per decidere gli annulli.
- `balance_cents = amount_due_cents - paid_cents`: saldo totale o credito, mai forzato a zero per nascondere extra.

Esempio coerente con la formula confermata: base 10 € + due giorni da 1 € = quota 12 €, due pasti extra 6 € ciascuno, totale 24 €. Versati 12 €: posto confermato, residuo conferma 0 €, saldo totale 12 €. Dopo annullo di 6 € del versato: quota non coperta, nuovo blocco secondo la regola attuale di annullo. Quota coperta ma extra insoluti: nessun nuovo blocco. La regola di imputazione prioritaria e il caso quota zero restano dettagli da formalizzare, senza riaprire la formula.

## Modello dati e migrazioni

B1 nel 18 propone la quota persistita con il totale nello stesso ricalcolo; letture senza prezzi dinamici affiancati a totali vecchi. Migrazione neutra e successiva attivazione admin con preview e ricalcolo ai valori correnti, approvata dal maintainer; nessuna modifica ai versamenti. Prezzi ai ricalcoli successivi come D-017, senza riscrivere gli archivi; variazioni di saldo/credito esposte nell'anteprima.

B4 introduce una politica per edizione e la spiegazione delle voci coperte. Distinguere budget congiunto «primo pasto» da quantità indipendenti pranzo/cena: default congiunto 1, non 1+1. Il primo si sceglie tra pasti selezionati con incasso organizzazione, in ordine data/tipo (pranzo prima di cena); i `provider` non consumano il beneficio e restano promemoria esterni al conto. Quantità intere non negative, nessun doppio sconto. Oltre ai pasti, il maintainer limita le altre voci a **benefit**; nessuna attività/servizio generico coperto. Il catalogo minimo dei benefit può essere disponibile nel 23, mentre la pagina consegne resta nel 30.

Migrazione di B4 senza addebiti retroattivi: dati precedenti conservati, anteprima della nuova politica prima dell'attivazione. Dopo l'attivazione, ricalcolo atomico delle sole prenotazioni attive interessate con gli stessi lock di D-049, mantenendo pagamenti, crediti, scadenze e regole di conferma aggiornate. Non aggiungere `edition_id` a Payment se è già determinato dal booking senza un motivo di integrità (F).

## API, pagine e compatibilità

Estendere `BookingView`, ricevuta di iscrizione e risposte admin con soglia e residuo, senza riutilizzare il totale per significati diversi. Regole da aggiornare insieme: registrazione, incassi, annullo, modifica slot/pasti/attività, ricalcolo prezzi, promozione waitlist, riattivazione, email di conferma e promemoria. La sola modifica al frontend non soddisfa B1.

`AdminCollect.tsx`: modale sullo stesso endpoint `POST /api/admin/registrations/{id}/payments`, con `defer_confirmation_email=true`, canale/data/nota e annullo esistenti. Nessuna nuova tabella o secondo libro incassi per B3. Confermato il controllo del saldo aggiornato prima del salvataggio e la revisione esplicita dell'importo; una risposta di conflitto non ritenta il pagamento automaticamente. Sovraversamenti validi possibili come credito. Il futuro flusso incassi esterni C2 resta distinto dal pagamento del booking.

Terminologia IT/EN confermata: modalità «Incasso dell'organizzazione / Collected by the organisers», componente «Quota di registrazione / Registration fee», modalità «Pagamento in loco al fornitore / Pay the provider on site». Sono due modalità; quota ed extra sono componenti, non altri tipi. «Coperto dalla quota di registrazione / Covered by the registration fee» si usa soltanto se B4 lo rende vero, mai come sinonimo della modalità di incasso.

Report/CSV distinguono quota, extra organizzazione, costi diretti e credito; le somme si riconciliano con il registro. Guide ed email IT/EN da aggiornare nei rispettivi MVP. `Da incassare` continua a comprendere confermate con extra da saldare; il promemoria automatico di posto è un flusso diverso.

## Modifiche a domain.md

Non applicate al comportamento operativo: conferma su base+giorni, soglia e totale separati, importi parziali dalla lista, inclusione pasti/benefit e terminologia confermata. Preservare annullo tracciato, confermate stabili dopo aumento extra, provider fuori dagli incassi e rimborsi manuali. B1/B2 sono ora specificati nel 18 per la revisione; restano le inclusioni Q-B4 del 23, non la scelta della formula o del ricalcolo iniziale. C2 aggiungerà esenzioni mirate e incassi esterni separati; non azzerare indiscriminatamente il conto di ogni non pagante.
