# MVP 30 · Consegne dei benefit

**Stato:** spec confermata il 2026-11-11 e implementata sul branch `feat/mvp-30-consegne-benefit` (sopra il 29), 6 task completati. Restano CI SQL Server, prova visiva e collaudo organizzatori. Nessun deploy. P3, C5. Origine: [US-C5](../revisione-2026-11-07/c-attivita-logistica/requirements.md), Q-C3 e le risposte del 2026-11-11 (D-120, D-121). Riusa il catalogo dei benefit dell'MVP 23 (`Benefit`, già in Impostazioni) e le categorie e esenzioni dell'MVP 25c. Una migrazione additiva (`0029`, dopo la `0028` dell'MVP 29; se il 29 non è ancora fatto, il numero successivo alla testa).

## US-30.1 · Chi ha diritto ai benefit (D-121)

Ha diritto una persona con un'iscrizione **attiva** (in attesa di pagamento o confermata, non scaduta né disdetta né rimborsata) nell'edizione corrente **e** almeno una di queste condizioni:

1. la categoria è «interno non pagante» (es. speaker);
2. la quota è esentata dall'admin (`fee_exempt`), anche se la categoria resta «ordinaria»;
3. il **versato netto** (pagamenti validi meno rimborsi, MVP 25c) copre almeno la **quota base** dell'edizione (non base più giorni).

- Quando la quota base è 0, allora la condizione 3 **non** vale da sola (altrimenti avrebbero diritto tutti): servono le condizioni 1 o 2.
- Quando la persona è solo in lista d'attesa, scaduta, disdetta, rimborsata, oppure è un esterno senza account, allora non ha diritto per il solo fatto di comparire nei conteggi.
- Quando cambia la quota base dell'edizione, allora il diritto si ricalcola alla lettura successiva; nulla viene riscritto.
- Questa soglia è **distinta** dalla conferma del posto (quota base + giorni, MVP 18): non si usa lo stato «confermata» come scorciatoia.

## US-30.2 · La pagina «Consegne»

- Quando un admin apre «Consegne» dal menu, allora sceglie un benefit tra quelli **non ritirati** del catalogo e vede l'elenco delle persone con diritto, con nome, categoria e stato per quel benefit («Da consegnare», «Consegnato il … da …», «Annullata»).
- Quando non ci sono benefit nel catalogo, allora la pagina spiega come aggiungerli in Impostazioni; nessuna consegna fittizia.
- Quando cerco per nome o cognome, allora l'elenco si restringe; con il filtro «Da consegnare / Consegnati / Tutti» e i contatori per benefit (consegnati su aventi diritto) in vista.
- Quando il catalogo di una vecchia edizione non aveva benefit, allora non compaiono consegne per quella edizione; catalogo e consegne **non** si copiano alla nuova edizione.
- L'elenco mostra solo nome, categoria e link alla scheda: nessuna email, telefono, allergia o importo.

## US-30.3 · Segnare una consegna

- Quando premo «Consegna» su una persona, allora si registrano persona, benefit, edizione, autore e data/ora, e la riga passa a «Consegnato».
- Quando premo due volte (o il browser ripete la richiesta), allora la consegna è **una sola**.
- Quando una consegna attiva esiste già per quella persona e quel benefit (anche registrata da un altro admin in contemporanea), allora la seconda richiesta non ne crea un'altra e la riga mostra quella esistente: **una sola consegna attiva per persona e benefit** (D-120).
- Quando la persona non ha diritto o il benefit è ritirato, allora la consegna è rifiutata (422) con un messaggio chiaro.

## US-30.4 · Correggere un errore

- Quando una consegna è sbagliata, allora l'admin la **annulla con un motivo** (obbligatorio, breve): la consegna resta in storico come annullata con autore, data e motivo; non viene cancellata.
- Quando una consegna è annullata, allora la persona torna «Da consegnare» e si può registrare una nuova consegna; lo storico mostra entrambe.
- Quando l'annullo si ripete, allora non cambia nulla e non si duplica la cronologia.

## US-30.5 · Diritto perso dopo la consegna

- Quando una persona con consegna attiva perde il diritto (disdetta, nuova categoria, esenzione tolta, versamento rimborsato), allora la consegna **resta** e compare ancora nell'elenco, marcata «Senza diritto attuale». Nessuna cancellazione automatica e nessuna restituzione tracciata (D-120).
- Quando riottiene il diritto, allora la marcatura sparisce.
- Quando una persona senza diritto ha solo consegne annullate, allora non compare nell'elenco principale (resta nello storico della consegna).

## US-30.6 · Benefit ritirati e storico

- Quando un benefit è ritirato dal catalogo, allora non si possono registrare nuove consegne, ma lo storico delle consegne passate resta leggibile e annullabile.
- Quando il catalogo cambia nome a un benefit, allora lo storico mostra il nome attuale.
- La consegna è legata a persona, benefit ed edizione, **non alla prenotazione**: sopravvive se la prenotazione viene rimossa.

## US-30.7 · Accessi e privacy

- Solo gli admin leggono e scrivono consegne (401/403 per gli altri). Nessun partecipante vede consegne, diritti o catalogo di consegna; la pagina personale, le email, la guida partecipante e gli export dei partecipanti non cambiano.
- Ogni consegna e annullo lascia una voce di cronologia (`AuditLog`) con autore, persona e benefit.
- Il CSV dell'elenco (stessi filtri) è riservato agli admin.

## US-30.8 · Accessibilità e lingue

- Sul telefono: scelta del benefit, ricerca e un pulsante «Consegna» da almeno 44 px per riga; stato espresso a parole, non solo a colore; focus visibile; dialogo di annullo con focus sul motivo e Esc che chiude.
- Testi IT/EN in `frontend/src/i18n/{it,en}.ts`, messaggi del server in `backend/app/i18n.py`, nomi dei benefit nella lingua dell'admin (campi `name_it`/`name_en` già esistenti), guida admin IT/EN, CSV con intestazioni per lingua.

## Fuori scope

Quantità multiple per benefit, scorte e acquisti, restituzioni tracciate, consegne agli esterni, auto-registrazione da parte del partecipante, copia del catalogo alla nuova edizione, notifiche. (Nel Backlog.)

## Modifiche a domain.md (proposta, non applicata)

- Benefit: hanno diritto gli iscritti attivi che sono interni non paganti, con quota esentata o con la quota base coperta dal versato netto; una sola consegna attiva per persona e benefit, correggibile con annullo motivato; la consegna resta anche se il diritto si perde; esterni e sola lista esclusi.
