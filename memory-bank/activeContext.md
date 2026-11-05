# Active context

## Ora

MVP 1 chiuso salvo il task 15 (verifica in Google Sites), aperto e non bloccante. MVP 2 e MVP 3 su `main` e deployati su Azure (PR #4 e #5, task 9 dell'MVP 2 validato): `https://cissonauti-booking.wonderfulbush-cbda30f0.italynorth.azurecontainerapps.io`. MVP 4, 5 e 6 implementati e provati in locale sul branch `claude/quirky-meitner-qn9hwh`, in PR verso `main`; descrizioni per gli organizzatori in `specs/mvp-0{4,5,6}-*/pr-description.md`. Modifiche a `domain.md` dei tre MVP applicate.

## Prossimo passo

1. CI della PR, in particolare SQL Server con le migrazioni 0005-0007 da zero.
2. Dopo il merge il deploy applica le migrazioni 0005-0007 all'avvio: il primo avvio a freddo può essere lento (circa 4 minuti con la PR #5).
3. Prove manuali in produzione con le checklist di MVP 2-6: email vera nella casella e fuori dallo spam, il job `cissonauti-booking-reminders` che gira ogni ora (portale Azure, «Execution history»), viste e CSV con dati veri, lista d'attesa che si sblocca dopo una scadenza.
4. MVP 7 (inviti e report): la priorità del +1 si innesta in `domain/waitlist.queue`; da definire come si verifica il +1 (Backlog).
5. Importi definitivi di pranzo e cena (oggi 8 € e 12 €, segnaposto).

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
