# MVP 13 · Email di iscrizione personalizzabile · Task

**Dimensione**: 8 task.

- [x] **1. Email HTML e allegati** in `EmailMessage`, ACS e console. Test: payload ACS con `html` e allegato inline.
- [x] **2. Migrazione 0012** e modelli. Test: da zero e downgrade.
- [x] **3. Segnaposto e validazione**. Test puri.
- [x] **4. Card con Pillow** e font. Test: PNG valido, nomi lunghi a capo, accenti, file non immagine e file troppo grande rifiutati.
- [x] **5. API admin**. Test: 200/401/403, formato errato, anteprima, prova inviata.
- [x] **6. `registration_email`** con testo e card, ricaduta sui default. Test: IT/EN, HTML escapato, nessuna card per la sola lista d'attesa.
- [x] **7. Sezione nelle Impostazioni**, bilingue. Test UI.
- [x] **8. Guida admin IT/EN e chiusura**.
