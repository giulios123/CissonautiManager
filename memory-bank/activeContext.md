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

## Domande aperte

- MVP 2: una prenotazione senza pagamenti che si disdice passa comunque a `disdetta_richiesta` (e l'admin la chiude) o a uno stato finale diretto? Nella spec passa a `disdetta_richiesta`.
- MVP 2: va bene bloccare la modifica degli slot di giorni già passati?
- MVP 3: l'admin può modificare a mano l'importo dovuto (sconti, organizzatori gratis)? Per ora nel Backlog.
- MVP 3: la proroga della scadenza del blocco resta qui?
- Le sezioni «Modifiche a domain.md» delle due spec (4 voci per l'MVP 2, 6 per l'MVP 3) vanno approvate prima di toccare `domain.md`.

## Dubbi aperti ereditati

- Task 15: verifica dell'embed reale in Google Sites e chiusura dell'MVP 1.
- Finché non c'è l'email reale (MVP 2) in produzione i magic link compaiono solo nei log.
- Il database Basic non si mette in pausa; la Container App deve restare a `minReplicas: 0`.
- Da chiarire prima dell'MVP 5: serve la presenza di giorno per il pranzo?
- Esiti della call (D-008), sera derivata (D-009), nome con due s (D-012) e risorse ricreate (D-013): già registrati in `decisions.md`.
