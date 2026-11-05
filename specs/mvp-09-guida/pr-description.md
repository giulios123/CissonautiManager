# MVP 9 · Guida in app e note di rilascio

Dopo il login c'è una pagina **Guida** che spiega le funzioni dell'app. Cosa vede ognuno dipende dal ruolo, e la guida si aggiorna a ogni deploy.

## Cosa cambia per chi usa l'app

- **Partecipanti**: dalla propria pagina, link «Come funziona: la guida». Trovano come iscriversi, accedere, pagare, cambiare slot, scegliere pasti e attività, proporre contributi, usare la lista d'attesa e disdire.
- **Organizzatori**: nel menu del pannello c'è «Guida», che porta alla sezione della pagina in cui ti trovi. Tre schede: **Organizzatori** (una sezione per voce del menu), **Partecipanti** (la guida che vedono gli iscritti, per aiutare chi chiede) e **Novità** (cosa è cambiato a ogni rilascio).
- In fondo alla pagina si legge la versione in uso e la data.

## Sotto il cofano

- I testi sono file Markdown in `frontend/src/guide/`: ogni PR che cambia una funzione visibile deve aggiornarli. Un controllo automatico (`Guide`) lo verifica; si salta con la label `senza-guida`.
- Le novità si generano dai messaggi dei commit a ogni deploy, quindi sono in inglese.

## Prove manuali per gli organizzatori

- [ ] Da telefono, entra come partecipante: dalla tua pagina apri «Come funziona: la guida»; vedi solo la guida dei partecipanti, nessuna scheda.
- [ ] Entra come organizzatore: vedi le tre schede; da «Giorni e slot» premi «Guida» e arrivi alla sezione «Giorni e slot».
- [ ] Nella scheda «Novità» compaiono i rilasci, l'ultimo in cima; la versione in fondo coincide con l'ultimo deploy.
- [ ] Leggi i testi delle due guide e segna cosa è sbagliato, mancante o scritto in modo poco chiaro.
- [ ] Con le frecce della tastiera passi da una scheda all'altra.
- [ ] Prima del merge: crea su GitHub la label `senza-guida`.
