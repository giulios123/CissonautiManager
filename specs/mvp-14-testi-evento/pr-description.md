## Cosa cambia per gli organizzatori

- **Nome dell'evento**: l'intestazione, il titolo della scheda del browser e l'oggetto delle email usano il nome dell'edizione (Impostazioni). Se lo cambiate, cambia dappertutto.
- **Testi nelle Impostazioni**, sotto «Email di iscrizione»: per ogni altra email (lista d'attesa, già iscritto, link di accesso, pagamento ricevuto, i due promemoria, posto liberato, disdetta) modificate oggetto e testo iniziale, in italiano e in inglese, con gli stessi segnaposto della mail di iscrizione. I dati della prenotazione restano automatici. Lì c'è anche il paragrafo sopra il modulo di iscrizione.
- **Dopo il login** (anche da admin) si arriva alla propria pagina; in alto c'è «Vai al pannello organizzatori» e nel menu del pannello c'è «La mia pagina».
- **Link di accesso**: vale 10 minuti, si può riaprire in quel tempo e porta dentro subito, senza la pagina «Entra».

## Da provare a mano

1. Impostazioni → cambiate il nome dell'edizione, salvate: intestazione e titolo della scheda cambiano senza ricaricare.
2. Impostazioni → «Testo sopra il modulo»: scrivete un paragrafo in italiano e uno in inglese, aprite `/register` e cambiate lingua: vedete quello giusto, con gli a capo.
3. Impostazioni → «Link di accesso» (o «Pagamento ricevuto»): cambiate oggetto e testo iniziale in una lingua, provate con una persona in quella lingua: l'email ha i vostri testi e, dopo, i dati di sempre.
4. Svuotate un campo e salvate: la prossima email torna al testo standard.
5. Entrate da admin con la password: arrivate su «Ciao …!», non sul pannello. Il pulsante in alto porta al pannello, «La mia pagina» riporta indietro.
6. Chiedete il link di accesso, apritelo: entrate senza altri clic. Riapritelo entro 10 minuti: entrate ancora. Dopo 10 minuti vedete «Link non valido» con «Richiedi un nuovo link».
7. Controllate che la guida («Testo del modulo e altre email», «Accedere alla tua pagina») corrisponda a ciò che vedete.

## Note tecniche

Migrazione 0013 (`edition.registration_intro_it`, `registration_intro_en`). Decisione D-047. Modifiche a `domain.md` applicate. Questo branch era nato prima degli MVP 11-13 di `main`: dopo l'unione, i testi delle altre email usano l'editor per lingua dell'MVP 13 (stessa tabella `email_template`, stessi segnaposto) e il lavoro è stato rinumerato MVP 14.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_012LLwpZJz4c5XF1A96Mu3nV
