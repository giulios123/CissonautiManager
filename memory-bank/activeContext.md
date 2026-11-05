# Active context

## Ora

MVP 1, Parte 1a completata sul branch `feat/mvp-01-iscrizione-base` (task 1-12 spuntati). Backend 173 test, frontend 33 test, lint verdi, provato end to end in locale.

## Prossimo passo

Task 13 (slot serale) fatto. Task 14 scritto (Bicep, workflow, README in `infra/`) ma da validare con un primo deploy: servono i passi di `infra/README.md` e i dati Azure. Il task 15 (verifica in Google Sites e chiusura) è in attesa: si sblocca dopo alcuni MVP. Il maintainer sta valutando Container Apps contro Static Web Apps con Functions (costi).

## Dubbi aperti

- La CI su SQL Server non è mai girata: al primo push può mostrare differenze tra SQLite e SQL Server da correggere.
- Il Dockerfile non è stato costruito in sessione (nessun daemon Docker).
- Per la 1b servono: abbonamento e resource group Azure, nome dell'app, dominio (o quello di default di Container Apps), mittente email per l'MVP 2.
- Chiarito: due slot diurni più la sera come terzo slot (default 19-24, senza limite).
- Da chiarire prima dell'MVP 5: serve la presenza di giorno per il pranzo?
- Conferma pagamento via email già nell'MVP 1 (assunto sì, non era stato risposto).
- In setup (task 14): ricordare al maintainer che la Container App deve scalare a zero. Il database Basic non si mette in pausa.
- Esiti della call decisi (D-008): due promemoria, magic link senza codice numerico, pranzi nell'app, MVP 7 ridotto, stack Azure.
- Deciso (D-009): la sera dell'intero giorno è una regola derivata, non si aggiunge alle prenotazioni.
- Task 14: Bicep, workflow di deploy e Dockerfile (migrazioni all'avvio) non sono mai stati eseguiti. Da verificare: `az bicep build`, `what-if`, build dell'immagine, primo deploy, `minReplicas: 0` e l'avvio da zero.
- Finché non c'è l'email reale (MVP 2) in produzione i magic link compaiono solo nei log.
- Deploy su Azure riuscito ma l'app non parte: il driver ODBC non caricava nel container (base Debian 13 contro repository Debian 12). Corretto nel Dockerfile con base Debian 12 e controllo in build, da verificare dopo il merge.
- Nome con due s (D-012): testi corretti; restano da decidere i nomi tecnici su Azure.
