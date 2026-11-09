# MVP 24 · Dettagli e note delle attività

**Stato:** implementata nel branch `feat/mvp-24-dettagli-attivita`; resta da completare il collaudo SQL Server e manuale. P2, C1 e C3. Indipendente dall’MVP 23 e basata sul modello attività dell’MVP 16. Decisioni di riferimento D-049 e D-091.

## US-24.1 · Leggere una scheda attività

- Quando apro un’attività disponibile o già scelta, allora vedo titolo e descrizione completi, giorno, fascia, orari strutturati disponibili, costo, destinatario, istruzioni e capienza/posti liberi quando prevista.
- Quando una persona è presente solo in una fascia, allora la scheda mantiene i controlli di adesione e la capienza già applicati dall’attività.
- Quando leggo riepiloghi o CSV che riportano già un’attività, allora il titolo localizzato resta riconoscibile e non è sostituito dall’identificativo tecnico.
- Quando un’attività legacy non ha orari strutturati, allora la scheda usa l’etichetta legacy se presente e non inventa orari.

## US-24.2 · Gestire contenuti bilingui

- Quando creo un’attività o modifico titolo o descrizione, allora inserisco titolo e descrizione non vuoti sia in italiano sia in inglese.
- Quando modifico titolo o descrizione, allora devo fornire entrambe le lingue; errori di validazione sono spiegati in IT/EN.
- Quando apro un’attività legacy monolingue, allora il testo originale resta visibile come fallback in entrambe le lingue e l’admin vede che le traduzioni sono da completare.
- Quando correggo soltanto orari, prezzo, capienza, destinatario o note di un’attività legacy, allora posso salvare senza dover prima riscrivere i testi.

## US-24.3 · Gestire note interne con cronologia

- Quando un admin crea o modifica la nota interna, allora la scheda mostra il testo corrente e lo storico con contenuto, autore e data/ora.
- Quando il salvataggio fallisce, allora né la nota corrente né lo storico risultano aggiornati parzialmente.
- Quando l’attività non ha note, allora la scheda resta utilizzabile senza contenuto fittizio.
- Quando un admin esporta il CSV attività, allora la nota corrente compare una volta per attività anche senza iscritti.
- Quando una persona non admin consulta API, email, riepilogo o export, allora la nota e lo storico non sono inclusi nei payload.
- Quando una persona anonima richiede direttamente endpoint o URL CSV admin, allora riceve rifiuto di autorizzazione.

## Modifiche a domain.md

Proposta da approvare: le nuove attività e le modifiche a titolo o descrizione richiedono il testo in IT e EN; i testi legacy monolingui sono conservati e mostrati come fallback finché completati. Le note interne sono dati amministrativi e non vengono mai esposte a partecipanti o anonimi. Il CSV admin attività include la nota corrente anche quando non ci sono iscritti; lo storico è consultabile nella scheda admin.

## Fuori perimetro

Conversione contributi in attività, presenze esterne, nuove regole di capienza/adesione, modifiche ai destinatari, note dei partecipanti e nuove modalità di esportazione oltre al CSV admin attività esistente.
