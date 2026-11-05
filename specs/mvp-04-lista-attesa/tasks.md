# MVP 4 · Lista d'attesa · Task

Branch di implementazione: `claude/quirky-meitner-qn9hwh` (vincolo di push della sessione, come per MVP 2 e 3). Parte dopo la conferma della spec.

**Dimensione**: 9 task.

- [x] **1. Migrazione 0005**: `edition.waitlist_percent`, tabella `waitlist_entry`.
  Test: upgrade e downgrade da zero; default 20 sulle edizioni esistenti.
- [x] **2. Regole pure**: `waitlist_limit`, `can_join`, `queue`, `position`, `hold_after_promotion`, `promotion_kind`.
  Test: 25 al 20% fa 5, 3 al 20% fa 0, sera senza lista; ogni motivo di rifiuto di `can_join`; ordine per arrivo a parità di orario; la scadenza non si accorcia mai; giorno passato rifiutato.
- [x] **3. Lista dalla pagina personale**: servizio `join`/`leave`, `POST` e `DELETE /api/me/waitlist`, `GET /api/me` con posizione, sezione nella pagina.
  Test: ingresso con slot pieno e lista aperta; rifiuto con lista completa, slot libero, slot già prenotato, doppia voce; uscita che fa salire gli altri; pagina con sole voci in lista.
- [x] **4. Lista dal modulo pubblico**: `waitlist_slot_ids` in `register`, persona senza prenotazione con testi legali sulla voce, email, riepilogo nel modulo.
  Test: slot misti (prenotazione più voci); soli slot in lista (nessuna `Booking`, testi salvati, magic link inviato); lista riempita o slot liberato nel frattempo (nessun salvataggio); persona già in lista trattata come D-005.
- [x] **5. Servizio di promozione ed email**: `promote_freed` nei tre casi (in attesa, confermata, nuova prenotazione).
  Test: in attesa con importo ricalcolato e scadenza allungata, promemoria ricalcolati come una proroga; confermata che resta tale con saldo positivo e compare in «Da verificare»; nuova prenotazione con testi legali della voce; due posti liberi promuovono due persone; voci della stessa persona su altri slot intatte; giorno passato senza promozione; email inviata dopo il commit.
- [x] **6. Agganci**: disdetta, cambio slot (partecipante e admin), disdetta admin, aumento di capienza; chiusura `booked` e `cancelled` delle voci.
  Test: un caso per ogni evento che libera un posto; la disdetta chiude le voci e lo scrive nell'email; chi prenota da sé lo slot esce dalla lista; «forza» dell'admin non promuove nessuno.
- [x] **7. Job orario**: passo di promozione dopo le scadenze in `send_reminders`.
  Test: prenotazione scaduta che libera il posto al primo in lista; due esecuzioni sovrapposte non assegnano lo stesso posto due volte; riepilogo nei log.
- [x] **8. Pannello admin**: coda in «Giorni e slot» e nel CSV, rimozione con cronologia, voci nella scheda, persone solo in lista in «Persone».
  Test: CSV con posizione; rimozione senza email e con cronologia; 403 per un partecipante; filtro «in lista».
- [x] **9. Impostazioni e chiusura**: percentuale in Impostazioni; lint e test verdi, migrazioni da zero, Memory Bank, README, descrizione PR con checklist per organizzatori.
  Test: percentuale fuori da 0-100 rifiutata; il nuovo limite vale per i nuovi ingressi.

## Da verificare a mano

- Riempire uno slot con un'edizione di prova e mettersi in lista dal modulo dentro l'iframe di Google Sites.
- Ricevere davvero l'email «si è liberato un posto» dopo una disdetta.
- Lasciar scadere una prenotazione e controllare che entro un'ora il posto passi al primo in lista (serve il job in produzione, task 9 dell'MVP 2).
