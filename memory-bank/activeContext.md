# Active context

## Ora

MVP 1 chiuso salvo il task 15 (verifica in Google Sites), aperto e non bloccante. MVP 2 implementato sul branch `claude/magical-gauss-vbss2u` (task 1-8 e 10; backend 262 test, frontend 49 test, lint verdi, provato in browser da telefono). Resta il task 9: infrastruttura Azure (ACS, job orario) scritta ma mai validata.

## Prossimo passo

1. Il maintainer valida il task 9: `az bicep build`, `what-if`, deploy, poi controlla l'email vera e l'esecuzione oraria del job (vedi `infra/README.md`).
2. Revisione della PR dell'MVP 2 con la checklist in `specs/mvp-02-pagina-personale/pr-description.md`.
3. MVP 3 (13 task, `specs/mvp-03-pannello-admin/`): parte dopo la chiusura dell'MVP 2. Le sue modifiche a `domain.md` sono approvate e si applicano alla chiusura.

## Scelte già prese per le spec

- MVP 3 resta unico (13 task, sopra la soglia di circa 10): punto di taglio naturale dopo il task 7.

## Risolto il 2026-11-05 (conferma del maintainer)

- Spec 2 e 3 confermate, parte l'MVP 2.
- Disdetta senza pagamenti: la prenotazione si rimuove e basta. Con pagamenti: `disdetta_richiesta`.
- Giorni passati: il partecipante non può cambiare gli slot, solo l'admin.
- La proroga della scadenza resta nell'MVP 3; l'importo dovuto modificabile a mano resta nel Backlog.
- Modifiche a `domain.md` approvate (5 per l'MVP 2, 6 per l'MVP 3): si applicano in chiusura di ciascun MVP.

## Stato dell'MVP 2

Sviluppo sul branch `claude/magical-gauss-vbss2u` (non `feat/mvp-02-...`, per il vincolo di push della sessione). Decisioni D-014 a D-019 in `decisions.md`; le 5 modifiche approvate sono già in `domain.md`.

## Domande aperte

- Il dominio gestito Azure può finire nella posta indesiderata: se succede, serve un dominio proprio (Backlog).
- La pagina pubblica di iscrizione permette di scegliere giorni già passati: bloccarli durante l'evento? (Backlog).

## Dubbi aperti ereditati

- Task 15: verifica dell'embed reale in Google Sites e chiusura dell'MVP 1.
- Finché il task 9 non è validato in produzione i magic link compaiono solo nei log (`EMAIL_PROVIDER=console`).
- Il database Basic non si mette in pausa; la Container App deve restare a `minReplicas: 0`.
- Da chiarire prima dell'MVP 5: serve la presenza di giorno per il pranzo?
- Esiti della call (D-008), sera derivata (D-009), nome con due s (D-012) e risorse ricreate (D-013): già registrati in `decisions.md`.
