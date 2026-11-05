import csv
import io
from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    STATUS_REFUNDED,
    Slot,
)
from tests.test_auth import login


def slot(db, day, period="morning"):
    return db.scalar(select(Slot).where(Slot.date == date(2026, 7, day), Slot.period == period))


def parse(response):
    return list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))


@pytest.fixture
def camp(db, edition, make_participant, make_booking, admin_client, clock):
    """Monday 13 July: a mix of bookings, some of which must not count as present."""

    def person(email, first, last):
        return make_participant(email, first_name=first, last_name=last)

    def book(who, slots, **kw):
        return make_booking(
            who, [slot(db, 13, p) if isinstance(p, str) else p for p in slots], **kw
        )

    ada = book(person("ada@example.com", "Ada", "Lovelace"), ["morning", "afternoon"])
    bob = book(person("bob@example.com", "Bob", "Builder"), ["evening"], status=STATUS_CONFIRMED)
    eve = book(person("eve@example.com", "Eve", "Adams"), ["morning"], status=STATUS_CONFIRMED)
    cara = book(person("cara@example.com", "Cara", "Expired"), ["morning"], status=STATUS_EXPIRED)
    dan = book(
        person("dan@example.com", "Dan", "Cancelled"), ["morning"], status=STATUS_CANCEL_REQUESTED
    )
    fay = book(person("fay@example.com", "Fay", "Refunded"), ["morning"], status=STATUS_REFUNDED)
    late = book(
        person("late@example.com", "Lia", "Late"),
        ["morning"],
        status=STATUS_PENDING,
        hold_expires_at=clock() - timedelta(minutes=1),
    )
    return dict(ada=ada, bob=bob, eve=eve, cara=cara, dan=dan, fay=fay, late=late)


def day_slots(response, day="2026-07-13"):
    days = {d["date"]: d for d in response.json()["days"]}
    return {s["period"]: s for s in days[day]["slots"]}


class TestSlotsView:
    def test_lists_every_day_and_slot_of_the_edition_even_when_empty(self, admin_client, edition):
        days = admin_client.get("/api/admin/views/slots").json()["days"]
        assert [d["date"] for d in days] == [f"2026-07-{n}" for n in range(13, 18)]
        assert all(
            [s["period"] for s in d["slots"]] == ["morning", "afternoon", "evening"] for d in days
        )
        assert all(s["present"] == 0 for d in days for s in d["slots"])

    def test_counts_capacity_and_free_seats(self, admin_client, camp):
        slots = day_slots(admin_client.get("/api/admin/views/slots"))
        assert (
            slots["morning"]["capacity"],
            slots["morning"]["present"],
            slots["morning"]["free"],
        ) == (25, 2, 23)
        assert (slots["afternoon"]["present"], slots["afternoon"]["free"]) == (1, 24)

    def test_names_are_listed_by_surname(self, admin_client, camp):
        morning = day_slots(admin_client.get("/api/admin/views/slots"))["morning"]
        assert [p["last_name"] for p in morning["people"]] == ["Adams", "Lovelace"]
        assert morning["people"][0]["email"] == "eve@example.com"

    def test_expired_cancelled_refunded_and_overdue_holds_are_not_present(self, admin_client, camp):
        morning = day_slots(admin_client.get("/api/admin/views/slots"))["morning"]
        names = {p["last_name"] for p in morning["people"]}
        assert names.isdisjoint({"Expired", "Cancelled", "Refunded", "Late"})

    def test_the_evening_includes_whoever_booked_the_whole_day_marked_as_derived(
        self, admin_client, camp
    ):
        evening = day_slots(admin_client.get("/api/admin/views/slots"))["evening"]
        by_name = {p["last_name"]: p for p in evening["people"]}
        assert set(by_name) == {"Builder", "Lovelace"}
        assert by_name["Lovelace"]["derived"] is True
        assert by_name["Builder"]["derived"] is False
        assert evening["present"] == 2

    def test_the_evening_has_no_limit(self, admin_client, camp):
        evening = day_slots(admin_client.get("/api/admin/views/slots"))["evening"]
        assert evening["capacity"] is None and evening["free"] is None

    def test_one_daytime_slot_does_not_imply_the_evening(self, admin_client, camp):
        evening = day_slots(admin_client.get("/api/admin/views/slots"))["evening"]
        assert "Adams" not in {p["last_name"] for p in evening["people"]}

    def test_other_days_are_untouched(self, admin_client, camp):
        assert (
            day_slots(admin_client.get("/api/admin/views/slots"), "2026-07-14")["morning"][
                "present"
            ]
            == 0
        )

    def test_csv_has_one_row_per_slot_and_person(self, admin_client, camp):
        response = admin_client.get("/api/admin/views/slots?format=csv")
        assert (
            response.headers["content-disposition"]
            == 'attachment; filename="giorni-slot-2026-07-01.csv"'
        )
        header, *rows = parse(response)
        assert header == [
            "Giorno",
            "Slot",
            "Orario",
            "Nome",
            "Cognome",
            "Email",
            "Stato",
            "Sera derivata",
        ]
        assert len(rows) == 2 + 1 + 2  # morning, afternoon, evening
        ada_evening = next(r for r in rows if r[3] == "Ada" and r[1] == "Sera")
        assert ada_evening[0] == "13/07/2026"
        assert ada_evening[2] == "19:00-00:00"
        assert ada_evening[6] == "In attesa di pagamento"
        assert ada_evening[7] == "sì"
        bob = next(r for r in rows if r[3] == "Bob")
        assert (bob[6], bob[7]) == ("Confermata", "no")

    def test_admins_only(self, client, outbox, make_participant, edition):
        assert client.get("/api/admin/views/slots").status_code == 401
        make_participant("ada@example.com")
        login(client, outbox)
        assert client.get("/api/admin/views/slots").status_code == 403
        assert client.get("/api/admin/views/slots?format=csv").status_code == 403

    def test_without_an_edition_it_is_empty(self, admin_client):
        assert admin_client.get("/api/admin/views/slots").json() == {"days": []}


