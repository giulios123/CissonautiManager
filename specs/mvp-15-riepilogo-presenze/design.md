# Design · Riepiloghi compatti delle presenze

## Interfacce e flussi

- Un componente web raggruppa fasce prenotate per data. Mattina+pomeriggio contano come giornata completa ai fini della sola visualizzazione; il dato prenotato resta invariato.
- Le risposte `BookingSummary` e `BookingView` espongono l'orario configurato di ciascuna fascia nei giorni prenotati, inclusa la sera derivata.
- Le email di iscrizione, pagamento e assegnazione di un posto usano la stessa forma testuale e un'alternativa HTML con le fasce parziali in corpo secondario.
- La registrazione mostra un link «Modifica presenze» con destinazione al calendario. La pagina personale pone modifica vicino al riepilogo.
- Gli orari si raggruppano per fascia e intervallo; se gli intervalli variano, si mostrano le date associate.

## Dati e compatibilità

- Nessuna modifica al database o alle regole di prenotazione.
- La lista d'attesa rimane in una sezione distinta e non completa una giornata prenotata.
- La versione testuale delle email resta disponibile per client senza HTML.

## Guida

Aggiornare iscrizione e modifica presenze in italiano e inglese.
