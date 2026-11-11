"""Texts the organizers see that are written in Italian in the code: CSV headers, report labels,
payment-review reasons and system warnings. `LABELS_EN` gives the English version of each fixed
Italian label; `ADMIN_MESSAGES` are keyed messages merged into the catalog of app.i18n.
"""

LABELS_EN: dict[str, str] = {
    "Incasso": "Collection",
    "Istruzioni di pagamento": "Payment instructions",
    "Nota interna": "Internal note",
    "Organizzatori": "Organizers",
    "Erogatore": "Provider",
    "Coperto dalla quota di registrazione": "Covered by the registration fee",
    "Incasso dell’organizzazione": "Collected by the organisers",
    "Pagamento in loco al fornitore": "Pay the provider on site",
    "Tipo di incasso": "Collection type",
    # --- CSV file names
    "persone": "people",
    "giorni-slot": "days-slots",
    "pasti": "meals",
    "settimana": "week",
    "contributi": "contributions",
    "pagamenti-da-verificare": "payments-to-review",
    "attivita": "activities",
    "esterni": "guests",
    "report": "report",
    # --- CSV headers
    "Di cui esterni": "Of which guests",
    "Rimborsi su iscrizioni attive (compresi in Rimborsato)": (
        "Refunds on active bookings (included in Refunded)"
    ),
    "Valore esentato": "Value exempted",
    "Iscrizioni interne non paganti": "Internal, not paying bookings",
    "Esente": "Exempt",
    "Categoria": "Category",
    "Quota esente": "Fee exempt",
    "Ordinaria": "Ordinary",
    "Interno non pagante": "Internal, not paying",
    "Incassi esterni": "Guest payments",
    "Dovuto dagli esterni": "Due from guests",
    "Versato dagli esterni": "Paid by guests",
    "Restituito agli esterni": "Refunded to guests",
    "Netto esterni (versato meno restituito)": "Guests net (paid minus refunded)",
    "Ancora da incassare dagli esterni": "Still to collect from guests",
    "Crediti degli esterni da restituire": "Guest credits to return",
    "Totale evento": "Event total",
    "Incassato dall'evento (quote più esterni)": "Collected by the event (fees plus guests)",
    "movimenti-esterni": "guest-movements",
    "Data": "Date",
    "Importo": "Amount",
    "Canale": "Channel",
    "Nota": "Note",
    "Tipo di movimento": "Type of movement",
    "Motivo dell'annullo": "Reason for voiding",
    "Pagamento": "Payment",
    "Restituzione": "Refund",
    "Annullato": "Voided",
    "Valido": "Valid",
    "Esterno": "Guest",
    "Iscritto": "Participant",
    "Pagante": "Paying",
    "Riferimento": "Reference",
    "Giorno": "Day",
    "Slot": "Slot",
    "Orario": "Time",
    "Nome": "First name",
    "Cognome": "Last name",
    "Email": "Email",
    "Telefono": "Phone",
    "Codice": "Code",
    "Giorni": "Days",
    "Sere": "Evenings",
    "Stato": "Status",
    "Dovuto": "Due",
    "Quota di partecipazione": "Registration fee",
    "Residuo per confermare": "Remaining to confirm",
    "Versato": "Paid",
    "Saldo": "Balance",
    "Scadenza blocco": "Hold deadline",
    "Iscritto il": "Registered on",
    "Slot in lista d'attesa": "Waitlist slots",
    "Sera derivata": "Derived evening",
    "Posizione in lista": "Waitlist position",
    "+1 verificato": "Verified +1",
    "Invitato da": "Invited by",
    "Pasto": "Meal",
    "Regime": "Diet",
    "Allergie e intolleranze": "Allergies and intolerances",
    "Mattina": "Morning",
    "Pomeriggio": "Afternoon",
    "Sera": "Evening",
    "di cui sera derivata": "of which derived evening",
    "Persone": "People",
    "Pranzi": "Lunches",
    "Cene": "Dinners",
    "Adesioni alle attività": "Activity sign-ups",
    "Totale (persone diverse)": "Total (different people)",
    "Tipo": "Type",
    "Titolo": "Title",
    "Descrizione": "Description",
    "Proposto il": "Proposed on",
    "Nascosta agli altri": "Hidden from the others",
    "Attività create": "Activities created",
    "Consegne": "Deliveries",
    "Da consegnare": "To deliver",
    "Consegnato": "Delivered",
    "Consegnato (senza diritto attuale)": "Delivered (no longer entitled)",
    "Consegnato il": "Delivered on",
    "Consegnato da": "Delivered by",
    "Consegne annullate": "Annulled deliveries",
    "Sì": "Yes",
    "Motivo": "Reason",
    "Fascia": "Time slot",
    "Attività": "Activity",
    "Prezzo": "Price",
    # --- fixed cell values
    "sì": "yes",
    "no": "no",
    "In lista d'attesa": "On the waitlist",
    "Non indicato": "Not specified",
    "Onnivoro": "Omnivore",
    "Vegetariano": "Vegetarian",
    "Vegano": "Vegan",
    "Talk": "Talk",
    "Tema per l'unconference": "Unconference topic",
    "Competenza": "Skill",
    "Competenza cercata": "Skill wanted",
    # --- payments to review
    "Scaduta con pagamenti registrati": "Expired with recorded payments",
    "Confermata con una differenza da versare": "Confirmed with a difference to pay",
    "Confermata con un credito (ha versato in più)": "Confirmed with a credit (overpaid)",
    "Disdetta richiesta: da rimborsare": "Cancellation requested: to refund",
    "Disdetta richiesta senza pagamenti: da chiudere": (
        "Cancellation requested without payments: to close"
    ),
    "In attesa con un pagamento parziale": "Awaiting payment with a partial payment",
    # --- report (CSV)
    "Sezione": "Section",
    "Voce": "Entry",
    "Confermate": "Confirmed",
    "In attesa di pagamento": "Awaiting payment",
    "Totale": "Total",
    "Iscrizioni": "Registrations",
    "Prenotazioni": "Bookings",
    "Persone con un posto": "People with a place",
    "Presenze": "Attendance",
    "di cui sera dell'intero giorno": "of which evening of the whole day",
    "Picco di presenti in uno slot": "Peak attendance in a slot",
    "Media di presenti per slot di mattina e pomeriggio": (
        "Average attendance per morning and afternoon slot"
    ),
    "Giorni-persona": "Person-days",
    "Pasti": "Meals",
    "Pranzi in totale": "Lunches in total",
    "Cene in totale": "Dinners in total",
    "regime": "diet",
    "onnivoro": "omnivore",
    "vegetariano": "vegetarian",
    "vegano": "vegan",
    "non indicato": "not specified",
    "Persone con allergie o intolleranze": "People with allergies or intolerances",
    "Nessuna attività": "No activities",
    "Capienza": "Capacity",
    "Incasso atteso": "Expected income",
    "senza limite": "no limit",
    "Contributi": "Contributions",
    "Temi per l'unconference": "Unconference topics",
    "Competenze": "Skills",
    "Competenze cercate": "Skills wanted",
    "Lista d'attesa": "Waitlist",
    "Ancora in lista": "Still waiting",
    "Promossi": "Promoted",
    "Promossi che erano +1 verificati al momento della promozione": (
        "Promoted who were verified +1 at the time of promotion"
    ),
    "Usciti da soli": "Left on their own",
    "Tolti da un admin": "Removed by an admin",
    "Annullati per disdetta": "Cancelled because of a cancellation",
    "Prenotati per altra via": "Booked another way",
    "Incassi": "Income",
    "Totale dovuto": "Total due",
    "Dovuto: quota di partecipazione": "Due: participation fee",
    "Dovuto: pasti": "Due: meals",
    "Dovuto: attività": "Due: activities",
    "Dovuto: differenza di prezzi": "Due: price difference",
    "Rimborsato": "Refunded",
    "Netto (versato meno rimborsato)": "Net (paid minus refunded)",
    "Ancora da incassare": "Still to collect",
    "Crediti da restituire": "Credits to return",
    "Disdette da rimborsare": "Cancellations to refund",
}

