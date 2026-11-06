# Orari selezionabili, telefono obbligatorio e pagamenti diretti

Le attività e i pasti finivano sempre nella quota degli organizzatori: adesso l’admin può indicare pagamento diretto all’erogatore, con costo e istruzioni visibili prima e dopo l’adesione. Le adesioni continuano nell’app; per esempio, una quota di 11 € con pranzo esterno da 23 € resta 11 €. Cambiando costo o destinatario si ricalcolano i saldi attivi interessati, mantenendo pagamenti e crediti. Le attività hanno inizio/fine da menu; il telefono è obbligatorio nei nuovi invii.

Migrazione 0015 compatibile con dati preesistenti: incasso organizer come default, vecchi orari mantenuti, nessun ricalcolo automatico al rilascio. Testi e guida in italiano e inglese.

## Verifica per gli organizzatori

- [ ] Da telefono, provare la registrazione senza telefono e con un numero valido, anche scegliendo solo la lista d’attesa.
- [ ] Creare un’attività scegliendo ore e minuti; provare un’attività serale fino a mezzanotte e un intervallo fuori fascia.
- [ ] Impostare pagamento diretto, costo e istruzioni per un’attività e per un singolo pranzo; verificare che le altre date mantengano i prezzi standard.
- [ ] Aderire e verificare che il saldo agli organizzatori non aumenti; chiudere l’editor e ritrovare costo e istruzioni nel riepilogo anche a quota saldata.
- [ ] Cambiare destinatario con iscritti e verificare saldo, credito, stato e cronologia; controllare report e CSV.
- [ ] Ripetere in inglese e verificare la guida.

## Validazione e limiti dell’ambiente

Suite SQLite completa e controlli mirati aggiuntivi, test frontend, Ruff, ESLint/Prettier e build. Migrazioni SQLite da zero, confronto modelli/schema e upgrade/downgrade con un’attività preesistente. SQL della migrazione compilato per SQL Server.

Prova HTTP su app reale e DB migrato temporaneo: login, riepilogo saldato con istruzioni, creazione 21:35–mezzanotte, cambio del pranzo provider→organizer→provider (quota 11→19→11 €), report coerente.

Test reali SQL Server non eseguibili: download dell’immagine ufficiale 2022 rifiutato con Forbidden. Browser locale e cloud non disponibili nella sessione: la prova visiva mobile/desktop rimane da fare; i componenti e i flussi sono coperti dai test automatici.
