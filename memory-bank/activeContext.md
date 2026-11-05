# Active context

## Ora

MVP 1-3 su `main` (PR #4). Aperti e non bloccanti: task 15 dell'MVP 1 (Google Sites) e task 9 dell'MVP 2 (infrastruttura Azure da validare). Fase B1 degli MVP 4, 5 e 6: spec scritte in `specs/mvp-04-lista-attesa/`, `specs/mvp-05-pranzi-cene/`, `specs/mvp-06-attivita-contributi/`, in attesa di conferma del maintainer. Nessun codice.

## Prossimo passo

1. Conferma delle tre spec e delle loro «Modifiche a domain.md».
2. Implementazione in ordine: MVP 4, poi 5, poi 6 (il 6 usa il calcolo unico dell'importo del 5).
3. Validazione del task 9 dell'MVP 2 quando il maintainer lo decide (serve anche al job orario che nell'MVP 4 promuove dalla lista).

## Scelte del maintainer per MVP 4-6 (2026-11-05)

- B0: l'MVP 4 non era fatto; il maintainer ha chiesto di pianificare 4, 5 e 6 insieme.
- MVP 4: lista d'attesa anche dal modulo pubblico, anche senza slot liberi; promozione su prenotazione confermata: resta confermata, saldo con la differenza.
- MVP 5: due prezzi (pranzo e cena); regime senza consenso, allergie e intolleranze con consenso specifico; pasti modificabili come gli slot.
- MVP 6: si aderisce a un'attività solo se presenti in quella fascia.

## Domande aperte MVP 4-6

- Importi di default di pranzo e cena (la spec usa segnaposto).
- MVP 4: l'email di promozione a chi è già confermato chiede la differenza senza una scadenza: va bene?
- MVP 4: la promozione dopo una scadenza arriva entro un'ora (job orario): va bene, o serve anche alla lettura?
- MVP 6: servono attività su tutto il giorno (escursioni)? Per ora nel Backlog.

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
