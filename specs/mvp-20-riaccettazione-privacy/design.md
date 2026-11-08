# MVP 20 · Design

## Dati e API

- Riutilizzare `ConsentEvent` aggiungendo la prova `kind=privacy`, `action=accepted`. Il registro rimane indipendente da booking e lista; per le importazioni legacy la lingua è `null`.
- Migrazione `0019` (dopo la migrazione profilo `0018`): importare le coppie documento/data ancora conservate su booking e lista, deduplicando prove con la stessa persona, edizione, documento e istante; creare `privacy_notice_attempt` con unicità per persona/edizione/documento.
- La prova valida è un evento esplicito riferito al documento privacy corrente. I campi storici su booking e lista restano snapshot dell'invio originale, non attestazioni delle versioni successive.
- `GET /api/me/privacy` restituisce documento corrente, stato pendente e storico con testi originali. `POST /api/me/privacy/accept` richiede documento, versione, `locale=it|en` e `accepted=true`.
- Una scrittura incompatibile con lo stato pendente risponde `428` con `code=privacy_acceptance_required`; un documento superato risponde `409`. Verificare l'accettazione nel backend su ogni API protetta.
- La reiscrizione anonima mantiene i comportamenti esistenti; gli account già presenti non ricevono una prova per la nuova versione dal modulo pubblico.

## Interfaccia, email e guide

- Pagina personale: testo corrente sempre leggibile, scelta esplicita, storico delle prove; il banner pendente disabilita le azioni limitate e resta visibile finché l'API conferma la nuova scelta.
- Se l'admin pubblica mentre la pagina è aperta, il server rifiuta le scritture stale; il client ricarica il documento alla risposta `428`, al ritorno della finestra e dopo un `409`.
- La scheda admin dei consensi mostra versione corrente, ultima versione accettata, stato e storico. L'editor legale avvisa che pubblicare una versione richiede nuova accettazione.
- Lavorare nel job orario già esistente. Filtrare prenotazioni confermate/in attesa valide e voci aperte di lista, controllare di nuovo versione e accettazione, reclamare l'unico tentativo prima dell'invio. Email IT/EN con nome edizione, versione e link `/login?lang=...`; nessuna accettazione dal link e nessun dato di prenotazione.
- Aggiungere testi UI, messaggi server, email e guida partecipante/amministratori in entrambe le lingue. La validazione dei testi legali definitivi resta prerequisito del rilascio reale.
