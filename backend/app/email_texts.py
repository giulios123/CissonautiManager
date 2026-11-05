"""Texts of the emails, in Italian and English. Merged into the catalog of app.i18n."""

EMAIL_MESSAGES: dict[str, dict[str, str]] = {
    "email.greeting": {"it": "Ciao {first_name},", "en": "Hi {first_name},"},
    "email.pay_default": {
        "it": "- Ti scriveremo le istruzioni appena possibile.",
        "en": "- We'll write to you with the instructions as soon as possible.",
    },
    "email.personal_link": {
        "it": "Il tuo link personale (vale 30 minuti, si usa una volta sola):\n{link}",
        "en": "Your personal link (valid for 30 minutes, single use):\n{link}",
    },
    "email.manage_link": {
        "it": "Per vedere o modificare la tua iscrizione: {link}",
        "en": "To view or change your registration: {link}",
    },
    "email.your_slots": {"it": "I tuoi slot:", "en": "Your slots:"},
    "email.how_to_pay": {"it": "Come pagare:", "en": "How to pay:"},
    "email.reference": {"it": "Causale: {code}", "en": "Payment reference: {code}"},
    "email.hold_until": {
        "it": (
            "Il posto è bloccato fino al {deadline}: senza pagamento entro quella data si libera."
        ),
        "en": ("Your place is held until {deadline}: without payment by then it will be released."),
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
        "it": (
            "risulti già iscritto: non abbiamo creato una nuova iscrizione.\n"
            "Per vedere la tua pagina personale apri questo link "
            "(vale 30 minuti, si usa una volta sola):\n{link}"
        ),
        "en": (
            "you are already registered: we have not created a new registration.\n"
            "To see your personal page open this link "
            "(valid for 30 minutes, single use):\n{link}"
        ),
    },
    # --- magic link
    "email.magic.subject": {
        "it": "Il tuo link di accesso ai Cissonauti",
        "en": "Your Cissonauti sign-in link",
    },
    "email.magic.body": {
        "it": (
            "apri questo link per entrare: {link}\n\n"
            "Il link vale 30 minuti e si può usare una sola volta."
        ),
        "en": (
            "open this link to sign in: {link}\n\n"
            "The link is valid for 30 minutes and can be used only once."
        ),
    },
    # --- payment received
    "email.payment.subject": {
        "it": "Pagamento ricevuto: sei dentro!",
        "en": "Payment received: you're in!",
    },
    "email.payment.body": {
        "it": (
            "abbiamo registrato il tuo pagamento ({amount}): "
            "la tua iscrizione al {event} è confermata."
        ),
        "en": (
            "we have recorded your payment ({amount}): your registration for {event} is confirmed."
        ),
    },
    "email.payment.see_you": {"it": "Ci vediamo presto!", "en": "See you soon!"},
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
        "it": "mancano meno di 24 ore: il tuo posto è bloccato fino al {deadline}.",
        "en": "less than 24 hours left: your place is held until {deadline}.",
    },
    "email.reminder.intro_mid": {
        "it": "ti ricordiamo che il tuo posto è bloccato fino al {deadline}.",
        "en": "a reminder that your place is held until {deadline}.",
    },
    "email.reminder.release": {
        "it": "Senza pagamento entro quella data il posto si libera.",
        "en": "Without payment by then the place will be released.",
    },
    "email.reminder.balance": {
        "it": "Ancora da versare: {amount}",
        "en": "Still to pay: {amount}",
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
        "it": "si è liberato un posto ed è tuo: {label}.",
        "en": "a place has opened up and it's yours: {label}.",
    },
    "email.promoted.fee": {"it": "Quota: {amount}", "en": "Fee: {amount}"},
    "email.promoted.stays_confirmed": {
        "it": "La tua iscrizione resta confermata: versa la differenza con le stesse istruzioni.",
        "en": (
            "Your registration stays confirmed: "
            "pay the difference following the same instructions."
        ),
    },
}
