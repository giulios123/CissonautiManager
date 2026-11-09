# MVP 25a · Task

- [x] **T25a-1** Funzioni pure in `domain/external.py`: omonimi, giorni ammessi, unione dei conteggi. Test in `test_domain_external.py`.
- [x] **T25a-2** Modelli e migrazione `0024_external_guests`; upgrade e downgrade su SQLite, vincoli compatibili con SQL Server.
- [x] **T25a-3** API admin di esterni, pasti e attività: 409 sui doppioni con conferma esplicita, `force` sulla capienza, consenso per le allergie, cronologia. Test: 403 ai non admin, nessun `Booking` o `Participant` creato, allergie cancellate togliendo il consenso.
- [x] **T25a-4** Capienze: posti occupati dagli esterni in `seats.py`, modifica e eliminazione delle attività con esterni aderenti. Test anche dal lato partecipante (`me`).
- [x] **T25a-5** Viste pasti, settimana, attività e relativi CSV con gli esterni. Test: conteggio e dettaglio coincidono, una persona per voce.
- [x] **T25a-6** Report e CSV con la colonna «Esterni». Test in `test_report.py`: i conteggi tornano con le altre viste, gli importi non cambiano.
- [x] **T25a-7** Frontend: pagina, rotta, menu, etichette e i18n IT/EN. Test vitest.
- [x] **T25a-8** Guide IT/EN ed etichette inglesi dei CSV.
- [x] **T25a-9** Suite completa (backend 1192, frontend 420), Ruff, lint, TypeScript, build e migrazioni locali verdi; `test-manuali.md` e `pr-description.md` pronti. Restano CI SQL Server e collaudo organizzatori.

Scostamenti rispetto al design: la colonna «Tipo» dei CSV di pasti e attività precede «Nota interna» (non è l'ultima) per non spostare la nota; nel report la colonna è «Di cui esterni» in fondo e il totale include gli esterni; il CSV degli esterni non contiene le allergie.
