# Active context

## Ora

MVP 4 (lista d'attesa) e MVP 5 (pranzi e cene) implementati e provati in locale sul branch `claude/quirky-meitner-qn9hwh`; descrizioni PR in `specs/mvp-04-lista-attesa/pr-description.md` e `specs/mvp-05-pranzi-cene/pr-description.md`. Modifiche a `domain.md` di entrambi applicate. Aperti e non bloccanti: task 15 dell'MVP 1 e task 9 dell'MVP 2.

## Prossimo passo

1. MVP 6 (attività e contributi), spec già confermata: usa `recompute_amount` e la regola «cade se perdi il titolo» dei pasti.
2. CI su SQL Server sul branch (migrazioni 0005 e 0006 mai girate su SQL Server) e validazione del task 9 dell'MVP 2.
3. Importi definitivi di pranzo e cena (oggi 8 € e 12 €, segnaposto).

## Scelte del maintainer per MVP 4-6 (2026-11-05)

- B0: l'MVP 4 non era fatto; il maintainer ha chiesto di pianificare 4, 5 e 6 insieme.
- MVP 4: lista d'attesa anche dal modulo pubblico, anche senza slot liberi; promozione su prenotazione confermata: resta confermata, saldo con la differenza.
- MVP 5: due prezzi (pranzo e cena); regime senza consenso, allergie e intolleranze con consenso specifico; pasti modificabili come gli slot.
- MVP 6: si aderisce a un'attività solo se presenti in quella fascia.

## Risposte del maintainer su MVP 4-6

- Prezzi di pranzo e cena: segnaposto (8 € e 12 €) finché non ci sono gli importi definitivi.
- Email di promozione ai confermati senza scadenza: va bene.
- Promozione dopo una scadenza entro un'ora con il job orario: va bene.
- Pranzo con mattina o pomeriggio: confermato.
- Attività su tutto il giorno: restano nel Backlog.

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
- Presenza di giorno per il pranzo: la spec dell'MVP 5 propone mattina o pomeriggio (da confermare).
- Esiti della call (D-008), sera derivata (D-009), nome con due s (D-012) e risorse ricreate (D-013): già registrati in `decisions.md`.
