# Progress

## Stato degli MVP

| MVP | Nome | Stato |
|-----|------|-------|
| 0 | Bootstrap (Memory Bank, AGENTS.md, roadmap, spec MVP 1) | fatto |
| 1 | Iscrizione base | fatto salvo il task 15 (verifica in Google Sites e chiusura), aperto e non bloccante |
| 2 | Pagina personale | codice fatto e provato in locale (task 1-8), infrastruttura Azure scritta ma non validata (task 9), chiusura documentale fatta (task 10) |
| 3 | Pannello admin completo | codice fatto e provato in locale (task 1-12), chiusura documentale fatta (task 13); si porta su `main` insieme al task 9 dell'MVP 2 |
| 4 | Lista d'attesa | codice fatto e provato in locale (task 1-9) |
| 5 | Pranzi e cene | codice fatto e provato in locale (task 1-10) |
| 6 | Attività e contributi | da fare |
| 7 | Inviti e report | da fare |

## Verifiche manuali

- **Bootstrap**: struttura del repo conforme alla Parte A; nessun codice applicativo. Nessuna verifica manuale funzionale prevista.

- **MVP 1a**, provato end to end in locale con browser (DB nuovo da migrazioni): login admin con password, creazione edizione e testi legali, iscrizione da telefono (10 € + 2 giorni = 12 €), magic link dall'email in console, pagina personale, registrazione pagamento con conferma, cookie httpOnly/Lax di 14 giorni, header CSP.
- **Slot serale (task 13)**: provato in browser su DB nuovo da migrazioni 0001 e 0002; la sera si prenota senza limite di posti e la sola sera costa 11 €.
- **CI su SQL Server**: ha trovato 4 problemi che SQLite nascondeva (D-011), tutti corretti. Immagine Docker: costruita dalla CI.
- **Deploy Azure (task 14)**: chiuso con successo dal maintainer, l'app parte su Container Apps e il login funziona.
- **Non verificato**: embed reale in Google Sites (task 15), email reali (MVP 2).

- **MVP 2**, provato end to end in locale con browser da telefono (DB nuovo da migrazioni, edizione 3-9 novembre con email in console): iscrizione dal modulo pubblico, magic link, cambio slot con anteprima della quota (12 € a 13 €), giorni passati bloccati e oggi modificabile, selezione vuota rifiutata, dialogo di disdetta (focus sul tasto sicuro, Esc lo chiude e riporta il focus), disdetta senza pagamenti con email e prenotazione rimossa. Il job `python -m app.jobs.send_reminders` parte da riga di comando su un database migrato.
- **Non verificato (MVP 2)**: `az bicep build`, `what-if` e primo deploy con ACS e job (task 9); email vere nella casella e fuori dalla posta indesiderata; il job che gira davvero ogni ora con l'app a zero repliche; disdetta con pagamenti provata solo nei test automatici.

- **MVP 3**, provato end to end in locale con browser da telefono (DB nuovo da migrazioni, edizione 3-9 novembre, tre iscritti con pagamenti diversi): voci del pannello; elenco Persone con telefono e sere e CSV scaricato (BOM, `;`, importi con la virgola, fuso di Roma); «Giorni e slot» con la sera dell'intero giorno marcata; «Settimana» con totale delle persone diverse; «Da verificare» con credito e pagamento parziale; aggiunta di un admin nuovo e rimozione con dialogo di conferma (focus sul tasto sicuro); admin attuale non rimovibile con spiegazione; proroga del blocco letta in ora di Roma; modifica dati e di slot (anche un giorno passato) con cronologia; annullamento di un pagamento che riporta la prenotazione in attesa; disdetta a nome della persona e rimborso (parte dall'importo versato); «Da verificare» che si svuota da sola.
- **Non verificato (MVP 3)**: CI su SQL Server (le query nuove sono semplici, ma la CI non è ancora girata sul branch); apertura dei CSV in Excel o Numbers veri (provato solo il contenuto dei file); uso con molti iscritti.
- **MVP 4**, provato end to end in locale con browser da telefono (DB nuovo da migrazioni 0001-0005, capienza 1 e lista al 100%): Ada prende l'ultimo posto; Bea trova lo slot «completo, spunta per entrare in lista», si iscrive solo in lista (nessuna quota), riceve l'email e vede «1° in lista» nella pagina personale; Ada disdice e Bea riceve «Si è liberato un posto» con quota, causale e scadenza, e la sua pagina mostra la prenotazione in attesa; pannello con «Persone», «Giorni e slot» e percentuale nelle Impostazioni. Downgrade e upgrade della 0005 senza errori.
- **Non verificato (MVP 4)**: CI su SQL Server; promozione dopo una scadenza con il job che gira davvero su Azure; due promozioni concorrenti sullo stesso slot (lock provato solo su SQLite); email vere.
- **MVP 5**, provato end to end in locale con browser da telefono (DB nuovo da migrazioni 0001-0006, prezzi 8 € e 12 €, consenso sanitario pubblicato): il modulo pubblico non chiede i pasti; dalla pagina personale pranzo e cena di lunedì con anteprima (11 € → 31 €); allergie rifiutate senza consenso e salvate con il consenso; togliendo la sera cade la cena con avviso; vista «Pasti» con regimi, allergie e CSV; colonne Pranzi e Cene in «Settimana». Downgrade e upgrade della 0006 senza errori.
- **Non verificato (MVP 5)**: CI su SQL Server; CSV dei pasti aperto in Excel vero; importi definitivi dei pasti.
- **B0**: l'MVP 2 non è completo (task 9 aperto). Il maintainer ha chiesto di procedere e di validare tutto insieme al passaggio su `main`.

## Bug corretti fuori MVP

- 2026-11-04: nel riepilogo e nelle email il pomeriggio compariva prima della mattina (ordinamento per nome del periodo). Corretto ordinando per orario di inizio, con test di regressione.
