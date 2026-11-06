# Email di iscrizione personalizzabile, con immagine

Da **Impostazioni → Email di iscrizione** gli organizzatori scrivono il testo della email di conferma (in italiano e in inglese) e possono aggiungere un'immagine con il nome della persona e le date dell'evento.

## Cosa cambia per gli organizzatori

- **Testo**: oggetto e testo iniziale per ciascuna lingua, con i pulsanti per inserire nome, cognome, evento, data di inizio e di fine. Lasciati vuoti, la email resta quella di prima.
- **Parte fissa**: dopo il tuo testo ci sono sempre slot, quota, causale, scadenza, istruzioni di pagamento e link personale. Non si possono togliere.
- **Immagine**: carica uno sfondo (JPEG, PNG o WebP, fino a 5 MB). L'app ci scrive sopra «Sono *nome cognome* e sarò a *evento* dal *data* al *data*» (in inglese «I'm *nome cognome* and I'll be at *evento* from *data* to *data*»). Puoi cambiare frase, colore e posizione.
- **Anteprima** che si aggiorna mentre scrivi e **«Inviami una prova»** per ricevere la email vera.
- Chi si iscrive solo in lista d'attesa non riceve l'immagine.
- Guida organizzatori aggiornata (nuova sezione «Email di iscrizione», anche in inglese).

## Note tecniche

Migrazione 0012 (`email_template`, `registration_card`). Nuove dipendenze: Pillow e python-multipart. Font Montserrat (licenza OFL) in `backend/app/assets/fonts/`. Decisione D-045.

## Test manuali (per gli organizzatori)

- [ ] In Impostazioni apri «Email di iscrizione», carica una foto: compare l'anteprima con «Ada Lovelace».
- [ ] Cambia la frase, il colore e la posizione: l'anteprima si aggiorna.
- [ ] Scrivi un testo con un segnaposto sbagliato (per esempio `{nome}`): al salvataggio viene rifiutato e ti elenca quelli validi.
- [ ] Salva e premi «Inviami una prova» in italiano e in inglese: guarda la email in Gmail, Outlook e sul telefono (l'immagine si vede? il testo è leggibile anche senza?).
- [ ] Iscriviti con una tua email dal modulo in inglese: arriva la email con il tuo nome nell'immagine e nelle date.
- [ ] Iscriviti con un nome con accenti o molto lungo: l'immagine resta leggibile.
- [ ] «Togli lo sfondo»: la prossima email parte senza immagine.
- [ ] Prova a caricare un PDF o una foto enorme: ricevi un messaggio chiaro e nulla cambia.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_012LLwpbQuKqdPp12BEQrJju
