import csv
import io
from datetime import timedelta

from sqlalchemy import select

from app.models import STATUS_CANCEL_REQUESTED, STATUS_EXPIRED, BookingMeal, Slot
from tests.helpers import d
from tests.test_auth import login


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


def parse(response):
    return list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))


def eater(db, make_participant, make_booking, email, first, meals, diet=None, allergies=None, **kw):
    booking = make_booking(
        make_participant(email, first_name=first),
        [slot(db, 13), slot(db, 13, "evening")],
        **kw,
    )
    booking.meals = [BookingMeal(date=d(day), kind=kind) for day, kind in meals]
    booking.diet, booking.allergies = diet, allergies
    db.commit()
    return booking


def test_counts_names_diets_and_allergies_per_meal(
    admin_client, db, make_participant, make_booking
):
    eater(
        db,
        make_participant,
        make_booking,
        "ada@example.com",
        "Ada",
        [(13, "lunch"), (13, "dinner")],
        "vegan",
        "Arachidi",
    )
    eater(db, make_participant, make_booking, "bob@example.com", "Bob", [(13, "lunch")], "omnivore")
    eater(db, make_participant, make_booking, "cid@example.com", "Cid", [(13, "lunch")])
    days = admin_client.get("/api/admin/views/meals").json()["days"]
    assert [day["date"] for day in days] == [f"2026-07-{n}" for n in range(13, 18)]
    lunch, dinner = days[0]["meals"]
    assert (lunch["kind"], lunch["count"]) == ("lunch", 3)
    assert lunch["diets"] == {"omnivore": 1, "vegetarian": 0, "vegan": 1, "none": 1}
    ada = next(p for p in lunch["people"] if p["first_name"] == "Ada")
    assert ada["allergies"] == "Arachidi"
    assert (dinner["kind"], dinner["count"]) == ("dinner", 1)
    assert days[1]["meals"][0]["count"] == 0


def test_expired_and_cancelled_bookings_do_not_count(
    admin_client, db, make_participant, make_booking, clock
):
    eater(
        db,
        make_participant,
        make_booking,
        "ada@example.com",
        "Ada",
        [(13, "lunch")],
        status=STATUS_EXPIRED,
        hold_expires_at=clock() - timedelta(hours=1),
    )
    eater(
        db,
        make_participant,
        make_booking,
        "bob@example.com",
        "Bob",
        [(13, "lunch")],
        status=STATUS_CANCEL_REQUESTED,
    )
    days = admin_client.get("/api/admin/views/meals").json()["days"]
    assert days[0]["meals"][0]["count"] == 0


def test_csv_has_a_row_per_person_with_diet_and_allergies(
    admin_client, db, make_participant, make_booking
):
    eater(
        db,
        make_participant,
        make_booking,
        "ada@example.com",
        "Ada",
        [(13, "dinner"), (13, "lunch")],
        "vegetarian",
        "Glutine",
    )
    response = admin_client.get("/api/admin/views/meals?format=csv")
    assert response.headers["content-disposition"] == 'attachment; filename="pasti-2026-07-01.csv"'
    header, *rows = parse(response)
    assert header == [
        "Giorno",
        "Pasto",
        "Nome",
        "Cognome",
        "Email",
        "Regime",
        "Allergie e intolleranze",
        "Prezzo",
        "Incasso",
        "Tipo di incasso",
        "Dovuto",
        "Istruzioni di pagamento",
        "Tipo",
    ]
    assert rows == [
        [
            "13/07/2026",
            "Pranzo",
            "Ada",
            "Lovelace",
            "ada@example.com",
            "Vegetariano",
            "Glutine",
            "8,00",
            "Organizzatori",
            "Incasso dell’organizzazione",
            "8,00",
            "",
            "Iscritto",
        ],
        [
            "13/07/2026",
            "Cena",
            "Ada",
            "Lovelace",
            "ada@example.com",
            "Vegetariano",
            "Glutine",
            "12,00",
            "Organizzatori",
            "Incasso dell’organizzazione",
            "12,00",
            "",
            "Iscritto",
        ],
    ]


def test_participants_cannot_see_the_meals_view(client, outbox, make_participant, edition):
    make_participant("ada@example.com")
    login(client, outbox)
    assert client.get("/api/admin/views/meals").status_code == 403


def test_week_counts_lunches_and_dinners(admin_client, db, make_participant, make_booking):
    eater(
        db,
        make_participant,
        make_booking,
        "ada@example.com",
        "Ada",
        [(13, "lunch"), (13, "dinner")],
    )
    eater(db, make_participant, make_booking, "bob@example.com", "Bob", [(13, "lunch")])
    week = admin_client.get("/api/admin/views/week").json()
    monday, tuesday = week["days"][0], week["days"][1]
    assert (monday["lunches"], monday["dinners"]) == (2, 1)
    assert (tuesday["lunches"], tuesday["dinners"]) == (0, 0)
    assert (week["total_lunches"], week["total_dinners"]) == (2, 1)
    header, *rows = parse(admin_client.get("/api/admin/views/week?format=csv"))
    first = dict(zip(header, rows[0], strict=True))
    assert (first["Pranzi"], first["Cene"]) == ("2", "1")
    total = dict(zip(header, rows[-1], strict=True))
    assert (total["Pranzi"], total["Cene"]) == ("2", "1")
