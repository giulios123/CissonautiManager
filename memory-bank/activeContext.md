# Active context

## Ora

MVP 1 chiuso salvo il task 15 (verifica in Google Sites), aperto e non bloccante. MVP 2 e MVP 3 implementati sul branch `claude/magical-gauss-vbss2u` (backend 470 test, frontend 96 test, lint verdi, provati in browser da telefono). Aperto solo il task 9 dell'MVP 2: infrastruttura Azure (ACS, job orario) scritta ma mai validata.

## Prossimo passo

1. MVP 2 e MVP 3 sono su `main` (PR #4). Il primo deploy è fallito per il provider `Microsoft.Communication` non registrato: il maintainer lo registra (`az provider register --namespace Microsoft.Communication --wait`), poi si rilancia il Deploy. Quando è verde si chiude il task 9 dell'MVP 2 e si fanno le prove manuali (email vera, job orario). Ogni nuovo errore di Azure sul Bicep, mai compilato prima, si corregge con una PR piccola.
2. Prova con le descrizioni di PR per gli organizzatori: `specs/mvp-02-pagina-personale/pr-description.md` e `specs/mvp-03-pannello-admin/pr-description.md`.
3. MVP 4 (lista d'attesa), dopo il passaggio su `main`. Da chiarire prima: dettagli della priorità per chi porta un +1 (vedi Backlog).

## Risolto il 2026-11-05 (conferma del maintainer)

- Spec 2 e 3 confermate, parte l'MVP 2.
- Disdetta senza pagamenti: la prenotazione si rimuove e basta. Con pagamenti: `disdetta_richiesta`.
- Giorni passati: il partecipante non può cambiare gli slot, solo l'admin.
- La proroga della scadenza resta nell'MVP 3; l'importo dovuto modificabile a mano resta nel Backlog.
- Modifiche a `domain.md` approvate (5 per l'MVP 2, 6 per l'MVP 3): si applicano in chiusura di ciascun MVP.

## Stato degli MVP 2 e 3

Sviluppo sul branch `claude/magical-gauss-vbss2u` (non `feat/...`, per il vincolo di push della sessione). Decisioni D-014 a D-019 (MVP 2) e D-020 a D-024 (MVP 3) in `decisions.md`; le modifiche a `domain.md` approvate sono applicate.

## Domande aperte

- MVP 3: l'admin non può cambiare a mano l'importo dovuto (sconti, organizzatori gratis): resta nel Backlog.
- MVP 3: se un admin cambia gli slot a una persona, a lei non parte nessuna email (Backlog).

- Il dominio gestito Azure può finire nella posta indesiderata: se succede, serve un dominio proprio (Backlog).
- La pagina pubblica di iscrizione permette di scegliere giorni già passati: bloccarli durante l'evento? (Backlog).

## Dubbi aperti ereditati

- Task 15: verifica dell'embed reale in Google Sites e chiusura dell'MVP 1.
- Finché il task 9 non è validato in produzione i magic link compaiono solo nei log (`EMAIL_PROVIDER=console`).
- Il database Basic non si mette in pausa; la Container App deve restare a `minReplicas: 0`.
- Da chiarire prima dell'MVP 5: serve la presenza di giorno per il pranzo?
- Esiti della call (D-008), sera derivata (D-009), nome con due s (D-012) e risorse ricreate (D-013): già registrati in `decisions.md`.
