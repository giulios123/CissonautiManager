# MVP 26 · Task

- [x] **T26-1** Servizio: `activity_signups` in `services/views.py` con `activity_signup_days` riscritta sopra di esso. Test: gli stessi conteggi di prima su iscritti ed esterni, esclusi scaduti e lista d'attesa.
- [x] **T26-2** Endpoint `GET /api/admin/views/week/detail` per le sette metriche, giorno e totale, solo campi minimi. Test: per ogni metrica la somma del dettaglio è uguale alla cella di `week_view`; sera derivata; esterni in pasti e attività e non nel coworking; zero righe.
- [x] **T26-3** Permessi e validazione. Test: 401/403 per non admin; 422 per metrica o data non valide; nessuna email, allergia o importo nella risposta.
- [x] **T26-4** `InfoDialog` riusabile da `ConfirmDialog`, classe larga e test: focus dentro, Tab trattenuto, Esc, ritorno del focus.
- [x] **T26-5** `AdminWeek.tsx`: celle e totali come pulsanti, `WeekDetailDialog` con caricamento, errore, vuoto, adesioni vs persone, avviso «numero cambiato». Chiavi i18n IT/EN. Test frontend.
- [x] **T26-6** Guida `admin/03-week.md` IT/EN, `test-manuali.md` pronto, suite completa, Ruff, lint, TypeScript e build verdi.

Scostamenti rispetto al design: il componente del dettaglio sta in `frontend/src/pages/WeekDetailDialog.tsx`; il dettaglio dei totali elenca una riga per persona (pranzi, cene e attività una riga per voce, con il giorno davanti); `common.close` è la nuova chiave del pulsante «Chiudi». Nessun CSV del dettaglio (era fuori scope).