class TestWeekView:
    def test_counts_per_period_with_the_derived_evening_and_distinct_people(
        self, admin_client, camp
    ):
        days = {d["date"]: d for d in admin_client.get("/api/admin/views/week").json()["days"]}
        monday = days["2026-07-13"]
        assert (monday["morning"], monday["afternoon"], monday["evening"]) == (2, 1, 2)
        assert monday["evening_derived"] == 1
        assert monday["people"] == 3  # Ada, Bob and Eve; the others do not count

    def test_every_day_of_the_edition_is_listed_with_zeros_when_empty(self, admin_client, camp):
        days = admin_client.get("/api/admin/views/week").json()["days"]
        assert [d["date"] for d in days] == [f"2026-07-{n}" for n in range(13, 18)]
        assert days[1] == {
            "date": "2026-07-14",
            "morning": 0,
            "afternoon": 0,
            "evening": 0,
            "evening_derived": 0,
            "people": 0,
        }

    def test_total_counts_each_person_once_across_days(self, admin_client, db, camp):
        camp["ada"].slots.append(slot(db, 14))
        db.commit()
        data = admin_client.get("/api/admin/views/week").json()
        assert data["total_people"] == 3
        assert {d["date"]: d["people"] for d in data["days"]}["2026-07-14"] == 1

    def test_csv_has_a_row_per_day_and_a_total(self, admin_client, camp):
        response = admin_client.get("/api/admin/views/week?format=csv")
        disposition = response.headers["content-disposition"]
        assert disposition == 'attachment; filename="settimana-2026-07-01.csv"'
        header, *rows = parse(response)
        assert header == [
            "Giorno",
            "Mattina",
            "Pomeriggio",
            "Sera",
            "di cui sera derivata",
            "Persone",
        ]
        assert rows[0] == ["13/07/2026", "2", "1", "2", "1", "3"]
        assert len(rows) == 5 + 1
        assert rows[-1][0] == "Totale persone diverse" and rows[-1][-1] == "3"

    def test_admins_only(self, client, outbox, make_participant, edition):
        assert client.get("/api/admin/views/week").status_code == 401
        make_participant("ada@example.com")
        login(client, outbox)
        assert client.get("/api/admin/views/week").status_code == 403

    def test_without_an_edition_it_is_empty(self, admin_client):
        assert admin_client.get("/api/admin/views/week").json() == {"days": [], "total_people": 0}


