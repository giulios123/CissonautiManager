import csv
import io
from datetime import date

import pytest
from sqlalchemy import func, select

from app.models import (
    CATEGORY_INTERNAL_NON_PAYING,
    ROLE_ADMIN,
    AuditLog,
    Benefit,
    BenefitDelivery,
    Edition,
    Participant,
    Payment,
    Slot,
)
from tests.helpers import d
from tests.test_auth import login

URL = "/api/admin/deliveries"


def slot(db, day=13, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


def parse(response):
    return list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))


@pytest.fixture
def bottle(db, edition):
    benefit = Benefit(edition_id=edition.id, name_it="Borraccia", name_en="Bottle")
    db.add(benefit)
    db.commit()
    return benefit


@pytest.fixture
def people(db, edition, admin_client, make_participant, make_booking):
    """A paid the base fee, B paid nothing, C is a speaker."""
    boss = db.scalar(select(Participant).where(Participant.role == ROLE_ADMIN))
    made = {}
    for key, last in (("a", "Alfa"), ("b", "Bravo"), ("c", "Charlie")):
        person = make_participant(f"{key}@example.com", first_name=key.upper(), last_name=last)
        made[key] = (person, make_booking(person, [slot(db)]))
    db.add(
        Payment(
            booking_id=made["a"][1].id,
            amount_cents=edition.base_fee_cents,
            channel="iban",
            paid_on=date(2026, 7, 2),
            recorded_by_id=boss.id,
        )
    )
    made["c"][1].category = CATEGORY_INTERNAL_NON_PAYING
    db.commit()
    return made


def deliver(client, people, bottle, who="a", **extra):
    return client.post(
        URL, json={"participant_id": people[who][0].id, "benefit_id": bottle.id, **extra}
    )


def test_the_catalogue_has_counters_and_names_in_the_language(admin_client, bottle, people):
    items = admin_client.get(f"{URL}/benefits").json()
    assert items == [
        {"id": bottle.id, "name": "Borraccia", "retired": False, "delivered": 0, "entitled": 2}
    ]
    english = admin_client.get(f"{URL}/benefits", headers={"Accept-Language": "en"}).json()
    assert english[0]["name"] == "Bottle"
    deliver(admin_client, people, bottle)
    assert admin_client.get(f"{URL}/benefits").json()[0]["delivered"] == 1


def test_an_edition_without_a_catalogue_has_nothing_to_deliver(admin_client, edition, people):
    assert admin_client.get(f"{URL}/benefits").json() == []


def test_the_list_has_only_names_category_and_state(admin_client, bottle, people):
    rows = admin_client.get(f"{URL}?benefit_id={bottle.id}").json()
    assert [r["last_name"] for r in rows] == ["Alfa", "Charlie"]
    assert {r["state"] for r in rows} == {"to_deliver"}
    allowed = {
        "participant_id",
        "first_name",
        "last_name",
        "booking_id",
        "category",
        "entitled",
        "state",
        "delivery",
        "annulled",
    }
    assert all(set(r) == allowed for r in rows)
    text = str(rows)
    assert "@example.com" not in text and "phone" not in text and "allerg" not in text


def test_search_and_state_filters(admin_client, bottle, people):
    deliver(admin_client, people, bottle)
    by_name = admin_client.get(f"{URL}?benefit_id={bottle.id}&q=charl").json()
    assert [r["last_name"] for r in by_name] == ["Charlie"]
    delivered = admin_client.get(f"{URL}?benefit_id={bottle.id}&state=delivered").json()
    assert [r["last_name"] for r in delivered] == ["Alfa"]
    pending = admin_client.get(f"{URL}?benefit_id={bottle.id}&state=pending").json()
    assert [r["last_name"] for r in pending] == ["Charlie"]


def test_an_unknown_benefit_is_404(admin_client, edition, people):
    assert admin_client.get(f"{URL}?benefit_id=999").status_code == 404
    assert admin_client.post(URL, json={"participant_id": 1, "benefit_id": 999}).status_code == 404


def test_deliver_is_201_then_200_for_the_same_person(admin_client, bottle, people, db):
    first = deliver(admin_client, people, bottle, request_key="key-0000-0001")
    again = deliver(admin_client, people, bottle, request_key="key-0000-0001")
    other_key = deliver(admin_client, people, bottle, request_key="key-0000-0002")
    assert (first.status_code, again.status_code, other_key.status_code) == (201, 200, 200)
    assert first.json()["id"] == again.json()["id"] == other_key.json()["id"]
    assert db.scalar(select(func.count()).select_from(BenefitDelivery)) == 1
    row = admin_client.get(f"{URL}?benefit_id={bottle.id}").json()[0]
    assert row["state"] == "delivered"
    assert row["delivery"]["delivered_by"] == "Ada Lovelace"


def test_who_is_not_entitled_gets_422(admin_client, bottle, people, db):
    response = deliver(admin_client, people, bottle, who="b")
    assert response.status_code == 422
    assert response.json()["detail"] == "Questa persona non ha diritto ai benefit."
    english = admin_client.post(
        URL,
        json={"participant_id": people["b"][0].id, "benefit_id": bottle.id},
        headers={"Accept-Language": "en"},
    )
    assert english.json()["detail"] == "This person is not entitled to the benefits."
    assert db.scalar(select(func.count()).select_from(BenefitDelivery)) == 0


