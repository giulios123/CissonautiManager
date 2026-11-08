# Design · MVP 19

## Modello e migrazione

Migrazione additiva 0018 dopo la 0017: `participant.telegram` e `participant.linkedin` nullable; `participant_edition_profile` con chiave univoca persona/edizione, città, provincia/regione opzionali, paese, codice ISTAT opzionale, professione, azienda, aspettative, partecipazione precedente, fonte (`derived`, `declared` o `admin`) e riferimento alla precedente edizione. I record legacy non vengono backfillati. Dati geografici locali versionati in `backend/app/assets/municipalities.json` e catalogo ISO paesi locale; le ricerche non escono dall'app.

## Interfacce

- `POST /api/public/registrations`: i nuovi campi sono obbligatori anche per la sola lista; creazione account, profilo per edizione, iscrizione/lista e consensi resta atomica. Per email già note il percorso pubblico resta login-link only.
- `GET /api/public/municipalities?q=...` e `GET /api/public/countries`: cataloghi locali, senza geoservizi terzi.
- `GET/PUT /api/me/profile`: autenticazione obbligatoria; ritorna campi propri, campi mancanti e completezza del profilo dell'edizione attiva. Il PUT richiede il set completo.
- `GET/PUT /api/admin/participants/{id}/profile`: accesso admin, anche senza booking. La scrittura aggiunge evento alla cronologia.
- Pagina personale: avviso non bloccante e modulo precompilato. Scheda admin: profilo per edizione e correzione.

## Regole

La presenza confermata in una prenotazione dell'edizione precedente prevale sul valore dichiarato e viene marcata come `derived`; senza tale prova si conserva la risposta della persona come `declared`. L'assenza di edizioni precedenti non equivale a risposta negativa. Codice ISTAT, comune e provincia sono validati insieme; la città fuori elenco resta testo libero e non acquisisce una regione presunta. Nessun flusso profilo modifica record di prenotazione, quote, pagamenti o consensi.

## Fonti dati e attribuzione

Il catalogo comunale è uno snapshot locale dell'elenco ISTAT, distribuito tramite mirror sincronizzato dal permalink ufficiale [Elenco dei comuni italiani](https://www.istat.it/storage/codici-unita-amministrative/Elenco-comuni-italiani.xlsx), snapshot del 2 novembre 2026. Il catalogo paesi deriva da iso-codes 4.18.0 e ISO 3166-1, licenza LGPL-2.1-or-later. Fonte, snapshot e licenza sono riportati anche in `backend/app/assets/NOTICE.md`. Nessuna query utente è inviata a tali fonti.

## Modifiche a `domain.md`

Le regole proposte sono elencate in `requirements.md` e applicate con l'implementazione del MVP 19.
