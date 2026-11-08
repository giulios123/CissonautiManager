# MVP 19 · Profilo completo e iscritti precedenti

## User story e criteri di accettazione

1. **Nuovo profilo.** Quando una persona si iscrive a uno o più slot oppure solo a una lista d'attesa, allora fornisce telefono, Telegram, LinkedIn, città, paese, professione, azienda, aspettative e risposta sulla partecipazione precedente.
2. **Assenza social.** Quando non possiede Telegram o LinkedIn, allora può dichiararlo esplicitamente; un campo vuoto non equivale a una dichiarazione di assenza. I profili indicati rispettano `@username` e URL HTTPS LinkedIn.
3. **Provenienza.** Quando la persona vive in Italia, allora può cercare fra i comuni ISTAT e distinguere omonimi tramite provincia; per estero inserisce città e paese, mentre per un comune assente dichiara città e provincia senza regione automatica.
4. **Storico precedente.** Quando esiste una prenotazione confermata nell'edizione cronologicamente precedente, allora il dato è derivato come partecipazione positiva e se ne registra la fonte. In assenza di prova si chiede sì/no; l'assenza di storico non imposta “no”.
5. **Riuso account.** Quando l'email appartiene già a un account, allora l'invio pubblico non modifica profilo o telefono; per completare i dati la persona accede al proprio account.
6. **Completamento legacy.** Quando un account autenticato ha risposte mancanti, allora la pagina personale mostra un richiamo persistente e l'elenco dei campi incompleti. Può completarlo senza perdere o bloccare prenotazioni, liste d'attesa, pagamenti, consensi o disdetta.
7. **Correzione admin.** Quando un admin cerca un partecipante con o senza prenotazione, allora può consultare e correggere i contatti e il profilo dell'edizione; la correzione viene registrata nella cronologia.
8. **Separazione annuale e privacy.** Quando cambiano lingua o giorni selezionati, allora i campi compilati restano nel modulo. Risposte annuali sono legate all'edizione e non trasferiscono consensi; i dati legacy restano mancanti fino a una risposta esplicita.

## Modifiche proposte a `domain.md`

- Separare i contatti riutilizzabili (telefono, Telegram, LinkedIn) dalle risposte annuali città/paese, professione, azienda, aspettative e partecipazione precedente.
- Richiedere il profilo completo nei nuovi invii pubblici, inclusa la sola lista d'attesa; gli account già noti non vengono aggiornati in anonimo.
- Rappresentare la partecipazione precedente come dato derivato da una prenotazione confermata quando disponibile, altrimenti come dichiarazione esplicita.
- Il completamento autenticato non modifica prenotazioni, liste, quote, scadenze, consensi o stato di disdetta.

## Esclusioni

Mappa e aggregazioni geografiche, nuova accettazione privacy, campagne email e gestione operativa del ciclo di edizioni restano nei rispettivi MVP.
