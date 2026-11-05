# MVP 11 · Lingue e indirizzi · Requisiti

**Obiettivo**: l'app parla italiano e inglese, gli indirizzi sono in inglese e quelli italiani continuano a funzionare se scritti a mano.

## Storie

1. **Lingua dell'interfaccia**. Come visitatore voglio usare l'app in italiano o in inglese.
   - Quando apro l'app per la prima volta allora la lingua è quella del browser (`it*` → italiano, altrimenti inglese).
   - Quando premo IT o EN nel selettore dell'intestazione allora tutta l'interfaccia cambia subito e il browser se ne ricorda.
   - Quando l'indirizzo contiene `?lang=en` o `?lang=it` allora vale quella lingua (serve all'iframe di Google Sites).
   - Quando cambio lingua da loggato allora la scelta si salva sul mio profilo.
2. **Indirizzi in inglese**. Come visitatore voglio indirizzi leggibili in inglese.
   - Quando navigo l'app allora vedo `/register`, `/login`, `/login/verify`, `/me`, `/guide`, `/admin/days`, `/admin/to-collect`, ecc.
   - Quando scrivo a mano un indirizzo italiano (`/iscrizione`, `/accedi`, `/io`, `/admin/giorni`...) allora vengo portato all'equivalente inglese, con query e hash intatti.
   - Quando apro un vecchio magic link `/accedi/verifica?token=...` allora l'accesso funziona.
   - Quando il modulo `/iscrizione` è incorporato in Google Sites allora l'iframe continua a mostrarsi.
   - I link generati dall'app (menu, email, promemoria, redirect del login) sono sempre in inglese.
3. **Messaggi del server nella mia lingua**. Quando un'operazione fallisce allora l'errore arriva nella lingua della richiesta (`Accept-Language`).
4. **Email nella mia lingua**. Quando mi iscrivo allora la lingua scelta si salva e tutte le mie email (iscrizione, magic link, pagamento, promemoria, lista d'attesa, disdetta) partono in quella lingua. L'oggetto usa il nome dell'edizione.
5. **Pagine del partecipante tradotte**: home, iscrizione, accesso, verifica, pagina personale e componenti, stati, dialoghi.
6. **Guida partecipante in due lingue**: `frontend/src/guide/{it,en}/participant/` con le stesse sezioni.
7. **Date e importi** si leggono secondo la lingua (`10 luglio` / `10 July`, `12,00 €` / `€12.00`).
8. **Regola per il futuro**: ogni funzione nuova è bilingue (in `AGENTS.md`); un test confronta le chiavi dei dizionari e le sezioni della guida.

## Fuori scope

Traduzione dei contenuti scritti dall'admin (attività, istruzioni di pagamento, testi legali): Backlog. Pannello admin e guida admin: MVP 12.
