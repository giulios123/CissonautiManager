# MVP 11 · Lingue e indirizzi · Design

## Schema d'insieme

| Pezzo | Cosa | Dove |
|---|---|---|
| Rotte | tabella unica inglese + alias italiani, `canonicalPath()` | `frontend/src/routes.ts` |
| Alias | la rotta `*` prova l'alias e fa `<Navigate replace>` con query e hash | `App.tsx` |
| i18n frontend | dizionari `it.ts` e `en.ts` (tipo `Messages`), `I18nProvider`, `useT()` | `frontend/src/i18n/` |
| Lingua | `?lang` → `localStorage` → `navigator.languages`; selettore in `SiteHeader` | `i18n/` |
| API | `Accept-Language` su ogni richiesta; `PUT /api/me/locale` | `api.ts`, `api/me.py` |
| Dati | `participant.locale` (`it`/`en`, default `it`), migrazione 0011 | `models.py` |
| Errori | `AppError(key, **params)` + handler che traduce; catalogo `{key: {it, en}}` | `backend/app/i18n.py` |
| Email | ogni template prende `locale`; 8 email × 2 lingue | `email/templates.py` |
| Date | `timefmt.py` per lingua | `timefmt.py` |
| Guida | `guide/{it,en}/{participant,admin}/NN-slug.md`, `content.ts` per lingua | `frontend/src/guide/` |

## Rotte

| Alias italiano | Indirizzo inglese |
|---|---|
| `/iscrizione` | `/register` |
| `/accedi` | `/login` |
| `/accedi/verifica` | `/login/verify` |
| `/io` | `/me` |
| `/guida?scheda=organizzatori` | `/guide?tab=organizers` |
| `/admin/iscrizioni/:id` | `/admin/registrations/:id` |
| `/admin/giorni` · `settimana` · `pasti` | `/admin/days` · `week` · `meals` |
| `/admin/attivita[/:id]` · `contributi` | `/admin/activities[/:id]` · `contributions` |
| `/admin/da-incassare` · `da-verificare` | `/admin/to-collect` · `to-review` |
| `/admin/amministratori` · `impostazioni` | `/admin/admins` · `settings` |

Backend: magic link → `/login/verify`; promemoria e lista d'attesa → `/login`; redirect del login → `/me` o `/admin`; CSP `frame-ancestors` di Google Sites sia su `/register` sia su `/iscrizione`.

## Scelte

- Nessuna libreria i18n: dizionari TypeScript, `en` tipizzato con `typeof it` (una chiave mancante non compila).
- Il backend mantiene `detail` come stringa tradotta, così il frontend non cambia.
- I contenuti dell'admin restano come scritti.
- Nei test il provider forza `it`.

## Modifiche a domain.md

- **Accesso**: l'app è in italiano e inglese; lingua dal browser o dal selettore, salvata sul partecipante; indirizzi in inglese, gli italiani reindirizzano.
- **Email**: partono nella lingua del partecipante.