def test_a_retired_benefit_takes_no_delivery(admin_client, bottle, people, db):
    bottle.retired = True
    db.commit()
    assert deliver(admin_client, people, bottle).status_code == 422


def test_annul_needs_a_reason_and_is_idempotent(admin_client, bottle, people, db):
    delivery_id = deliver(admin_client, people, bottle).json()["id"]
    assert admin_client.post(f"{URL}/{delivery_id}/annul", json={"reason": " "}).status_code == 422
    assert admin_client.post(f"{URL}/{delivery_id}/annul", json={}).status_code == 422
    first = admin_client.post(f"{URL}/{delivery_id}/annul", json={"reason": "Persona sbagliata"})
    again = admin_client.post(f"{URL}/{delivery_id}/annul", json={"reason": "Altro"})
    assert (first.json()["changed"], again.json()["changed"]) == (True, False)
    row = admin_client.get(f"{URL}?benefit_id={bottle.id}").json()[0]
    assert row["state"] == "to_deliver"
    assert [a["reason"] for a in row["annulled"]] == ["Persona sbagliata"]
    assert (
        db.scalar(
            select(func.count()).select_from(AuditLog).where(AuditLog.action == "benefit_annulled")
        )
        == 1
    )
    assert deliver(admin_client, people, bottle).status_code == 201


def test_an_unknown_delivery_is_404(admin_client, edition):
    assert admin_client.post(f"{URL}/999/annul", json={"reason": "x"}).status_code == 404


def test_a_delivery_of_another_edition_is_404(admin_client, bottle, people, db, edition):
    delivery_id = deliver(admin_client, people, bottle).json()["id"]
    delivery = db.get(BenefitDelivery, delivery_id)
    other = Edition(
        name="Old", start_date=edition.start_date, end_date=edition.end_date, is_active=False
    )
    db.add(other)
    db.commit()
    delivery.edition_id = other.id
    db.commit()
    assert admin_client.post(f"{URL}/{delivery_id}/annul", json={"reason": "x"}).status_code == 404


def test_the_csv_has_the_same_rows_and_headers_in_the_language(admin_client, bottle, people):
    deliver(admin_client, people, bottle)
    rows = parse(admin_client.get(f"{URL}?benefit_id={bottle.id}&format=csv"))
    assert rows[0] == [
        "Nome",
        "Cognome",
        "Categoria",
        "Stato",
        "Consegnato il",
        "Consegnato da",
        "Consegne annullate",
    ]
    assert [(r[1], r[3]) for r in rows[1:]] == [
        ("Alfa", "Consegnato"),
        ("Charlie", "Da consegnare"),
    ]
    listed = admin_client.get(f"{URL}?benefit_id={bottle.id}").json()
    assert [r[1] for r in rows[1:]] == [r["last_name"] for r in listed]
    english = parse(
        admin_client.get(
            f"{URL}?benefit_id={bottle.id}&format=csv", headers={"Accept-Language": "en"}
        )
    )
    assert english[0][0:2] == ["First name", "Last name"]
    assert english[1][3] == "Delivered"
    assert "@example.com" not in "".join(map("".join, english))


def test_delivering_leaves_a_history_entry_on_the_booking(admin_client, bottle, people, db):
    deliver(admin_client, people, bottle)
    log = db.scalar(select(AuditLog).where(AuditLog.action == "benefit_delivered"))
    assert log.booking_id == people["a"][1].id
    assert log.edition_id == bottle.edition_id


def test_only_admins_can_use_it(client, outbox, bottle, people, make_participant):
    assert client.get(f"{URL}/benefits").status_code == 401
    assert client.get(f"{URL}?benefit_id={bottle.id}").status_code == 401
    assert client.post(URL, json={"participant_id": 1, "benefit_id": bottle.id}).status_code == 401
    login(client, outbox, "a@example.com")
    assert client.get(f"{URL}/benefits").status_code == 403
    assert client.get(f"{URL}?benefit_id={bottle.id}").status_code == 403
    assert client.get(f"{URL}?benefit_id={bottle.id}&format=csv").status_code == 403
    response = client.post(URL, json={"participant_id": people["a"][0].id, "benefit_id": bottle.id})
    assert response.status_code == 403
    assert client.post(f"{URL}/1/annul", json={"reason": "x"}).status_code == 403


def test_participants_never_see_benefits_or_deliveries(
    admin_client, client, outbox, bottle, people
):
    deliver(admin_client, people, bottle)
    login(client, outbox, "a@example.com")
    for path in ("/api/me", "/api/me/proposals"):
        text = client.get(path).text
        assert "Borraccia" not in text and "benefit_delivery" not in text, path


def test_the_csv_filename_does_not_depend_on_the_benefit_name(admin_client, edition, people, db):
    odd = Benefit(edition_id=edition.id, name_it='Borraccia "🍹" è', name_en="Bottle")
    db.add(odd)
    db.commit()
    response = admin_client.get(f"{URL}?benefit_id={odd.id}&format=csv")
    assert response.status_code == 200
    header = response.headers["content-disposition"]
    assert header.isascii()
    assert f"-{odd.id}-" in header
