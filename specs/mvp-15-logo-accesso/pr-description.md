# MVP 15 · Logo dell'edizione e accesso diretto

## Cosa cambia

Gli organizzatori possono caricare il logo dell'edizione dalle Impostazioni, vederne l'anteprima e tornare al logo iniziale. Il logo dell'intestazione apre la pagina personale; chi non ha fatto accesso viene indirizzato al login. Dal modulo di iscrizione si può già accedere, anche quando il modulo è dentro una scheda incorporata.

## Da provare a mano

- Dalle Impostazioni carica un logo PNG trasparente e verifica che appaia integro nell'intestazione; prova poi a sostituirlo e a ripristinare il logo iniziale.
- Carica un file non immagine e uno oltre 5 MB: il logo già configurato deve restare visibile.
- Clicca il logo da admin e da partecipante: deve aprirsi la pagina personale; da visitatore senza sessione deve apparire il login.
- Dalla pagina d'iscrizione usa «Accedi»; ripeti con l'edizione chiusa e nell'iframe del sito, verificando la nuova scheda e la lingua.

## Verifiche automatiche

- [x] 995 test backend e 357 test frontend passati; lint e build locali completati.
- [x] Migrazione 0013→0014 e downgrade 0014→0013 verificati su SQLite.
- [ ] Eseguire la CI SQL Server dopo la pubblicazione del branch.
