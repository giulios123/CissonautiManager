# Pannello admin in inglese

Tutto il pannello degli organizzatori è ora in italiano e in inglese, con lo stesso selettore IT / EN dell'intestazione.

## Cosa cambia per gli organizzatori

- Menu, viste (Persone, Giorni e slot, Settimana, Pasti, Attività, Contributi, Report, Da incassare, Da verificare, Admin, Impostazioni), scheda iscrizione, finestre di conferma ed errori sono tradotti.
- «Scarica CSV» produce il file nella lingua scelta in quel momento: intestazioni, stati e righe del report. Il formato resta quello di prima (punto e virgola, virgola decimale, date gg/mm/aaaa), così continua ad aprirsi bene in Excel italiano.
- Cambiando lingua dal pannello la pagina si ricarica con i dati nella nuova lingua.
- La guida degli organizzatori è disponibile in inglese, con le stesse sezioni.
- **Non cambia**: la «Cronologia» della scheda mantiene le voci già scritte e quelle nuove in italiano; nomi e testi che scrivete voi (attività, istruzioni di pagamento, testi legali) restano come li scrivete.

## Note tecniche

Nessuna migrazione. Decisione D-044. Nuovo file `backend/app/admin_texts.py` con le etichette inglesi dei CSV; un test controlla che ogni intestazione abbia la sua versione.

## Test manuali (per gli organizzatori)

- [ ] Entra nel pannello con il browser in inglese: menu e viste sono in inglese; premi IT e passano all'italiano.
- [ ] Da «People» scarica il CSV in inglese e aprilo in Excel: le colonne sono «First name», «Last name»… e gli importi sono leggibili.
- [ ] Scarica lo stesso CSV in italiano: è identico a quello che avevi prima.
- [ ] Registra un pagamento da «To collect» e prova «Undo» entro 10 secondi.
- [ ] Apri la guida in inglese (scheda «Organizers») e controlla che le sezioni siano le stesse dell'italiano.
- [ ] Apri il report in inglese e stampalo.
- [ ] Da telefono: il menu scorre di lato e le tabelle restano leggibili.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_012LLwpbQuKqdPp12BEQrJju
