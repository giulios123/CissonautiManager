# MVP 18 · Procedure manuali

**Da eseguire dopo l'implementazione, non eseguite ora.** Usare dati sintetici, orologio controllato dove serve e posta console/prova.

| Caso | Procedura | Esito atteso |
|---|---|---|
| M18-1 · Base/giorni/extra | Configurare base 10 €, giorno 1 €, due giorni, extra organizzazione 12 € e provider 15 €. | Quota 12 €, totale evento 24 €, provider separato. Stesso giorno conta una volta, sola sera conta; lista non aumenta la quota. |
| M18-2 · Pagamento parziale | A politica attiva, versare 5 € e poi 7 € dal dettaglio. | Prima attesa/residuo conferma 7 €/saldo 19 €; poi confermata/residuo conferma 0 €/saldo totale 12 €. Nessuna riga di versamento inventata. |
| M18-3 · Extra dopo conferma | Aggiungere un pasto/attività e poi un giorno a una confermata; aprire email/pagina IT/EN. | Stato stabile, saldo aggiornato, nessuna minaccia di perdita del posto; messaggio sugli extra pagabili dopo. |
| M18-4 · Annullo | Con quota 12 €, incasso 12+6 €. Annullare i 6 €, poi una parte dei versamenti che porta sotto 12 €. | Prima ancora confermata; poi attesa con nuovo blocco, annulli visibili e promemoria del nuovo blocco. |
| M18-5 · Sola lista e quota zero | Entrare soltanto in lista; promuovere con quota zero o creare booking gratuito. | Sola lista senza debito/booking; slot assegnato a quota zero già confermato senza Payment zero o ricevuta fittizia. |
| M18-6 · Scaduta | Provare pagamento/riattivazione su scaduta con posto pieno e con un'altra iscrizione attiva; ripetere con posto libero. | Pagamento conservato con avviso nei primi casi; nessun posto duplicato. Solo riattivazione ammissibile ricalcola e conferma sulla quota. |
| M18-7 · Preview legacy | Preparare attesa con sola quota coperta, confermata con credito, scaduta e disdetta. Cambiare un prezzo generale, leggere l'anteprima e annullare. | Differenze quota/totale/saldo/credito spiegate, scadute/chiuse escluse; annullo senza effetti né email. |
| M18-8 · Preview obsoleta | Aprire anteprima, poi cambiare pagamento/adesione/prezzo o far passare una scadenza da altra sessione; applicare il vecchio token. | 409 e nessuna applicazione parziale; una nuova anteprima mostra i dati correnti. |
| M18-9 · Attivazione | Applicare preview aggiornata e ripetere la stessa richiesta. Confrontare movimenti e stati. | Un solo passaggio; pagamenti/rimborsi identici, saldo/credito secondo anteprima, confermate stabili, sole attese valide coperte confermate e al massimo una notifica per nuovo stato. |
| M18-10 · Differita | Lasciare una conferma pagamento in coda a 30 s, attivare e far intervenire timer/job; ripetere con annullo entro 10 s. | La coda valida conserva l'orario e non duplica; annullo impedisce la notifica causata dal pagamento. Conferma da attivazione senza falso nuovo incasso. |
| M18-11 · Promemoria | Far scattare metà blocco/24 h per quota insoluta e per confermata con soli extra; cambiare lingua. | Solo la prima riceve residuo quota corretto; stessi criteri blocco corto/duplicati, nessun sollecito di posto alla seconda. |
| M18-12 · Amministrazione | Confrontare pagina personale, Da incassare, dettaglio, report e CSV IT/EN dopo ricalcoli e provider. | Totali e crediti riconciliati, extra ancora da incassare anche per confermate, costi provider fuori dagli incassi. |
| M18-13 · Accesso/UI | Tentare preview/apply come anonimo/partecipante; usare tastiera, telefono e zoom 200%. | Operazioni admin negate, importi e comandi leggibili; niente modale B3 o feature future introdotte. |

Annotare separatamente problemi di consegna reale e risultati dei test automatici. Nessun test o cambio di produzione viene eseguito dalla sola presenza di questa procedura.
