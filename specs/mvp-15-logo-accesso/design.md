# MVP 15 · Design

## Dati e migrazione

- Aggiungere `Edition.logo_image`, colonna binaria nullable, con la migrazione Alembic 0014. Un `NULL` continua a indicare il logo incluso nell'app.
- Normalizzare i file con l'elaborazione immagini già usata per la mail di iscrizione: PNG, JPEG e WebP; massimo 5 MB, massimo 1600 px per lato e metadati rimossi. Mantenere la modalità RGB per l'immagine email e preservare l'alpha solo per il logo.

## API

- `PUT /api/admin/edition/logo`, multipart con campo `file`, valida e salva il logo dell'edizione attiva. `DELETE /api/admin/edition/logo` elimina la personalizzazione. Entrambi richiedono ruolo admin e rispondono con `EditionOut`.
- `GET /api/public/edition/logo?v=<sha256>` serve il PNG dell'edizione attiva. Un logo assente o una versione non più corrente rispondono 404; gli URL versionati possono essere memorizzati in cache immutable.
- Aggiungere `logo_url: string | null` alle risposte pubbliche e admin dell'edizione. Calcolare l'URL sul contenuto corrente senza includere i byte nelle risposte JSON; esporlo anche se le iscrizioni sono chiuse.
- Errori file 413 (dimensione) e 422 (formato o immagine non leggibile), con testi italiani e inglesi già usati dai caricamenti immagine.

## Interfaccia

- Impostazioni: sezione Logo dopo il modulo dell'edizione; file input accessibile, anteprima, messaggi di esito e pulsante di ripristino mostrato solo con personalizzazione.
- Contesto dell'edizione: carica `logo_url` dalla risposta pubblica e lo rilegge dopo caricamento, ripristino o rinomina dell'edizione. L'intestazione usa il PNG custom e torna a quello incluso se il custom non si carica.
- Intestazione: il marchio rimanda a `ROUTES.me`; l'autenticazione resta affidata a `RequireLogin`.
- Iscrizione: link localizzato verso `/login?lang=<locale>` negli stati del modulo e della sua risposta. Nel frame usa `_blank` e `rel="noopener"`; altrimenti naviga nella stessa scheda.

## Modifiche a domain.md

Nessuna: il logo è una preferenza di presentazione dell'edizione.
