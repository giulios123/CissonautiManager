import csv
import io
from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.models import STATUS_CONFIRMED, STATUS_EXPIRED, Payment, Slot
from tests.test_auth import login


def slot(db, day, period="morning"):
    return db.scalar(select(Slot).where(Slot.date == date(2026, 7, day), Slot.period == period))


def parse(response):
    return list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))


@pytest.fixture
def people(db, edition, make_participant, make_booking, admin_client):
    ada = make_participant(
        "ada@example.com", first_name="Ada", last_name="Lovelace", phone="+39 333 1234567"
    )
    bob = make_participant("bob@example.com", first_name="Bob", last_name="Builder")
    # Ada: Monday whole day (derived evening), Tuesday evening only, Wednesday morning only
    ada_booking = make_booking(
        ada,
        [slot(db, 13), slot(db, 13, "afternoon"), slot(db, 14, "evening"), slot(db, 15)],
        amount_due_cents=1300,
    )
    bob_booking = make_booking(bob, [slot(db, 13)], amount_due_cents=1100)
    return ada_booking, bob_booking


def test_row_shows_phone_and_the_evenings_including_the_derived_one(admin_client, people):
    rows = {r["first_name"]: r for r in admin_client.get("/api/admin/registrations").json()}
    assert rows["Ada"]["phone"] == "+39 333 1234567"
    assert rows["Ada"]["evenings"] == 2  # Monday derived, Tuesday booked; Wednesday morning only
    assert rows["Ada"]["days"] == 3
    assert rows["Bob"]["phone"] is None
    assert rows["Bob"]["evenings"] == 0


def test_a_booking_that_does_not_occupy_seats_has_no_evenings(admin_client, db, people, clock):
    people[0].status = STATUS_EXPIRED
    db.commit()
    rows = {r["first_name"]: r for r in admin_client.get("/api/admin/registrations").json()}
    assert rows["Ada"]["evenings"] == 0


def test_csv_is_a_download_with_bom_and_one_row_per_person(admin_client, people):
    response = admin_client.get("/api/admin/registrations?format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert (
        response.headers["content-disposition"] == 'attachment; filename="persone-2026-07-01.csv"'
    )
    assert response.content.startswith(b"\xef\xbb\xbf")
    rows = parse(response)
    assert rows[0][:8] == [
        "Nome",
        "Cognome",
        "Email",
        "Telefono",
        "Codice",
        "Giorni",
        "Sere",
        "Stato",
    ]
    assert {r[0] for r in rows[1:]} == {"Ada", "Bob"}


def test_csv_writes_amounts_with_a_comma_and_the_phone_as_typed(
    admin_client, db, people, make_participant
):
    admin = make_participant("treasurer@example.com")
    db.add(
        Payment(
            booking_id=people[0].id, amount_cents=1500, channel="iban",
            paid_on=date(2026, 7, 2), recorded_by_id=admin.id,
        )
    )  # fmt: skip
    db.commit()
    ada = next(
        r for r in parse(admin_client.get("/api/admin/registrations?format=csv")) if r[0] == "Ada"
    )
    assert ada[3] == "+39 333 1234567"
    header = parse(admin_client.get("/api/admin/registrations?format=csv"))[0]
    values = dict(zip(header, ada, strict=True))
    assert (values["Dovuto"], values["Versato"], values["Saldo"]) == ("13,00", "15,00", "-2,00")
    assert values["Giorni"] == "3" and values["Sere"] == "2"


def test_csv_respects_the_same_filters_as_the_list(admin_client, people):
    rows = parse(admin_client.get("/api/admin/registrations?format=csv&q=bob"))
    assert [r[0] for r in rows[1:]] == ["Bob"]
    rows = parse(admin_client.get("/api/admin/registrations?format=csv&status=confermata"))
    assert rows[1:] == []


def test_csv_times_are_in_rome_and_the_hold_only_for_pending_bookings(
    admin_client, db, people, clock
):
    people[1].status = STATUS_CONFIRMED
    people[0].hold_expires_at = clock() + timedelta(days=3, hours=-1)  # 09:00 UTC = 11:00 Rome
    db.commit()
    header, *rows = parse(admin_client.get("/api/admin/registrations?format=csv"))
    by_name = {r[0]: dict(zip(header, r, strict=True)) for r in rows}
    assert by_name["Ada"]["Scadenza blocco"] == "04/07/2026 11:00"
    assert by_name["Bob"]["Scadenza blocco"] == ""
    assert by_name["Ada"]["Iscritto il"] == "01/07/2026 12:00"


def test_names_that_look_like_formulas_are_neutralised_in_the_csv(admin_client, db, people):
    people[1].participant.first_name = "=HYPERLINK(1)"
    db.commit()
    header, *rows = parse(admin_client.get("/api/admin/registrations?format=csv"))
    assert "'=HYPERLINK(1)" in [r[0] for r in rows]


def test_csv_is_for_admins_only(client, outbox, make_participant, edition):
    assert client.get("/api/admin/registrations?format=csv").status_code == 401
    make_participant("ada@example.com")
    login(client, outbox)
    assert client.get("/api/admin/registrations?format=csv").status_code == 403


def test_csv_without_an_edition_is_just_the_header(admin_client):
    rows = parse(admin_client.get("/api/admin/registrations?format=csv"))
    assert len(rows) == 1 and rows[0][0] == "Nome"
