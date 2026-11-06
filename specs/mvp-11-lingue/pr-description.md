# Lingue: italiano e inglese, indirizzi in inglese

L'app parla italiano e inglese dal lato del partecipante (iscrizione, accesso, pagina personale, guida) e le email partono nella lingua di chi le riceve. Il pannello degli organizzatori resta in italiano fino all'MVP 12.

## Cosa cambia per gli organizzatori e per i partecipanti

- Nell'intestazione c'è il selettore **IT / EN**. La prima volta la lingua è quella del browser; con `?lang=en` o `?lang=it` nell'indirizzo si può forzarla (utile per l'iframe nel sito).
- Gli indirizzi sono in inglese: `/register`, `/login`, `/me`, `/guide`, `/admin/days`, `/admin/to-collect`... Chi scrive a mano un indirizzo italiano (`/iscrizione`, `/accedi`, `/io`...) viene portato a quello inglese. I vecchi link nelle email continuano a funzionare.
- Chi si iscrive in inglese riceve in inglese tutte le email (iscrizione, link di accesso, pagamento, promemoria, lista d'attesa, disdetta). Le email già inviate non cambiano.
- Cambiando lingua da loggati, la scelta si salva e vale per le email future.
- Nuova regola per chi sviluppa (in `AGENTS.md`): ogni funzione nuova è bilingue; il controllo della guida chiede entrambe le lingue.
- Restano come scritti dagli organizzatori: nomi e descrizioni delle attività, istruzioni di pagamento, testi legali.

## Note tecniche

Migrazione 0011 (`participant.locale`, default `it`). Decisioni D-041, D-042, D-043. Nessuna nuova dipendenza.

## Test manuali (per gli organizzatori)

- [ ] Apri il sito con il browser in inglese: il modulo è in inglese; premi IT e diventa italiano, e resta tale dopo aver ricaricato.
- [ ] Scrivi `…/iscrizione` nella barra degli indirizzi: finisci su `…/register` con il modulo.
- [ ] Nel sito Google il modulo incorporato si vede ancora (prova anche con `?lang=en` nell'indirizzo del modulo).
- [ ] Iscriviti dal modulo in inglese con una tua email: arriva l'email in inglese, con il link che apre la tua pagina.
- [ ] Apri un vecchio link di accesso (`…/accedi/verifica?token=…`) ricevuto prima: funziona ancora.
- [ ] Nella pagina personale cambia lingua: testi, date e importi cambiano (€12.00 / 12,00 €).
- [ ] Leggi la guida in inglese e segnala le frasi che non suonano bene.
- [ ] Da telefono: il selettore si tocca bene e la pagina non scorre di lato.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_012LLwpbQuKqdPp12BEQrJju
