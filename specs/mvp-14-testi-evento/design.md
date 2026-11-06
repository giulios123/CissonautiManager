# MVP 14 · Design

## Dati (migrazione 0013)
- `edition.registration_intro_it`, `edition.registration_intro_en` (testo, nullable, senza default).
- Nessuna tabella nuova: le altre email usano `email_template` (`kind`, `locale`) dell'MVP 13.

## Backend
- `email/base.py`: `EmailTexts(event_name, subject, body)`; `RegistrationExtras` guadagna `event_name`.
- `email_texts.py` (dizionari): i testi che contenevano dati sono spezzati in frase + riga di dati (`email.magic.link`, `email.already.link`, `email.payment.amount`, `email.promoted.slot`); link da 10 minuti.
- `email/templates.py`: ogni email prende `texts: EmailTexts`; apertura = testo scritto o saluto + frase standard; oggetto = scritto o chiave standard con il nome dell'edizione.
- `domain/email_template.py`: `OTHER_EMAIL_KINDS`, `DEFAULT_FORM_INTRO`, `FORM_INTRO_MAX`.
- `services/email_templates.py`: `texts_for`, `texts_for_booking`, `emails_view`, `save_email`, `save_form_intro`, `form_intro_for`; usati dai punti di invio (registrazione, auth, pagamenti, promemoria, lista d'attesa, disdetta).
- API: `GET /api/admin/email/texts`, `PUT /api/admin/email/texts/{kind}` (con un nuovo tentativo su `IntegrityError`), `PUT /api/admin/email/form-intro`; `registration_intro` (le due lingue) nell'edizione pubblica.
- Auth: `MAGIC_LINK_TTL` 10 minuti, `consume_magic_link` non rifiuta i token già usati, `login_result` rimanda sempre a `/me`.

## Frontend
- `eventName.tsx` (`EventNameProvider`, `useEventName`, `useRefreshEventName`) per intestazione, titoli, home; le Impostazioni lo rinfrescano al salvataggio.
- `Registration.tsx`: paragrafo da `registration_intro[locale]`.
- `AdminEmailTexts.tsx` nelle Impostazioni, sotto l'editor dell'iscrizione: schede lingua, testo sopra il modulo, una scheda per email con oggetto, testo e parte automatica.
- `Verify.tsx` entra da solo; `Personal.tsx` barra admin; `AdminLayout.tsx` «La mia pagina»; testi it/en in `i18n/`.

## Guida
`admin/14-email-texts.md` (it e en), `01-people`, `10-settings`, `participant/02-signing-in`.
