# MVP 11 · Design

Dettaglio completo nel piano di sessione; qui la sintesi.

## Dati (migrazione 0011)
- `edition.registration_intro` (testo, nullable).
- Tabella `email_text`: `edition_id`, `kind`, `subject`, `intro`, `closing`, `updated_at`, `updated_by_id`; unica per (`edition_id`, `kind`). Null = predefinito.

## Dominio (`domain/email_texts.py`, funzioni pure)
- 9 tipi: registration, waitlist_joined, already_registered, magic_link, payment_confirmation, reminder_mid, reminder_final, waitlist_promoted, cancellation.
- `resolve` (vuoto → predefinito), `fill` (solo `{nome}` e `{evento}`, con `str.replace`), limiti (oggetto 200, testi 4000).

## Backend
- `templates.py`: ogni email = oggetto + apertura + blocco automatico + chiusura.
- `services/email_texts.py`: carica i testi dell'edizione attiva; usato dai punti di invio.
- API: `GET /api/admin/email-texts`, `PUT /api/admin/email-texts/{kind}`; `registration_intro` su edizione admin e pubblica.
- `login_result`: redirect sempre `/io`.
- `MAGIC_LINK_TTL` 10 minuti; `consume_magic_link` non rifiuta i token già usati, `used_at` registra il primo uso.

## Frontend
- `EventNameProvider` / `useEventName()` per intestazione, titoli, home.
- `Registration.tsx`: paragrafo da `registration_intro`.
- `AdminTexts.tsx` su `/admin/testi`; voce «La mia pagina» nel menu admin; barra «Pannello organizzatori» in `Personal.tsx`.
- `Verify.tsx`: chiama la verifica al caricamento (una sola volta), `replace` verso la pagina.

## Impatti
MVP 2 (pagina personale), MVP 3 (menu admin), guida (`admin/13-testi.md`, `partecipante/02-accedere.md`).
