# Cissonauti Booking

Gestione delle iscrizioni al **Cissone Summer Camp**, una settimana di coworking informale in un salone comunale tra amici e amici di amici.

L'app serve a sapere quante persone ci sono ogni giorno nello spazio, ai pasti e alle attività, a ridurre le rinunce legando il posto al pagamento e a dare agli organizzatori una vista completa e modificabile.

## Stato

Le funzionalità sono organizzate in MVP:

- **MVP 1–3 · Iscrizioni e amministrazione:** iscrizione pubblica, accesso con magic link o password, pagina personale, gestione delle iscrizioni e dei pagamenti, promemoria, viste admin con export CSV, rimborsi e cronologia. Il deploy è su Azure.
- **MVP 4–6 · Liste d'attesa, pasti e attività:** promozione automatica dalla lista d'attesa; scelta di pranzi, cene e attività dalla pagina personale; gestione di esigenze alimentari, capienze e contributi.
- **MVP 7–9 · Inviti, report e guida:** gestione dei +1 e report dell'edizione; stile coerente con il sito, anche nell'iframe di Google Sites; guida in app per ruolo e note di rilascio.
- **MVP 10–13 · Incassi, lingue ed email:** pagina per registrare gli incassi; app, pannello admin e guida in italiano e inglese; email di iscrizione personalizzabile con immagine e nome del partecipante.

Per lo stato aggiornato e le verifiche ancora aperte, consulta [`memory-bank/progress.md`](memory-bank/progress.md); la roadmap è in [`specs/ROADMAP.md`](specs/ROADMAP.md).

## Come è organizzato il repo

- `AGENTS.md`: istruzioni per chi sviluppa con Claude Code, Codex o GitHub Copilot (e utili anche agli umani).
- `memory-bank/`: contesto del progetto, regole di dominio, decisioni, avanzamento.
- `specs/`: roadmap e una cartella per ogni MVP con requisiti, design e task.
- `backend/`: FastAPI (Python 3.12), API sotto `/api`.
- `frontend/`: React con Vite e TypeScript, servito dal backend. La guida in app è in `frontend/src/guide/{it,en}/` (un file Markdown per sezione e per lingua).
- `scripts/`: script di supporto (note di rilascio, controllo della guida).
- `infra/`: infrastruttura Azure in Bicep.

## Avvio in locale

I comandi sono in [`AGENTS.md`](AGENTS.md#comandi). In breve: copia `.env.example` in `.env` (imposta `ADMIN_EMAIL` e `ADMIN_PASSWORD`), applica le migrazioni, avvia backend e frontend. Senza Docker l'app usa un file SQLite locale. Le email in sviluppo compaiono nel log del backend.

## Contribuire

Issue e pull request sono benvenute. Prima di proporre una modifica leggi `AGENTS.md` e `memory-bank/domain.md`: le idee fuori dall'MVP corrente vanno nel Backlog di `specs/ROADMAP.md`.

## Licenza

[MIT](LICENSE)

Il logo di Cissone (`frontend/src/assets/logo-cissone.png`) appartiene alla Pro Loco di Cissone ed è usato con il suo permesso: non rientra nella licenza MIT. Il font Montserrat è distribuito con licenza SIL Open Font License.
