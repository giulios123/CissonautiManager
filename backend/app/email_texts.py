"""Texts of the emails, in Italian and English. Merged into the catalog of app.i18n."""

EMAIL_MESSAGES: dict[str, dict[str, str]] = {
    "email.greeting": {"it": "Ciao {first_name},", "en": "Hi {first_name},"},
    "email.pay_default": {
        "it": "- Ti scriveremo le istruzioni appena possibile.",
        "en": "- We'll write to you with the instructions as soon as possible.",
    },
    "email.personal_link": {
        "it": "Il tuo link personale (vale 10 minuti):\n{link}",
        "en": "Your personal link (valid for 10 minutes):\n{link}",
    },
    "email.manage_link": {
        "it": "Per vedere o modificare la tua iscrizione: {link}",
        "en": "To view or change your registration: {link}",
    },
    "email.your_slots": {"it": "I tuoi slot:", "en": "Your slots:"},
    "email.presence.heading.one": {"it": "1 giorno di presenza:", "en": "1 day of attendance:"},
    "email.presence.heading.other": {
        "it": "{count} giorni di presenza:",
        "en": "{count} days of attendance:",
    },
    "email.presence.note": {
        "it": "Giornate complete, salvo fasce indicate.",
        "en": "Full days, except where periods are listed.",
    },
    "email.presence.hours": {"it": "Orari:", "en": "Times:"},
    "email.how_to_pay": {"it": "Come pagare:", "en": "How to pay:"},
    "email.reference": {"it": "Causale: {code}", "en": "Payment reference: {code}"},
    "email.hold_until": {
        "it": (
            "Il posto è bloccato fino al {deadline}: senza pagamento entro quella data si libera."
        ),
        "en": ("Your place is held until {deadline}: without payment by then it will be released."),
    },
    "email.registration.hold_until": {
        "it": (
            "Il posto è bloccato fino al {deadline}: entro quella data devi coprire la quota "
            "necessaria a confermare."
        ),
        "en": (
            "Your place is held until {deadline}: by then you must cover the fee needed to "
            "confirm it."
        ),
    },
    "email.waitlist_section": {
        "it": (
            "Sei in lista d'attesa per:\n{slots}\n"
            "Se si libera un posto ti scriviamo e lo slot diventa tuo."
        ),
        "en": (
            "You are on the waitlist for:\n{slots}\n"
            "If a place frees up we'll write to you and the slot becomes yours."
        ),
    },
    # --- cancellation
    "email.cancellation.subject": {
        "it": "Disdetta al {event}",
        "en": "Cancellation for {event}",
    },
    "email.cancellation.body": {
        "it": "abbiamo registrato la tua disdetta e i tuoi posti sono stati liberati.",
        "en": "we have recorded your cancellation and your places have been released.",
    },
    "email.cancellation.removed": {
        "it": (
            "Non risultano pagamenti, quindi non devi fare altro: l'iscrizione è stata "
            "annullata. Se cambi idea puoi iscriverti di nuovo quando vuoi."
        ),
        "en": (
            "We have no payments on record, so there is nothing else to do: the registration "
            "has been cancelled. If you change your mind you can sign up again at any time."
        ),
    },
    "email.cancellation.paid": {
        "it": (
            "Ci sono pagamenti registrati: chi organizza ti scriverà per il rimborso "
            "e segnerà la disdetta come conclusa."
        ),
        "en": (
            "There are payments on record: the organizers will write to you about the refund "
            "and will mark the cancellation as completed."
        ),
    },
    "email.cancellation.left_waitlist": {
        "it": "Sei uscito anche dalle liste d'attesa in cui eri.",
        "en": "You have also left the waitlists you were on.",
    },
    # --- registration confirmation
    "email.registration.subject": {
        "it": "Iscrizione al {event}",
        "en": "Registration for {event}",
    },
    "email.registration.thanks": {
        "it": "grazie per esserti iscritto al {event}!",
        "en": "thank you for signing up for {event}!",
    },
    "email.registration.fee": {
        "it": "Quota da versare: {amount}",
        "en": "Amount to pay: {amount}",
    },
    "email.registration.fee_split": {
        "it": "Quota di partecipazione: {amount}",
        "en": "Registration fee: {amount}",
    },
    "email.registration.total": {
        "it": "Totale dovuto all'organizzazione: {amount}",
        "en": "Total due to the organisers: {amount}",
    },
    "email.registration.confirmation_due": {
        "it": "Dovuto per confermare la prenotazione: {amount}",
        "en": "Amount due to confirm your booking: {amount}",
    },
    "email.registration.confirmed": {
        "it": "la tua prenotazione al {event} è confermata.",
        "en": "your booking for {event} is confirmed.",
    },
    "email.registration.balance": {
        "it": "Resta da saldare all'organizzazione: {amount}",
        "en": "Still due to the organisers: {amount}",
    },
    "email.registration.credit": {
        "it": "Credito presso l'organizzazione: {amount}",
        "en": "Credit with the organisers: {amount}",
    },
    "email.registration.no_balance": {
        "it": "Non resta altro da pagare all'organizzazione.",
        "en": "There is no remaining balance due to the organisers.",
    },
    "email.registration.extras_later": {
        "it": "Pranzi, cene e attività possono essere pagati dopo.",
        "en": "Lunches, dinners and activities can be paid later.",
    },
    # --- waitlist
    "email.waitlist_joined.subject": {
        "it": "Sei in lista d'attesa al {event}",
        "en": "You are on the waitlist for {event}",
    },
    "email.waitlist_joined.body": {
        "it": "gli slot che hai scelto sono al completo: ti abbiamo messo in lista d'attesa.",
        "en": "the slots you chose are full: we have put you on the waitlist.",
    },
    "email.waitlist_joined.nothing_to_pay": {
        "it": "Finché non si libera un posto non devi pagare nulla.",
        "en": "You don't have to pay anything until a place frees up.",
    },
    "email.already.subject": {
        "it": "Sei già iscritto al {event}",
        "en": "You are already registered for {event}",
    },
    "email.already.body": {
        "it": "risulti già iscritto: non abbiamo creato una nuova iscrizione.",
        "en": "you are already registered: we have not created a new registration.",
    },
    "email.already.link": {
        "it": "Per vedere la tua pagina personale apri questo link (vale 10 minuti):\n{link}",
        "en": "To see your personal page open this link (valid for 10 minutes):\n{link}",
    },
    # --- magic link
    "email.magic.subject": {
        "it": "Il tuo link di accesso al {event}",
        "en": "Your sign-in link for {event}",
    },
    "email.magic.body": {
        "it": "apri questo link per entrare.",
        "en": "open this link to sign in.",
    },
    "email.magic.link": {
        "it": "{link}\n\nIl link vale 10 minuti e si può riaprire in quel tempo.",
        "en": "{link}\n\nThe link is valid for 10 minutes and can be reopened in that time.",
    },
    # --- payment received
    "email.payment.subject": {
        "it": "Pagamento ricevuto: sei dentro al {event}!",
        "en": "Payment received: you're in for {event}!",
    },
    "email.payment.body": {
        "it": "abbiamo registrato il tuo pagamento: la tua iscrizione al {event} è confermata.",
        "en": "we have recorded your payment: your registration for {event} is confirmed.",
    },
    "email.payment.amount": {
        "it": "Pagamento registrato: {amount}",
        "en": "Payment recorded: {amount}",
    },
    "email.payment.see_you": {"it": "Ci vediamo presto!", "en": "See you soon!"},
    "email.booking_confirmation.subject": {
        "it": "La tua iscrizione al {event} è confermata",
        "en": "Your registration for {event} is confirmed",
    },
    "email.booking_confirmation.body": {
        "it": "la quota necessaria è coperta e la tua iscrizione al {event} è confermata.",
        "en": "the required fee is covered and your registration for {event} is confirmed.",
    },
    "email.booking_confirmation.fee": {
        "it": "Quota di partecipazione coperta: {amount}",
        "en": "Registration fee covered: {amount}",
    },
    "email.booking_confirmation.fee_uncovered": {
        "it": "Quota di partecipazione: {amount}",
        "en": "Registration fee: {amount}",
    },
    "email.booking_confirmation.balance": {
        "it": "Resta da saldare all'organizzazione: {amount}",
        "en": "Still due to the organisers: {amount}",
    },
    "email.booking_confirmation.total": {
        "it": "Totale dovuto all'organizzazione: {amount}",
        "en": "Total due to the organisers: {amount}",
    },
    "email.booking_confirmation.credit": {
        "it": "Credito presso l'organizzazione: {amount}",
        "en": "Credit with the organisers: {amount}",
    },
    "email.booking_confirmation.no_balance": {
        "it": "Non resta altro da pagare all'organizzazione.",
        "en": "There is no remaining balance due to the organisers.",
    },
    "email.booking_confirmation.access": {
        "it": "Per vedere la tua iscrizione accedi alla pagina personale: {link}",
        "en": "To view your registration, open your personal page: {link}",
    },
    "email.booking_confirmation.extras_later": {
        "it": "Pranzi, cene e attività possono essere pagati dopo.",
        "en": "Lunches, dinners and activities can be paid later.",
    },
    # --- reminders
    "email.reminder.subject_final": {
        "it": "Ultimo promemoria: il tuo posto al {event} sta per liberarsi",
        "en": "Last reminder: your place at {event} is about to be released",
    },
    "email.reminder.subject_mid": {
        "it": "Promemoria: il tuo posto al {event}",
        "en": "Reminder: your place at {event}",
    },
    "email.reminder.intro_final": {
        "it": "mancano meno di 24 ore alla scadenza del blocco del tuo posto.",
        "en": "less than 24 hours left before your place is released.",
    },
    "email.reminder.intro_mid": {
        "it": "ti ricordiamo che il tuo posto è bloccato.",
        "en": "a reminder that your place is being held.",
    },
    "email.reminder.balance": {
        "it": "Ancora da versare: {amount}",
        "en": "Still to pay: {amount}",
    },
    "email.reminder.confirmation_balance": {
        "it": "Ancora da versare per confermare: {amount}",
        "en": "Still due to confirm: {amount}",
    },
    "email.reminder.already_paid": {
        "it": (
            "Se hai già pagato, ignora questo messaggio: registreremo il pagamento appena "
            "possibile."
        ),
        "en": (
            "If you have already paid, please ignore this message: we'll record the payment "
            "as soon as possible."
        ),
    },
    # --- seat freed from the waitlist
    "email.promoted.subject": {
        "it": "Si è liberato un posto al {event}",
        "en": "A place has opened up at {event}",
    },
    "email.promoted.body": {
        "it": "si è liberato un posto ed è tuo.",
        "en": "a place has opened up and it's yours.",
    },
    "email.promoted.slot": {
        "it": "Slot assegnato: {label}",
        "en": "Slot assigned: {label}",
    },
    "email.promoted.fee": {"it": "Quota: {amount}", "en": "Fee: {amount}"},
    "email.promoted.stays_confirmed": {
        "it": "La tua iscrizione resta confermata: versa la differenza con le stesse istruzioni.",
        "en": (
            "Your registration stays confirmed: pay the difference following the same instructions."
        ),
    },
}
