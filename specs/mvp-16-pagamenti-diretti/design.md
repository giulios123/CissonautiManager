# Design

Migrazione 0015: activity.starts_at/ends_at UTC nullable per i dati precedenti, payment_mode e payment_instructions; meal_setting per edizione/data/tipo con prezzo e istruzioni. Default organizer e nessun ricalcolo al rilascio. L’API accetta orari locali Europe/Rome (start_time/end_time), genera time_label e conserva quello precedente per i record non convertiti. Fine 00:00 indica la mezzanotte successiva.

POST/PATCH /api/admin/activities gestisce orari e incasso; PUT /api/admin/meals/{date}/{kind} configura il singolo pasto. Le viste restituiscono price_cents, payment_mode, payment_instructions e collectable_cents. La modalità provider richiede istruzioni e costo; organizer sui pasti usa i prezzi generali.

Le scritture HTTP prendono prima il lock dell’edizione, poi i lock esistenti delle prenotazioni/attività. Anche la promozione del job orario prende prima quello dell’edizione. Il ricalcolo interessa soltanto le prenotazioni attive collegate alla voce modificata, conserva scadenza e versamenti, conferma quelle già coperte e invia la conferma dopo il commit. Scadute e chiuse restano intatte.

Un’unica politica di incasso alimenta calcolo backend, viste, anteprime e report. AdminActivities usa selettori ore/minuti e modalità d’incasso; AdminMeals aggiunge configurazione per ciascun pranzo/cena. I dettagli restano visibili nella pagina personale e nella scheda admin. Nessun tracciamento dei versamenti all’erogatore o rimborso automatico.

Test: dominio, API e transizioni dei saldi, migrazioni con dati precedenti, componenti e percorsi nelle due lingue. Verifica manuale mobile e desktop. Test SQL Server in CI se Docker non è accessibile localmente.
