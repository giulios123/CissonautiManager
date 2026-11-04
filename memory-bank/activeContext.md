# Active context

## Ora

Bootstrap completato: Memory Bank, `AGENTS.md`, roadmap e spec dell'MVP 1 (`specs/mvp-01-iscrizione-base/`).
La spec dell'MVP 1 è in attesa di conferma del maintainer.

## Prossimo passo

Dopo la conferma: fase B2 sull'MVP 1, partendo dal task 1 di `specs/mvp-01-iscrizione-base/tasks.md`.

## Dubbi aperti

1. Dividere l'MVP 1 in 1a (tutto in locale, task 1-11) e 1b (deploy Azure, task 12-13)?
2. Branch: la Parte B prevede `feat/mvp-NN-<slug>`, ma la sessione cloud corrente può pushare solo sul branch assegnato. Quale usare?
3. L'admin deve fare login già nell'MVP 1: si anticipa il magic link con cookie da 14 giorni dall'MVP 2, con una pagina personale solo in lettura.
4. Scadenza del blocco: N x 24 ore esatte oppure fine giornata (23:59 Europe/Rome) dell'N-esimo giorno? Proposta: fine giornata.
5. Email già iscritta: con prenotazione attiva si reinvia il link; con prenotazione scaduta se ne crea una nuova?
6. Pagamento registrato su prenotazione scaduta: riattivarla solo se c'è ancora posto, altrimenti registrare il pagamento e avvisare l'admin?
7. Email di conferma pagamento già nell'MVP 1 (in console)?