class TestPaymentsReview:
    @pytest.fixture
    def cases(self, db, edition, make_participant, make_booking, admin_client, clock):
        from tests.test_change_slots import pay

        def case(last, status=STATUS_PENDING, due=1100, paid=0, **kw):
            who = make_participant(f"{last.lower()}@example.com", first_name="Test", last_name=last)
            booking = make_booking(who, [slot(db, 13)], status=status, amount_due_cents=due, **kw)
            if paid:
                pay(db, booking, paid)
            return booking

        return dict(
            expired=case("Expired", STATUS_EXPIRED, paid=500),
            balance=case("Balance", STATUS_CONFIRMED, due=1200, paid=1100),
            credit=case("Credit", STATUS_CONFIRMED, due=1100, paid=1200),
            refund=case("Refund", STATUS_CANCEL_REQUESTED, paid=1100),
            close=case("Close", STATUS_CANCEL_REQUESTED),
            partial=case("Partial", paid=400),
            overdue=case("Overdue", paid=300, hold_expires_at=clock() - timedelta(minutes=1)),
            # nothing to look at below
            waiting=case("Waiting"),
            settled=case("Settled", STATUS_CONFIRMED, paid=1100),
            refunded=case("Refunded", STATUS_REFUNDED, paid=1100),
            lapsed=case("Lapsed", STATUS_EXPIRED),
        )

    def reasons(self, client):
        return {
            r["last_name"]: r["reason"]
            for r in client.get("/api/admin/views/payments-review").json()
        }

    def test_lists_each_kind_of_case_with_its_reason(self, admin_client, cases):
        assert self.reasons(admin_client) == {
            "Expired": "scaduta_con_pagamenti",
            "Overdue": "scaduta_con_pagamenti",
            "Balance": "saldo_positivo",
            "Credit": "credito",
            "Refund": "disdetta_da_rimborsare",
            "Close": "disdetta_da_chiudere",
            "Partial": "pagamento_parziale",
        }

    def test_amounts_balance_and_label(self, admin_client, cases):
        rows = {
            r["last_name"]: r for r in admin_client.get("/api/admin/views/payments-review").json()
        }
        balance, credit = rows["Balance"], rows["Credit"]
        assert (balance["amount_due_cents"], balance["paid_cents"], balance["balance_cents"]) == (
            1200,
            1100,
            100,
        )
        assert credit["balance_cents"] == -100
        assert balance["reason_label"] == "Confermata con una differenza da versare"
        assert rows["Overdue"]["status"] == STATUS_EXPIRED
        assert rows["Balance"]["booking_id"] == cases["balance"].id

    def test_cases_come_in_a_stable_order_by_kind_then_surname(self, admin_client, cases):
        order = [
            r["last_name"] for r in admin_client.get("/api/admin/views/payments-review").json()
        ]
        assert order == ["Expired", "Overdue", "Balance", "Credit", "Refund", "Close", "Partial"]

    def test_a_case_leaves_the_view_once_it_is_solved(self, admin_client, cases):
        response = admin_client.post(
            f"/api/admin/registrations/{cases['balance'].id}/payments",
            json={"amount_cents": 100, "channel": "iban"},
        )
        assert response.status_code == 201
        assert "Balance" not in self.reasons(admin_client)

    def test_voided_payments_do_not_count(self, admin_client, db, cases):
        for payment in cases["partial"].payments:
            payment.voided_at = payment.created_at
            payment.voided_by_id = payment.recorded_by_id
        db.commit()
        assert "Partial" not in self.reasons(admin_client)

    def test_csv(self, admin_client, cases):
        response = admin_client.get("/api/admin/views/payments-review?format=csv")
        disposition = response.headers["content-disposition"]
        assert disposition == 'attachment; filename="pagamenti-da-verificare-2026-07-01.csv"'
        header, *rows = parse(response)
        assert header[-1] == "Motivo"
        assert len(rows) == 7
        credit = next(r for r in rows if r[1] == "Credit")
        values = dict(zip(header, credit, strict=True))
        assert (values["Dovuto"], values["Versato"], values["Saldo"]) == ("11,00", "12,00", "-1,00")
        assert values["Motivo"] == "Confermata con un credito (ha versato in più)"

    def test_admins_only(self, client, outbox, make_participant, edition):
        assert client.get("/api/admin/views/payments-review").status_code == 401
        make_participant("ada@example.com")
        login(client, outbox)
        assert client.get("/api/admin/views/payments-review").status_code == 403

    def test_without_an_edition_it_is_empty(self, admin_client):
        assert admin_client.get("/api/admin/views/payments-review").json() == []
