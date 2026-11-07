# D5 · Riscontro sui promemoria di pagamento

**Esito dell'ispezione statica del 7 novembre 2026:** esistono già due promemoria automatici. Non è stata interrogata Azure né inviata posta. La Memory Bank registra ancora verifiche di job/recapito reali pendenti; la presenza del codice non prova che l'ultima produzione li esegua correttamente.

## Quando e a chi

| Aspetto | Comportamento verificato nel repository |
|---|---|
| Esecutore | Azure Container Apps Job, stessa immagine dell'app, comando `python -m app.jobs.send_reminders`. |
| Frequenza | Cron `0 * * * *`, UTC: una volta ogni ora, anche con app a zero repliche. La consegna non è garantita al minuto della soglia. |
| Primo invio | A metà fra `hold_started_at` e `hold_expires_at`. Con blocco di 72 ore: dopo 36 ore. |
| Secondo invio | Da 24 ore prima della scadenza. Con blocco sotto le 48 ore: solo il primo; se il job arriva tardi quando sono dovuti entrambi: solo quello finale. |
| Destinatari | Email del partecipante del booking in `in_attesa_pagamento`, non scaduto e con pagamenti validi inferiori al totale oggi usato come dovuto. Nessun sollecito per sole liste d'attesa, confermate, scadute, disdette o rimborsate. |
| Importo attuale | `booking.amount_due_cents - paid_total(booking)`: oggi include gli extra organizzazione, esclude pagamenti annullati e costi diretti al fornitore. B1 dovrà usare il residuo della sola quota per il posto. |
| Lingua | `participant.locale`, IT o EN. |
| Ripetizioni | Marcatura per tipo prima dell'invio con UPDATE condizionato sullo stato ancora valido. Un errore d'invio non è ritentato: compromesso D-016. Non è una garanzia di consegna. |
| Riattivazione/proroga | Riattivazione apre un nuovo blocco e riavvia i promemoria; una proroga conserva o azzera le marche secondo le nuove soglie future (D-024). |

## Testo standard

| Parte | Italiano | Inglese |
|---|---|---|
| Oggetto metà | Promemoria: il tuo posto al {event} | Reminder: your place at {event} |
| Introduzione metà | ti ricordiamo che il tuo posto è bloccato. | a reminder that your place is being held. |
| Oggetto finale | Ultimo promemoria: il tuo posto al {event} sta per liberarsi | Last reminder: your place at {event} is about to be released |
| Introduzione finale | mancano meno di 24 ore alla scadenza del blocco del tuo posto. | less than 24 hours left before your place is released. |
| Residuo | Ancora da versare: {amount} | Still to pay: {amount} |
| Chiusura | Se hai già pagato, ignora questo messaggio: registreremo il pagamento appena possibile. | If you have already paid, please ignore this message: we'll record the payment as soon as possible. |

Il messaggio include anche saluto, scadenza formattata, causale personale, istruzioni dei canali attivi e link `/login`. Oggetto e introduzione possono essere sostituiti dall'admin per lingua e per edizione (`reminder_mid`, `reminder_final`, MVP 14); il blocco dati resta automatico. I testi personalizzati effettivi del database di produzione non sono noti a questa ispezione.

Il job esegue inoltre promozione delle liste d'attesa e recupero delle email di conferma pagamento differite dall'MVP 10: queste ultime non sono ulteriori promemoria di pagamento.

## Evidenze riproducibili

- `backend/app/domain/reminders.py`: `due_reminder` e `reminders_to_keep_after_extension`, soglie e sovrapposizioni.
- `backend/app/jobs/send_reminders.py`: selezione destinatari, importo, `_claim`, invio e funzioni aggiuntive.
- `backend/app/email/templates.py`: `reminder_email`, composizione del messaggio.
- `backend/app/email_texts.py`: chiavi `email.reminder.*`; catalogo importato da `i18n.py`.
- `backend/app/services/email_templates.py` e `backend/app/domain/email_template.py`: personalizzazione per tipo/lingua.
- `infra/main.bicep`: risorsa `reminderJob`, cron e comando; `infra/README.md`: consultazione della cronologia operativa.
- `backend/tests/test_reminders_job.py`, `test_domain_personal.py`, `test_i18n_emails.py`, `test_email_texts.py`: copertura esistente da consultare, **non rieseguita per questa modifica documentale**.

## Implicazione per i nuovi MVP

Non proporre un secondo scheduler. Nel P1 B1 aggiornare insieme filtro di copertura, residuo e messaggio affinché gli extra non minaccino la perdita del posto; mantenere frequenza e prevenzione duplicati. D4 rimane distinto e non estende questi invii senza una futura approvazione.
