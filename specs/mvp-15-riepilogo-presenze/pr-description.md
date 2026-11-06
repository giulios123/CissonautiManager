# Riepiloghi più chiari per chi partecipa

Presenze e orari erano ripetuti per ogni fascia nel modulo, nella pagina personale e nelle email. Ora le presenze sono raggruppate per giorno: le giornate complete occupano una riga con la sola data e i giorni parziali mostrano le fasce scelte. Un'unica legenda raccoglie gli orari. Importo, scadenza e stato sono facili da trovare; le fasce in lista d'attesa restano separate.

## Verifiche per gli organizzatori

- [x] Test automatici: backend 991 test; frontend 354 test; build, lint, Ruff e controllo guide passati. Dopo le rifiniture finali sono passati anche i test mirati per riepilogo, API e email.
- [x] Verifica locale in Chromium: desktop, layout mobile al 200%, barra con quota e invio, focus visibile e policy iframe coperta dai test.
- [ ] Da telefono, selezionare più giorni e verificare il riepilogo e il link «Modifica presenze».
- [ ] Includere mattina e pomeriggio: la data appare come giornata completa. Provare anche solo una fascia.
- [ ] Aprire pagina di conferma e pagina personale; confrontare date e orari.
- [ ] Controllare email di iscrizione e conferma pagamento in italiano e inglese, anche in un client solo testuale.

Le verifiche manuali su telefono fisico, nell'iframe reale di Google Sites e nei client email restano da fare dopo il deploy.
