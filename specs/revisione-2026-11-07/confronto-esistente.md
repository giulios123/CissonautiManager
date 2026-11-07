# Confronto con il progetto esistente

Ispezione statica del checkout al 7 novembre 2026; nessuna interrogazione dei dati o della configurazione di produzione. Le vecchie specifiche restano storiche; le differenze sotto sono sul codice attuale, mentre le risposte del maintainer sono già recepite nelle spec e nel registro D-076–D-104. Non sono differenze da chiedere nuovamente né funzioni già implementate.

| Requisito | Riscontro nel repository | Differenza da specificare |
|---|---|---|
| A1–A2 | `api/public.py:RegistrationIn` richiede già privacy e scarico; `models.py:LegalDocument` è versionato. Consenso sanitario separato sulla prenotazione. | Mancano presenza e foto/video, gestione/revoca e tracciamento anche per chi è solo in lista. Non duplicare privacy, scarico o consenso sanitario. |
| A3 | `Participant.invited_by` è testo libero; verifica +1 admin già presente, MVP 7. Non trovata una lista nominale pubblica negli endpoint pubblici. | Conservare il testo libero. Il consenso A2 non autorizza automaticamente una nuova lista pubblica: visibilità soltanto autenticata, ora chiarita dal maintainer. |
| A3 / vincolo dati | `public.py` restituisce un riepilogo al nuovo invio; per email già attiva risponde `already_registered` senza scheda. D-005 accetta l'informazione sull'esistenza dell'iscrizione. | Confermata l'eccezione attuale D-005 per email già nota; scartata la risposta neutra proposta, senza esporre altri dati preesistenti né rivedere i magic link. |
| A4 | Telefono obbligatorio nei nuovi invii già nell'MVP 16; colonna nullable per dati precedenti. Nome, cognome, email, invitante e `can_bring` già esistono. | Gli altri sei punti mancano: risposte obbligatorie, città da elenco, profili assenti dichiarabili e completamento legacy non bloccante. Telefono e altri campi obbligatori attuali restano; niente invalidazione dei dati storici. |
| A5 | `services/edition.py:publish_legal_document` crea una versione; booking e waitlist conservano documento e data. `/api/me` espone il testo sanitario, non una richiesta di riaccettazione privacy. | Versionamento presente; mancano richiesta di nuova accettazione anche email e corpi IT/EN della stessa versione. Storico append-only senza sovrascrivere prove precedenti. |
| A6 | `request_cancellation` cancella booking senza righe di pagamento; con righe, anche annullate, passa a disdetta. `AuditLog` conserva solo azioni admin e può perdere il collegamento al booking rimosso. `audit.history` filtra per booking. | La disdetta autonoma non lascia una voce amministrativa; una voce scollegata non è consultabile dalla normale scheda rimossa. Contraddice la perdita di traccia accettata in D-018; integrare D-022/D-025 senza perdere consensi. Solo procedura manuale per A6. |
| A7 | Provenienza strutturata e mappa assenti. | Bozza e proposta grafica; soglia minima 5 confermata, insieme/base e casi geografici residui da definire. |
| B1–B2 | `services/payments.py`, `booking_changes.py`, `meals.py`, `activities.py`, `pricing.py` e `waitlist.py` usano il totale per confermare; `amount_due_cents` comprende extra organizzazione. | Separare soglia di conferma e saldo totale in tutti i percorsi, compresi annullo e promemoria. D-017/D-021/D-049 vanno riallineate per la parte relativa alla copertura. |
| B3 | MVP 10: un clic sul saldo, annullo 10 secondi, email differita 30 secondi; «Altro importo» porta alla scheda. | Modale sullo stesso elenco, con identiche garanzie. Non ricreare un registro pagamenti. |
| B4 | Quote base/giornaliera, prezzi pranzo/cena e `MealSetting` per pagamento al fornitore già presenti. Nessuna politica dei pasti compresi. | Nuova politica di inclusione e quantità; «primo pranzo O prima cena» deve essere deterministico. Conflitto con il vecchio totale che addebita ogni pasto organizzazione. |
| B5 | MVP 16 / D-049 distinguono `organizer` e `provider`, senza registrare incassi del fornitore. IT contiene «Organizzatori (incluso nella quota)». | Le modalità tecniche esistono: correggere terminologia e distinguere destinatario, costo e inclusione. Non introdurre un terzo tipo né trattare gli extra come gratuiti. |
| C1 | `ActivityOffer` espone già titolo, descrizione, orari e costi; `ActivityView` titolo, etichetta e orario. | Assicurare dettagli completi e titoli leggibili in ogni riepilogo; non assumere assenza del dato nel modello. |
| C2 | Partecipante/account e booking; niente categorie logistiche esterne. MVP 5/6 impongono presenza per aderire. | Esterni senza account né coworking ma occupanti capienza, con incassi organizzazione separati; iscritti non paganti con esenzioni mirate. Questa precisazione aggiorna il precedente vincolo di esclusione economica indistinta. |
| C3–C5 | Descrizione attività pubblicabile agli iscritti; contributi legati al booking; benefit assenti. | Note admin separate dalla descrizione; conversione guidata senza calendario automatico; catalogo e consegne benefit per edizione. |
| D1–D3 | `AdminWeek.tsx` mostra conteggi statici, in ordine data; dati aggregati già presenti. | Dettagli in modale e successivo ordinamento corrente/futuri/passati al ritorno alla pagina. Calendario a box accantonato dal maintainer. D-038 non prescrive più il vecchio riepilogo basso su telefono: correzione 7 novembre e E1 prevalgono. |
| D4–D5 | Promemoria già in `jobs/send_reminders.py` e `infra/main.bicep`; testi personalizzabili MVP 14. Nessuna integrazione tratto.email trovata. | [Riscontro D5](d-admin-comunicazioni/promemoria-esistenti.md); D4 rimane una bozza di invio per gruppi, senza integrazione. |
| E1–E2 | `.registration-toolbar` è già sticky con offset sotto l'header; `.summary` laterale non è sticky. | Migliorare evidenza, rendere bianco il riquadro e marcare la striscia. Non ripristinare la vecchia barra inferiore di D-038. |
| E3 | `/api/me` mostra solo contributi propri; vista di tutti protetta da ruolo admin; tipi `talk`, `topic`, `skill`. | Nuova lettura autenticata di sole proposte attive: nome con consenso, proposta anonima altrimenti; nuovo tipo richieste competenza, nessuna API admin aperta ai partecipanti. |
| F | `Edition` esiste e molte tabelle sono già collegate; servizi e viste selezionano l'attiva, account e audit non sempre isolati. | Multi-edizione resta non implementata; scelta stesso DB/una aperta confermata, chiusura da Impostazioni e archivio admin attuali/precedenti, obiettivo prima prossimo evento se fattibile. |

## Documenti storici da non confondere con lo stato corrente

`projectbrief.md` riportava ancora «UI solo in italiano»: riallineato per riferimento alla regola bilingue già approvata. Le spec MVP 5/6 parlano di prezzi immutabili o ricalcolati solo in seguito: la successiva D-049 / MVP 16 consente già modifiche e ricalcolo delle prenotazioni attive. Non riproporre quelle funzioni come nuove. La numerazione doppia MVP 15 esiste già: i nuovi rilasci proposti iniziano dal 17 senza rinumerare lo storico.

## Confini da segnalare

- D2 richiede una finestra di rilascio lontana dalle demo; nessuna data inventata.
- D3 è accantonato; C4 non autorizza generazione automatica del calendario o wall fisico dello scambio.
- D4 non autorizza invii reali o configurazione di tratto.email.
- F non autorizza reset, export dei dati reali o nuovi deploy.
- Domini, hosting always-on e revisione del magic link admin restano fuori ambito.
