# MVP 9 · Guida in app e note di rilascio · Requisiti

**Obiettivo**: chi ha fatto il login trova nell'app una guida alle funzioni che può usare, sempre allineata alla versione in produzione; gli organizzatori vedono anche le novità di ogni rilascio.

## Storie

1. **Guida del partecipante**. Come partecipante voglio una pagina «Guida» che mi spiega come iscrivermi, pagare, cambiare slot, scegliere pasti e attività, proporre contributi e disdire.
   - Quando sono loggato come partecipante e apro `/guida` allora vedo solo la guida del partecipante, con un indice delle sezioni.
   - Quando non sono loggato e apro `/guida` allora vengo mandato a `/accedi`.
2. **Guida dell'organizzatore**. Come admin voglio la guida di ogni voce del pannello, e poter leggere anche quella dei partecipanti per aiutare chi mi chiede.
   - Quando sono loggato come admin e apro `/guida` allora vedo tre schede: «Organizzatori», «Partecipanti», «Novità».
   - Quando sono partecipante allora non vedo le schede e non posso ottenere il testo della guida admin né le novità (le API rispondono 403).
3. **Aiuto nel punto giusto**. Come admin voglio che il link «Guida» del pannello mi porti alla sezione della pagina in cui mi trovo.
   - Quando premo «Guida» da «Giorni e slot» allora si apre la sezione «Giorni e slot» della guida organizzatori.
4. **Note di rilascio**. Come admin voglio sapere cosa è cambiato a ogni deploy.
   - Quando si fa un deploy allora «Novità» elenca, per rilascio, le novità e le correzioni dei commit uniti, dal più recente.
   - Quando il file delle note manca (ambiente locale) allora «Novità» dice che saranno disponibili dopo il primo deploy.
5. **Versione visibile**. Come utente voglio vedere quale versione sto usando.
   - Quando apro `/guida` allora in fondo leggo «Versione {codice breve} del {data}» in ora di Roma.
6. **Guida sempre aggiornata**. Come maintainer voglio che la guida non resti indietro.
   - Quando una PR cambia pagine o API senza toccare `frontend/src/guide/` allora la CI fallisce, salvo la label `senza-guida`.
   - Quando si fa un deploy allora la guida pubblicata è quella del codice, perché è nella build.

## Fuori scope (Backlog)

- Note di rilascio tradotte o riscritte a mano: oggi i testi dei commit sono in inglese.
- Guida in più lingue, ricerca nel testo, immagini e screenshot.
- Guida visibile senza login.
