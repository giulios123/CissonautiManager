# MVP 13 · Email di iscrizione personalizzabile · Design

## Dati (migrazione 0012)

- `email_template`: `edition_id`, `kind` (`registration`), `locale`, `subject`, `body`, `updated_at`, `updated_by_id`; unico per (edizione, tipo, lingua).
- `registration_card`: `edition_id` unico, `image` (PNG, `LargeBinary`), `text_it`, `text_en`, `text_color`, `text_position`, `updated_at`.

L'immagine sta nel database: pochi file, niente Blob Storage da aggiungere all'infrastruttura.

## Pezzi

| Pezzo | Cosa |
|---|---|
| Regole pure | `domain/email_template.py`: segnaposto, validazione, date per lingua |
| Card | `email/card.py` con Pillow: ricodifica, testo a capo, riduzione della dimensione, fascia semitrasparente, Montserrat 800 (licenza OFL) in `backend/app/assets/fonts/` |
| Email | `EmailMessage` aggiunge `html` e `attachments` (con `content_id`); `acs.py` manda `html` e allegati inline; `console.py` registra i nomi |
| API | `GET/PUT /api/admin/email/registration`, `PUT/DELETE .../image`, `GET .../preview.png`, `POST .../test` (`require_admin`) |
| Pagina | sezione «Email di iscrizione» in `AdminSettings` |
| Dipendenze | `pillow`, `python-multipart` |

## Modifiche a domain.md

- **Email**: la conferma di iscrizione ha oggetto e testo modificabili per lingua e un'immagine generata con nome, cognome, evento e date su uno sfondo caricato dall'admin.
- **Pannello admin · Impostazioni**: aggiunta «email di iscrizione e immagine».
