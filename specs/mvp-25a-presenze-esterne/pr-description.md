# MVP 25a · Presenze esterne

## Descrizione

Gli organizzatori possono aggiungere **esterni**: persone senza account che partecipano a pasti e attività (accompagnatori, ospiti, relatori). Un esterno ha nome, cognome e «pagante / non pagante»; non ha prenotazione, email né slot di coworking. Può prendere qualsiasi pranzo o cena dei giorni dell'edizione, anche passati, e occupa un posto della capienza delle attività (si supera il limite solo con «Forza oltre la capienza»).

Gli esterni compaiono in **Pasti**, **Settimana**, **Attività** e **Report** come persone distinte, con l'etichetta «Esterno» e una colonna «Di cui esterni». In questa versione **non generano importi**: gli incassi sono l'MVP 25b. Le allergie si salvano solo con la spunta «consenso raccolto dalla persona» e sono visibili solo agli organizzatori.

Migrazione additiva `0024_external_guests` (tre tabelle nuove, nessun dato esistente modificato). Testi e guida in italiano e inglese. Le modifiche proposte a `domain.md` non sono applicate. Nessun deploy.

## Verifiche automatiche

- Backend: 1192 test passati; Ruff e formattazione passati.
- Frontend: 420 test passati; lint, TypeScript e build passati.
- Migrazione da zero e downgrade a `0023` provati su SQLite; CI SQL Server da verificare sulla PR.

## Collaudo per gli organizzatori

La checklist è in [`test-manuali.md`](test-manuali.md). Verificare almeno:

- un esterno al solo pranzo, uno alla sola cena, uno a un'attività: nessun account o iscrizione compare in «Persone» e nessuno riceve email;
- l'ultimo posto di un'attività occupato da un esterno: il partecipante la vede piena; superare il limite chiede la conferma esplicita;
- omonimo di un esterno o di un iscritto: l'app chiede conferma;
- allergie solo con la spunta del consenso; togliendola spariscono;
- report e CSV (pasti, attività, settimana, esterni): colonne «Esterni» e «Tipo», importi e incassi identici a prima;
- area esterni negata a chi non è admin.
