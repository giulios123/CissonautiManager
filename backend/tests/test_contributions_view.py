import csv
import io
from datetime import timedelta

from sqlalchemy import select

from app.models import STATUS_EXPIRED, Activity, Contribution, Slot
from tests.helpers import d
from tests.test_auth import login


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


def parse(response):
    return list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))


def offer(db, booking, kind, title, at):
    db.add(
        Contribution(booking_id=booking.id, kind=kind, title=title, created_at=at, updated_at=at)
    )
    db.commit()


def test_lists_and_filters_contributions(admin_client, db, make_participant, make_booking, clock):
    ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    bob = make_booking(
        make_participant("bob@example.com", first_name="Bob"),
        [slot(db, 13)],
        status=STATUS_EXPIRED,
        hold_expires_at=clock() - timedelta(hours=1),
    )
    offer(db, bob, "talk", "Vecchio talk", clock() - timedelta(days=1))
    offer(db, ada, "talk", "Macchine", clock())
    offer(db, ada, "skill", "Saldatura", clock())
    rows = admin_client.get("/api/admin/views/contributions").json()
    assert [(r["title"], r["active"]) for r in rows] == [
        ("Macchine", True),
        ("Saldatura", True),
        ("Vecchio talk", False),
    ]
    talks = admin_client.get("/api/admin/views/contributions?kind=talk").json()
    assert [r["title"] for r in talks] == ["Macchine", "Vecchio talk"]
    header, *csv_rows = parse(
        admin_client.get("/api/admin/views/contributions?kind=talk&format=csv")
    )
    assert header == [
        "Tipo",
        "Titolo",
        "Descrizione",
        "Nome",
        "Cognome",
        "Email",
        "Stato",
        "Proposto il",
    ]
    assert [r[1] for r in csv_rows] == ["Macchine", "Vecchio talk"]
    assert csv_rows[1][6] == "Scaduta"


def test_participants_cannot_see_it(client, outbox, make_participant, edition):
    make_participant("ada@example.com")
    login(client, outbox)
    assert client.get("/api/admin/views/contributions").status_code == 403


def test_week_counts_activity_signups(
    admin_client, db, edition, make_participant, make_booking, clock
):
    hike = Activity(
        edition_id=edition.id, title="Escursione", date=d(14), period="morning", price_cents=0
    )
    db.add(hike)
    db.commit()
    for email in ("ada@example.com", "bob@example.com"):
        booking = make_booking(make_participant(email), [slot(db, 14)])
        booking.activities = [hike]
    gone = make_booking(
        make_participant("cid@example.com"),
        [slot(db, 14)],
        status=STATUS_EXPIRED,
        hold_expires_at=clock() - timedelta(hours=1),
    )
    gone.activities = [hike]
    db.commit()
    week = admin_client.get("/api/admin/views/week").json()
    assert [day["activities"] for day in week["days"]] == [0, 2, 0, 0, 0]
    assert week["total_activities"] == 2
    header, *rows = parse(admin_client.get("/api/admin/views/week?format=csv"))
    assert dict(zip(header, rows[-1], strict=True))["Adesioni alle attività"] == "2"


def test_the_wanted_skill_is_listed_filtered_exported_and_reported(
    admin_client, db, make_participant, make_booking, clock
):
    ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    offer(db, ada, "skill", "Saldatura", clock())
    offer(db, ada, "wanted_skill", "Montaggio video", clock())
    rows = admin_client.get("/api/admin/views/contributions?kind=wanted_skill").json()
    assert [r["title"] for r in rows] == ["Montaggio video"]
    _, *csv_rows = parse(admin_client.get("/api/admin/views/contributions?format=csv"))
    assert sorted(r[0] for r in csv_rows) == ["Competenza", "Competenza cercata"]
    report = admin_client.get("/api/admin/views/report").json()
    assert report["contributions"]["wanted_skill"] == 1
