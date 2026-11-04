# Active context

## Ora

MVP 1, Parte 1a completata sul branch `feat/mvp-01-iscrizione-base` (task 1-12 spuntati). Backend 173 test, frontend 33 test, lint verdi, provato end to end in locale.

## Prossimo passo

Task 13 (slot serale, deciso il 2026-11-04, vedi D-006), poi Parte 1b (task 14-15): Bicep, deploy su Azure, prova dentro Google Sites. Il maintainer sta valutando Container Apps contro Static Web Apps con Functions (costi).

## Dubbi aperti

- La CI su SQL Server non è mai girata: al primo push può mostrare differenze tra SQLite e SQL Server da correggere.
- Il Dockerfile non è stato costruito in sessione (nessun daemon Docker).
- Per la 1b servono: abbonamento e resource group Azure, nome dell'app, dominio (o quello di default di Container Apps), mittente email per l'MVP 2.
- Chiarito: due slot diurni più la sera come terzo slot (default 19-24, senza limite).
- Da chiarire prima dell'MVP 5: serve la presenza di giorno per il pranzo?
- Conferma pagamento via email già nell'MVP 1 (assunto sì, non era stato risposto).
- In setup (task 14): ricordare al maintainer che la Container App deve scalare a zero. Il database Basic non si mette in pausa.
- Esiti della call decisi (D-008): due promemoria, magic link senza codice numerico, pranzi nell'app, MVP 7 ridotto, stack Azure.
- Da decidere al task 13: la sera di chi prenota l'intero giorno si aggiunge alle prenotazioni o si considera solo per la cena.
