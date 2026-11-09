# MVP 25b · Incassi degli esterni

## Descrizione

Gli esterni aggiunti con l'MVP 25a ora hanno un **conto**. Per un esterno *pagante* l'app calcola quanto deve: la somma dei prezzi correnti dei suoi pasti e delle sue attività incassati dall'organizzazione (niente quota, niente pasto compreso; i costi al fornitore restano fuori). Un *non pagante* non deve nulla.

L'admin registra **pagamenti** e **restituzioni** (queste ultime mai oltre il credito) in un registro **separato** dai pagamenti delle prenotazioni: nessuna quota di iscritto cambia e non parte nessuna email. Un movimento sbagliato si **annulla** con un motivo, non si cancella. Doppio clic o nuovo invio non duplicano il movimento. Un esterno con movimenti, anche annullati, non si elimina.

In **Da incassare** compare in fondo la sezione «Esterni da incassare» (con ricerca per nome); la lista delle prenotazioni non cambia. Il **Report** ha la tabella «Incassi esterni» e il «Totale evento», somma del netto delle quote e del netto degli esterni; c'è anche il CSV dei movimenti.

Migrazione additiva `0025_external_movements` (una tabella nuova). Testi e guida in italiano e inglese. Le modifiche proposte a `domain.md` non sono applicate. Nessun deploy. Questo branch si appoggia sul 25a: va integrato dopo.

## Verifiche automatiche

- Backend: 1251 test passati; Ruff e formattazione passati.
- Frontend: 430 test passati; lint, TypeScript e build passati.
- Migrazione da zero e downgrade a `0024` provati su SQLite; CI SQL Server da verificare sulla PR.

## Collaudo per gli organizzatori

La checklist è in [`test-manuali.md`](test-manuali.md). Verificare almeno:

- esterno pagante con un pranzo da 8 €: dovuto 8 €, compare in «Da incassare» → «Esterni»;
- incasso di 6 €: il totale evento sale di 6 €, quote e pagamenti delle prenotazioni identici;
- doppio clic su «Registra»: un solo movimento; annullo con motivo: resta barrato e non conta;
- non pagante dopo un versamento: il versato diventa credito, restituibile fino a quel credito;
- pasto pagato al fornitore: visibile con costo, ma fuori da dovuto e totali;
- CSV dei movimenti e del report nella lingua dell'app; area esterni negata a chi non è admin.
