# Active context

## Ora

MVP 1 chiuso salvo il task 15 (verifica in Google Sites), aperto e non bloccante. MVP 2 e MVP 3 implementati sul branch `claude/magical-gauss-vbss2u` (backend 470 test, frontend 96 test, lint verdi, provati in browser da telefono). Aperto solo il task 9 dell'MVP 2: infrastruttura Azure (ACS, job orario) scritta ma mai validata.

## Prossimo passo

1. Passaggio su `main` quando il maintainer lo decide (decisione: tutto insieme a fine sviluppi, nessuna PR intermedia). Prima: CI su SQL Server sul branch, poi `az bicep build`, `what-if` e deploy per validare il task 9 dell'MVP 2 (vedi `infra/README.md`).
2. Prova con le descrizioni di PR per gli organizzatori: `specs/mvp-02-pagina-personale/pr-description.md` e `specs/mvp-03-pannello-admin/pr-description.md`.
3. MVP 4 (lista d'attesa), dopo il passaggio su `main`. Da chiarire prima: dettagli della priorità per chi porta un +1 (vedi Backlog).

## Spec degli MVP 7 e 8 (2026-11-05)

Scritte su richiesta del maintainer mentre gli MVP 4-6 sono in lavorazione altrove: `specs/mvp-07-inviti-report/` e `specs/mvp-08-stile-sito/`. Confermate.

- MVP 7: priorità a chi è stato invitato (+1), verificata dall'admin con una spunta; ordine calcolato alla promozione. Report di edizione a video, in stampa e in CSV. Il design si appoggia su ipotesi sugli MVP 4-6, da riallineare prima del task 1.
- MVP 8 (nuovo): grafica ripresa da https://sites.google.com/view/cissoneeventi/welcome. Colori, font (Montserrat) e loghi rilevati in `specs/mvp-08-stile-sito/stile.md`. Confermati: nome «Cissonauti Summer Camp», palette petrolio `#005C68` e ambra `#F4B400`, bottoni squadrati. Aperto: permesso della Pro Loco per i loghi (senza, l'intestazione mostra solo il nome).

Risposte del maintainer (2026-11-05), spec confermate:

- MVP 7: un +1 verificato non entra oltre il limite della lista; il report distingue confermate e in attesa di pagamento.
- MVP 8: nessuna modalità scura; dentro l'iframe intestazione ridotta (solo il nome, senza logo).

MVP 8 completato sul branch `claude/nifty-hawking-mgu6fa` (D-026), descrizione PR in `specs/mvp-08-stile-sito/pr-description.md`. Da provare nel sito Google vero dopo il deploy. Le pagine degli MVP 4-7 devono usare i token di `styles.css`, senza colori scritti a mano (lo controlla `theme.test.ts`).

Prossimo passo: MVP 7 dopo la chiusura degli MVP 4-6, riallineando prima le ipotesi del design.

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
