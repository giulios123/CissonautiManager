# MVP 26 · Dettaglio dei numeri settimanali

## Cosa cambia per gli organizzatori

Nella pagina «Settimana» ogni numero (anche i totali in fondo) si può premere: si apre l'elenco delle persone o delle adesioni che compongono quel numero, con il link alla scheda. Nessun dato nuovo viene salvato; l'elenco non mostra email, telefono, allergie né importi.

## Come provarlo

Segui [test-manuali.md](test-manuali.md) (10 passi, in italiano e in inglese).

## Dettagli tecnici

- `GET /api/admin/views/week/detail?metric=&date=`, solo admin; usa gli stessi loader della tabella, quindi numero ed elenco non possono divergere (un test lo verifica per ogni metrica e giorno).
- `activity_signups` sostituisce la logica di `activity_signup_days`, che ora ne deriva.
- Nuovo `InfoDialog` riusabile (MVP 27).
- Nessuna migrazione. Guida admin aggiornata in IT/EN.
