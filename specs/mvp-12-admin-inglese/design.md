# MVP 12 · Pannello admin in inglese · Design

Nessuna migrazione. Riusa l'infrastruttura dell'MVP 11.

| Pezzo | Cosa |
|---|---|
| Dizionari | sezione `admin` in `i18n/it.ts` e `en.ts` |
| Pagine | `AdminLayout` e viste, scheda e componenti, `AdminAdmins`, `AdminSettings`, `CsvButton` |
| CSV | `csv_export.py` e `report_export.py` prendono `locale`; `status_label` e `period_label` per lingua |
| Guida | `guide/en/admin/` (12 file), test di parità esteso |
| CI | `check-guide.sh` chiede entrambe le lingue |

Impatto sugli MVP precedenti: i test del pannello restano in italiano (il provider dei test forza `it`); si aggiungono test in inglese sulle pagine chiave.
