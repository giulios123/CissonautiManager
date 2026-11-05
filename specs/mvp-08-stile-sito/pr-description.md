# MVP 8 · Stile del sito Cissone Eventi

## Cosa c'è
L'app prende l'aspetto del sito Cissone Eventi: font Montserrat, petrolio del logo per link e focus, ambra per il bottone principale, bottoni e campi squadrati, logo di Cissone in alto. Dentro l'iframe del sito il modulo di iscrizione ha lo sfondo trasparente e un'intestazione ridotta al solo nome, così non ripete quella del sito. Testi, pagine e funzioni non cambiano.

## Da provare a mano (per gli organizzatori)

**Dentro il sito**
- [ ] Apri la pagina del sito che contiene l'iscrizione, dal telefono e dal computer: il modulo sembra parte della pagina (stesso font, stessi colori, niente riquadro di colore diverso).
- [ ] In alto nel modulo c'è solo la scritta piccola «Cissonauti Summer Camp», senza logo.
- [ ] Fai un'iscrizione completa dal sito: tutto funziona come prima.

**Fuori dal sito**
- [ ] Apri il link dell'email: in alto vedi il logo di Cissone e «Cissonauti Summer Camp», con una riga gialla sotto.
- [ ] Nella pagina personale i bottoni principali sono gialli con testo scuro, quelli secondari bianchi con il bordo petrolio (anche «Esci»), «Richiedi disdetta» è rosso.
- [ ] Lo stato dell'iscrizione ha un colore: giallo «In attesa di pagamento», verde «Confermata», grigio «Scaduta», rosa «Disdetta richiesta», petrolio «Rimborsata». Lo trovi nella pagina personale, in «Persone», «Giorni e slot», «Da verificare» e nella scheda.
- [ ] Nel pannello organizzatori la barra del menu è petrolio, la voce aperta è sottolineata, le tabelle hanno l'intestazione grigia e le righe alterne.

**Dopo l'audit** (`specs/mvp-08-stile-sito/audit.md`)
- [ ] Da telefono il menu del pannello è una riga che scorre di lato e la voce in cui sei è sempre in vista.
- [ ] Ogni pagina ha un titolo diverso nella scheda del browser (per esempio «Giorni e slot · Cissonauti Summer Camp»).
- [ ] In «Giorni e slot» la lista d'attesa è numerata una volta sola.
- [ ] In «Impostazioni» i campi data mostrano il bordo petrolio quando ci arrivi con Tab.

**Accessibilità**
- [ ] Compila il modulo di iscrizione usando solo la tastiera (Tab, spazio, Invio): vedi sempre dove sei grazie al bordo petrolio.
- [ ] Da telefono la pagina non scorre di lato e i bottoni si premono facilmente.

## Note
- Il logo è della Pro Loco di Cissone, usato con il suo permesso: è scritto nel README.
- Le spaziature del sito non sono state rilevate (il CSS di Google Sites non era raggiungibile): restano quelle dell'app.
