"""The edition report as rows for a CSV: «sezione; voce; confermate; in attesa; totale».

Rows without a split (a plain count or an amount) fill only the last column. Allergies are health
data and appear only as a number, never with names.
"""

from app.csv_export import Amount, Cell
from app.domain.report import EditionReport, Split
from app.i18n import channel_label, tr
from app.services.edition import PAYMENT_CHANNELS
from app.timefmt import format_activity, meal_label, period_label, status_label

HEADER = ["Sezione", "Voce", "Confermate", "In attesa di pagamento", "Totale"]
DIET_LABELS = {
    "omnivore": "onnivoro",
    "vegetarian": "vegetariano",
    "vegan": "vegano",
    "none": "non indicato",
}
CONTRIBUTION_LABELS = {"talk": "Talk", "topic": "Temi per l'unconference", "skill": "Competenze"}


def header() -> list[str]:
    return [tr(cell) for cell in HEADER]


Row = list[Cell]


def _split(section: str, label: str, value: Split) -> Row:
    return [tr(section), tr(label), value.confirmed, value.pending, value.total]


def _plain(section: str, label: str, value: Cell) -> Row:
    return [tr(section), tr(label), None, None, value]


def _decimal(value: float) -> str:
    return f"{value:.1f}".replace(".", ",")


def report_rows(report: EditionReport) -> list[Row]:
    rows: list[Row] = []

    section = "Iscrizioni"
    for status, count in report.enrollment.by_status.items():
        rows.append(_plain(section, f"{tr('Prenotazioni')}: {status_label(status).lower()}", count))
    rows.append(_plain(section, "Persone con un posto", report.enrollment.people_with_seat))

    section = "Presenze"
    for slot in report.presence.slots:
        label = f"{slot.day:%d/%m/%Y} {period_label(slot.period).lower()}"
        rows.append(_split(section, label, slot.present))
        if slot.derived:
            rows.append(
                _plain(section, f"{label}, {tr("di cui sera dell'intero giorno")}", slot.derived)
            )
    rows.append(_plain(section, "Picco di presenti in uno slot", report.presence.peak))
    rows.append(
        _plain(
            section,
            "Media di presenti per slot di mattina e pomeriggio",
            _decimal(report.presence.average_per_daytime_slot),
        )
    )
    rows.append(_split(section, "Giorni-persona", report.presence.person_days))

    section = "Pasti"
    for day in report.meals.days:
        rows.append(_split(section, f"{meal_label('lunch')} {day.day:%d/%m/%Y}", day.lunches))
        rows.append(_split(section, f"{meal_label('dinner')} {day.day:%d/%m/%Y}", day.dinners))
    rows.append(_split(section, "Pranzi in totale", report.meals.lunches))
    rows.append(_split(section, "Cene in totale", report.meals.dinners))
    for key, count in report.meals.lunch_diets.items():
        rows.append(
            _plain(
                section,
                f"{tr('Pranzi')}, {tr('regime')} {tr(DIET_LABELS[key])}: {tr('persone')}",
                count,
            )
        )
    for key, count in report.meals.dinner_diets.items():
        rows.append(
            _plain(
                section,
                f"{tr('Cene')}, {tr('regime')} {tr(DIET_LABELS[key])}: {tr('persone')}",
                count,
            )
        )
    rows.append(
        _plain(section, "Persone con allergie o intolleranze", report.meals.people_with_allergies)
    )

    section = "Attività"
    if not report.activities:
        rows.append(_plain(section, "Nessuna attività", 0))
    for activity in report.activities:
        title = format_activity(activity.title, activity.day, activity.period)
        rows.append(_split(section, title, activity.joined))
        rows.append(
            _plain(section, f"{tr('Prezzo')}: {activity.title}", Amount(activity.price_cents))
        )
        capacity = tr("senza limite") if activity.capacity is None else activity.capacity
        rows.append(_plain(section, f"{tr('Capienza')}: {activity.title}", capacity))
        rows.append(
            _plain(
                section,
                f"{tr('Incasso atteso')}: {activity.title}",
                Amount(activity.expected_cents),
            )
        )

    section = "Contributi"
    for kind, count in report.contributions.items():
        rows.append(_plain(section, tr(CONTRIBUTION_LABELS.get(kind, kind)), count))

    section = "Lista d'attesa"
    wl = report.waitlist
    rows += [
        _plain(section, "Ancora in lista", wl.waiting),
        _plain(section, "Promossi", wl.promoted),
        _plain(
            section,
            "Promossi che erano +1 verificati al momento della promozione",
            wl.promoted_plus_one,
        ),
        _plain(section, "Usciti da soli", wl.left),
        _plain(section, "Tolti da un admin", wl.removed),
        _plain(section, "Annullati per disdetta", wl.cancelled),
        _plain(section, "Prenotati per altra via", wl.booked),
    ]

    section = "Incassi"
    money = report.revenue
    rows += [
        _plain(section, "Totale dovuto", Amount(money.due_cents)),
        _plain(section, "Dovuto: quota di partecipazione", Amount(money.due_fee_cents)),
        _plain(section, "Dovuto: pasti", Amount(money.due_meals_cents)),
        _plain(section, "Dovuto: attività", Amount(money.due_activities_cents)),
        _plain(section, "Dovuto: differenza di prezzi", Amount(money.due_difference_cents)),
        _plain(section, "Versato", Amount(money.paid_cents)),
    ]
    for channel, cents in money.paid_by_channel.items():
        name = channel_label(channel, PAYMENT_CHANNELS.get(channel, channel))
        rows.append(
            _plain(
                section,
                f"{tr('Versato')}: {name}",
                Amount(cents),
            )
        )
    rows += [
        _plain(section, "Rimborsato", Amount(money.refunded_cents)),
        _plain(section, "Netto (versato meno rimborsato)", Amount(money.net_cents)),
        _plain(section, "Ancora da incassare", Amount(money.to_collect_cents)),
        _plain(section, "Crediti da restituire", Amount(money.credits_cents)),
        _plain(section, "Disdette da rimborsare", Amount(money.to_refund_cents)),
    ]
    return rows
