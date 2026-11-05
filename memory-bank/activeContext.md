# Active context

## Ora

MVP 1 chiuso salvo il task 15 (verifica in Google Sites), aperto e non bloccante. Il task 14 è validato: deploy Azure riuscito e login funzionante. Spec degli MVP 2 e 3 scritte (fase B1), in attesa della conferma del maintainer.

## Prossimo passo

1. Conferma delle spec in `specs/mvp-02-pagina-personale/` e `specs/mvp-03-pannello-admin/` (domande aperte sotto).
2. MVP 2 (10 task), branch `feat/mvp-02-pagina-personale`.
3. MVP 3 (13 task), branch `feat/mvp-03-pannello-admin`, dopo la chiusura dell'MVP 2.

## Scelte già prese per le spec

- Promemoria da un Container Apps Job orario (non da GitHub Actions).
- Email da dominio gestito Azure (ACS), con passaggio a dominio proprio come evoluzione.
- Prenotazione confermata che aggiunge giorni: resta confermata, il saldo mostra la differenza.
- MVP 3 resta unico (13 task, sopra la soglia di circa 10): punto di taglio naturale dopo il task 7.

## Risolto il 2026-11-05 (conferma del maintainer)

- Spec 2 e 3 confermate, parte l'MVP 2.
- Disdetta senza pagamenti: la prenotazione si rimuove e basta. Con pagamenti: `disdetta_richiesta`.
- Giorni passati: il partecipante non può cambiare gli slot, solo l'admin.
- La proroga della scadenza resta nell'MVP 3; l'importo dovuto modificabile a mano resta nel Backlog.
- Modifiche a `domain.md` approvate (5 per l'MVP 2, 6 per l'MVP 3): si applicano in chiusura di ciascun MVP.

## Stato dell'MVP 2

In corso, task 1 (migrazione 0003) fatto. Sviluppo sul branch `claude/magical-gauss-vbss2u` (non `feat/mvp-02-...`, per il vincolo di push della sessione).

## Domande aperte

## Dubbi aperti ereditati

- Task 15: verifica dell'embed reale in Google Sites e chiusura dell'MVP 1.
- Finché non c'è l'email reale (MVP 2) in produzione i magic link compaiono solo nei log.
- Il database Basic non si mette in pausa; la Container App deve restare a `minReplicas: 0`.
- Da chiarire prima dell'MVP 5: serve la presenza di giorno per il pranzo?
- Esiti della call (D-008), sera derivata (D-009), nome con due s (D-012) e risorse ricreate (D-013): già registrati in `decisions.md`.