ADMIN_MESSAGES: dict[str, dict[str, str]] = {
    "exemptions.not_active": {
        "it": "Le esenzioni valgono solo per una prenotazione in attesa o confermata",
        "en": "Exemptions apply only to a pending or confirmed booking",
    },
    "exemptions.invalid": {
        "it": "Categoria o voci non valide per questa prenotazione",
        "en": "Category or items not valid for this booking",
    },
    "exemptions.preview_changed": {
        "it": "La prenotazione è cambiata dopo l'anteprima: rifai l'anteprima prima di applicare",
        "en": "The booking changed after the preview: preview again before applying",
    },
    "booking_refund.not_active": {
        "it": "Si può rimborsare credito solo su una prenotazione in attesa o confermata",
        "en": "Credit can only be refunded on a pending or confirmed booking",
    },
    "booking_refund.too_high": {
        "it": "Il rimborso non può superare il credito (quanto versato oltre il totale dovuto)",
        "en": "The refund can't exceed the credit (what was paid beyond the total due)",
    },
    "booking_refund.invalid_amount": {
        "it": "L'importo deve essere maggiore di zero",
        "en": "The amount must be greater than zero",
    },
    "booking_refund.not_found": {
        "it": "Questo rimborso non esiste",
        "en": "This refund doesn't exist",
    },
    "booking_refund.already_voided": {
        "it": "Questo rimborso è già stato annullato",
        "en": "This refund has already been voided",
    },
    "payment.void_blocked_by_refund": {
        "it": (
            "Non si può annullare questo pagamento: i rimborsi registrati supererebbero "
            "quanto resta versato. Annulla prima il rimborso"
        ),
        "en": (
            "This payment can't be voided: the refunds on record would exceed what remains "
            "paid. Void the refund first"
        ),
    },
    "guests.has_movements": {
        "it": (
            "Questo esterno ha pagamenti o restituzioni registrati e non si può eliminare: "
            "puoi togliergli pasti e attività"
        ),
        "en": (
            "This guest has payments or refunds on record and can't be deleted: "
            "you can remove their meals and activities"
        ),
    },
    "guests.refund_too_high": {
        "it": "La restituzione non può superare il credito dell'esterno",
        "en": "The refund can't exceed the guest's credit",
    },
    "guests.invalid_amount": {
        "it": "L'importo deve essere maggiore di zero",
        "en": "The amount must be greater than zero",
    },
    "guests.movement_not_found": {
        "it": "Questo movimento non esiste",
        "en": "This movement doesn't exist",
    },
    "guests.movement_voided": {
        "it": "Questo movimento è già stato annullato",
        "en": "This movement has already been voided",
    },
    "guests.void_blocked": {
        "it": (
            "Non si può annullare questo pagamento: le restituzioni registrate supererebbero "
            "quanto resta versato. Annulla prima la restituzione"
        ),
        "en": (
            "This payment can't be voided: the refunds on record would exceed what remains paid. "
            "Void the refund first"
        ),
    },
    "guests.not_found": {
        "it": "Questo esterno non esiste",
        "en": "This guest doesn't exist",
    },
    "guests.duplicate": {
        "it": (
            "C'è già una persona con questo nome in questa edizione: {names}. "
            "Se è una persona diversa, conferma per salvare comunque."
        ),
        "en": (
            "Someone with this name is already in this edition: {names}. "
            "If it is a different person, confirm to save anyway."
        ),
    },
    "guests.consent_required": {
        "it": "Per salvare allergie o intolleranze serve il consenso raccolto dalla persona",
        "en": "To save allergies or intolerances you need the person's consent",
    },
    "guests.meals_invalid": {
        "it": "I pasti scelti non sono validi: devono cadere nei giorni dell'edizione",
        "en": "The chosen meals are not valid: they must fall on days of the edition",
    },
    "warn.over_capacity": {
        "it": "Attenzione: capienza superata in {labels}.",
        "en": "Warning: capacity exceeded in {labels}.",
    },
    "warn.dropped_meals": {
        "it": "Tolti anche i pasti senza più presenza: {meals}.",
        "en": "The meals without presence were removed too: {meals}.",
    },
    "warn.dropped_activities": {
        "it": "Tolte anche le attività senza più presenza: {names}.",
        "en": "The activities without presence were removed too: {names}.",
    },
    "warn.expired_with_payments": {
        "it": "Ci sono pagamenti registrati su una prenotazione scaduta.",
        "en": "There are payments recorded on an expired booking.",
    },
    "warn.revived_without_activities": {
        "it": (
            "Prenotazione riattivata senza queste attività, "
            "che nel frattempo sono al completo: {names}."
        ),
        "en": (
            "Booking reactivated without these activities, "
            "which have become full in the meantime: {names}."
        ),
    },
    "warn.payment_expired_already_active": {
        "it": (
            "Pagamento registrato, ma la persona ha già un'altra iscrizione attiva: "
            "questa prenotazione resta scaduta. Decidi come procedere con la persona."
        ),
        "en": (
            "Payment recorded, but the person already has another active registration: "
            "this booking stays expired. Decide how to proceed with the person."
        ),
    },
    "warn.payment_expired_no_room": {
        "it": (
            "Pagamento registrato, ma la prenotazione è scaduta e almeno uno slot è ormai pieno: "
            "la prenotazione resta scaduta. Decidi come procedere con la persona."
        ),
        "en": (
            "Payment recorded, but the booking has expired and at least one slot is now full: "
            "the booking stays expired. Decide how to proceed with the person."
        ),
    },
    "emailtpl.unknown_placeholder": {
        "it": "Segnaposto sconosciuto: {names}. Puoi usare solo: {allowed}.",
        "en": "Unknown placeholder: {names}. You can only use: {allowed}.",
    },
    "emailtpl.unknown_email": {
        "it": "Email sconosciuta.",
        "en": "Unknown email.",
    },
    "emailtpl.invalid_color": {
        "it": "Il colore deve essere scritto come #rrggbb, ad esempio #ffffff.",
        "en": "The color must be written as #rrggbb, for example #ffffff.",
    },
    "emailtpl.image_too_big": {
        "it": "L'immagine è troppo grande: al massimo 5 MB.",
        "en": "The image is too big: 5 MB at most.",
    },
    "emailtpl.image_wrong_format": {
        "it": "Formato non supportato: usa una foto JPEG, PNG o WebP.",
        "en": "Unsupported format: use a JPEG, PNG or WebP picture.",
    },
    "emailtpl.image_not_an_image": {
        "it": "Il file non è un'immagine valida.",
        "en": "The file is not a valid image.",
    },
    "emailtpl.test_sent": {
        "it": "Email di prova inviata a {email}.",
        "en": "Test email sent to {email}.",
    },
}
