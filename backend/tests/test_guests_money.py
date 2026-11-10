import csv
import io
from uuid import uuid4

from sqlalchemy import func, select

from app.models import AuditLog, Booking, ExternalGuest, ExternalMovement, MealSetting, Payment
from tests.helpers import d
from tests.test_activities_me import activity
from tests.test_auth import login

URL = "/api/admin/guests"


def parse(response):
    assert response.status_code == 200, response.text
    return list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))


def make_guest(client, first="Anna", last="Rossi", meals=(), activity_ids=(), **extra):
    guest_id = client.post(URL, json={"first_name": first, "last_name": last, **extra}).json()["id"]
    client.put(
        f"{URL}/{guest_id}/meals",
        json={"meals": [{"date": f"2026-07-{day}", "kind": kind} for day, kind in meals]},
    )
    if activity_ids:
        client.put(f"{URL}/{guest_id}/activities", json={"activity_ids": list(activity_ids)})
    return guest_id


def move(client, guest_id, amount, kind="payment", channel="revolut", **extra):
    return client.post(
        f"{URL}/{guest_id}/movements",
        json={"kind": kind, "amount_cents": amount, "channel": channel, **extra},
    )


def detail(client, guest_id):
    return client.get(f"{URL}/{guest_id}").json()


class TestDue:
    def test_due_is_the_sum_of_what_the_organisation_collects(self, admin_client, db, edition):
        hike = activity(db, edition, "Escursione", 13, "morning", price=1500)
        free = activity(db, edition, "Quiz", 13, "evening")
        guest_id = make_guest(
            admin_client, meals=[("13", "lunch"), ("13", "dinner")], activity_ids=[hike.id, free.id]
        )
        body = detail(admin_client, guest_id)
        # lunch 8 + dinner 12 + hike 15; no fee, no meal covered by it.
        assert body["due_cents"] == 800 + 1200 + 1500
        assert body["balance_cents"] == body["due_cents"]
        assert [i["collectable_cents"] for i in body["items"]] == [800, 1200, 1500, 0]

    def test_a_provider_item_is_shown_but_adds_nothing(self, admin_client, db, edition):
        db.add(
            MealSetting(
                edition_id=edition.id,
                date=d(13),
                kind="lunch",
                payment_mode="provider",
                price_cents=900,
                payment_instructions="Paga al ristorante",
            )
        )
        db.commit()
        guest_id = make_guest(admin_client, meals=[("13", "lunch"), ("13", "dinner")])
        body = detail(admin_client, guest_id)
        assert body["due_cents"] == 1200
        lunch = body["items"][0]
        assert (lunch["price_cents"], lunch["collectable_cents"]) == (900, 0)

    def test_a_non_paying_guest_owes_nothing(self, admin_client, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")], payer="non_paying")
        assert detail(admin_client, guest_id)["due_cents"] == 0

    def test_the_due_follows_a_price_change_without_touching_the_movements(
        self, admin_client, db, edition
    ):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        move(admin_client, guest_id, 300)
        edition.lunch_price_cents = 1000
        db.commit()
        body = detail(admin_client, guest_id)
        assert (body["due_cents"], body["paid_cents"], body["balance_cents"]) == (1000, 300, 700)


class TestPayments:
    def test_a_payment_updates_the_balance_and_touches_no_booking(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking = make_booking(make_participant("ada@example.com"), [], amount_due_cents=1100)
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        response = move(admin_client, guest_id, 600, note="contanti", paid_on="2026-07-13")
        assert response.status_code == 201
        body = response.json()
        assert (body["paid_cents"], body["balance_cents"]) == (600, 200)
        assert body["movements"][0]["note"] == "contanti"
        assert db.scalar(select(func.count()).select_from(Payment)) == 0
        assert db.get(Booking, booking.id).amount_due_cents == 1100
        log = db.scalar(select(AuditLog).where(AuditLog.action == "guest_payment"))
        assert "Anna Rossi" in log.detail

    def test_the_date_defaults_to_today_in_rome(self, admin_client, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        body = move(admin_client, guest_id, 100).json()
        assert body["movements"][0]["paid_on"] == "2026-07-01"

    def test_paying_more_than_due_is_a_credit_not_a_refund(self, admin_client, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        body = move(admin_client, guest_id, 1000).json()
        assert body["balance_cents"] == -200
        assert body["movements"][0]["kind"] == "payment"

    def test_the_same_request_is_recorded_once(self, admin_client, db, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        key = str(uuid4())
        first = move(admin_client, guest_id, 500, request_key=key)
        second = move(admin_client, guest_id, 500, request_key=key)
        assert first.status_code == second.status_code == 201
        assert db.scalar(select(func.count()).select_from(ExternalMovement)) == 1
        assert second.json()["paid_cents"] == 500

    def test_the_same_key_with_other_data_is_a_conflict(self, admin_client, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        key = str(uuid4())
        move(admin_client, guest_id, 500, request_key=key)
        other = move(admin_client, guest_id, 600, request_key=key)
        assert other.status_code == 409
        assert other.json()["detail"]["code"] == "payment_request_conflict"

    def test_a_bad_channel_or_amount_is_refused(self, admin_client, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        assert move(admin_client, guest_id, 100, channel="cash").status_code == 422
        assert move(admin_client, guest_id, 0).status_code == 422
        assert move(admin_client, guest_id, -5).status_code == 422

    def test_unknown_guest_is_not_found(self, admin_client, edition):
        assert move(admin_client, 999, 100).status_code == 404


class TestRefunds:
    def test_a_refund_up_to_the_credit_is_accepted(self, admin_client, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        move(admin_client, guest_id, 1000)  # credit of 200
        response = move(admin_client, guest_id, 200, kind="refund")
        assert response.status_code == 201
        body = response.json()
        assert (body["paid_cents"], body["refunded_cents"], body["balance_cents"]) == (
            1000,
            200,
            0,
        )

    def test_a_refund_beyond_the_credit_is_refused(self, admin_client, db, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        move(admin_client, guest_id, 1000)
        refused = move(admin_client, guest_id, 201, kind="refund")
        assert refused.status_code == 422
        assert "credito" in refused.json()["detail"]
        assert db.scalar(select(func.count()).select_from(ExternalMovement)) == 1

    def test_a_refund_with_no_credit_is_refused(self, admin_client, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        move(admin_client, guest_id, 800)
        assert move(admin_client, guest_id, 1, kind="refund").status_code == 422

    def test_switching_to_non_paying_turns_the_payment_into_a_credit(self, admin_client, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        move(admin_client, guest_id, 800)
        admin_client.patch(
            f"{URL}/{guest_id}",
            json={"first_name": "Anna", "last_name": "Rossi", "payer": "non_paying"},
        )
        body = detail(admin_client, guest_id)
        assert (body["due_cents"], body["balance_cents"]) == (0, -800)
        assert move(admin_client, guest_id, 800, kind="refund").status_code == 201


class TestVoid:
    def test_a_voided_payment_stays_on_record_and_stops_counting(self, admin_client, db, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        movement_id = move(admin_client, guest_id, 800).json()["movements"][0]["id"]
        response = admin_client.post(
            f"{URL}/movements/{movement_id}/void", json={"reason": "Errore di battitura"}
        )
        assert response.status_code == 200
        body = response.json()
        assert (body["paid_cents"], body["balance_cents"]) == (0, 800)
        assert body["movements"][0]["voided_at"] is not None
        assert body["movements"][0]["void_reason"] == "Errore di battitura"
        assert db.scalar(select(func.count()).select_from(ExternalMovement)) == 1
        log = db.scalar(select(AuditLog).where(AuditLog.action == "guest_movement_voided"))
        assert "Errore di battitura" in log.detail

    def test_a_reason_is_required(self, admin_client, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        movement_id = move(admin_client, guest_id, 800).json()["movements"][0]["id"]
        assert admin_client.post(f"{URL}/movements/{movement_id}/void", json={}).status_code == 422
        blank = admin_client.post(f"{URL}/movements/{movement_id}/void", json={"reason": " "})
        assert blank.status_code == 422

    def test_voiding_twice_is_a_conflict(self, admin_client, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        movement_id = move(admin_client, guest_id, 800).json()["movements"][0]["id"]
        url = f"{URL}/movements/{movement_id}/void"
        assert admin_client.post(url, json={"reason": "x"}).status_code == 200
        assert admin_client.post(url, json={"reason": "x"}).status_code == 409

    def test_a_payment_cannot_be_voided_while_a_refund_relies_on_it(self, admin_client, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        pay = move(admin_client, guest_id, 1000).json()["movements"][0]["id"]
        refund = move(admin_client, guest_id, 200, kind="refund").json()["movements"][1]["id"]
        blocked = admin_client.post(f"{URL}/movements/{pay}/void", json={"reason": "x"})
        assert blocked.status_code == 409
        assert "restituzione" in blocked.json()["detail"]
        voided_refund = admin_client.post(f"{URL}/movements/{refund}/void", json={"reason": "x"})
        assert voided_refund.status_code == 200
        voided_pay = admin_client.post(f"{URL}/movements/{pay}/void", json={"reason": "x"})
        assert voided_pay.status_code == 200

    def test_unknown_movement_is_not_found(self, admin_client, edition):
        response = admin_client.post(f"{URL}/movements/999/void", json={"reason": "x"})
        assert response.status_code == 404


class TestDelete:
    def test_a_guest_with_movements_is_not_deleted_even_if_voided(self, admin_client, db, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        movement_id = move(admin_client, guest_id, 800).json()["movements"][0]["id"]
        admin_client.post(f"{URL}/movements/{movement_id}/void", json={"reason": "x"})
        refused = admin_client.delete(f"{URL}/{guest_id}")
        assert refused.status_code == 409
        assert db.get(ExternalGuest, guest_id) is not None
        # The meals can still be taken away.
        cleared = admin_client.put(f"{URL}/{guest_id}/meals", json={"meals": []})
        assert cleared.status_code == 200

    def test_a_guest_without_movements_is_deleted(self, admin_client, edition):
        guest_id = make_guest(admin_client)
        assert admin_client.delete(f"{URL}/{guest_id}").status_code == 204


class TestToCollect:
    def test_only_paying_guests_with_a_balance_are_listed(self, admin_client, db, edition):
        owes = make_guest(admin_client, "Anna", "Rossi", [("13", "lunch")])
        paid = make_guest(admin_client, "Luca", "Bianchi", [("13", "lunch")])
        move(admin_client, paid, 800)
        make_guest(admin_client, "Gino", "Verdi", [("13", "lunch")], payer="non_paying")
        make_guest(admin_client, "Pia", "Neri")  # nothing selected, owes nothing
        rows = admin_client.get(f"{URL}/to-collect").json()
        assert [(r["guest_id"], r["balance_cents"]) for r in rows] == [(owes, 800)]
        assert rows[0]["items"][0]["collectable_cents"] == 800

    def test_a_partial_payment_keeps_the_guest_in_the_list_with_the_rest(
        self, admin_client, edition
    ):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        move(admin_client, guest_id, 300)
        row = admin_client.get(f"{URL}/to-collect").json()[0]
        assert (row["due_cents"], row["paid_cents"], row["balance_cents"]) == (800, 300, 500)

    def test_search_by_name(self, admin_client, edition):
        make_guest(admin_client, "Anna", "Rossi", [("13", "lunch")])
        make_guest(admin_client, "Luca", "Bianchi", [("13", "lunch")])
        rows = admin_client.get(f"{URL}/to-collect", params={"q": "bian"}).json()
        assert [r["last_name"] for r in rows] == ["Bianchi"]

    def test_provider_only_items_do_not_make_a_guest_owe(self, admin_client, db, edition):
        db.add(
            MealSetting(
                edition_id=edition.id,
                date=d(13),
                kind="lunch",
                payment_mode="provider",
                price_cents=900,
                payment_instructions="Paga al ristorante",
            )
        )
        db.commit()
        make_guest(admin_client, meals=[("13", "lunch")])
        assert admin_client.get(f"{URL}/to-collect").json() == []

    def test_the_booking_to_collect_view_is_unchanged(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        make_booking(make_participant("ada@example.com"), [], amount_due_cents=1100)
        before = admin_client.get("/api/admin/views/to-collect").json()
        make_guest(admin_client, meals=[("13", "lunch")])
        assert admin_client.get("/api/admin/views/to-collect").json() == before


class TestAccess:
    def test_only_admins(self, admin_client, client, outbox, make_participant, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        movement_id = move(admin_client, guest_id, 100).json()["movements"][0]["id"]
        make_participant("ada@example.com")
        login(client, outbox)
        for response in (
            move(client, guest_id, 100),
            client.post(f"{URL}/movements/{movement_id}/void", json={"reason": "x"}),
            client.get(f"{URL}/to-collect"),
            client.get(f"{URL}/movements"),
            client.get(f"{URL}/movements?format=csv"),
        ):
            assert response.status_code == 403

    def test_a_participant_never_sees_guest_money(
        self, admin_client, client, outbox, make_participant, make_booking, edition
    ):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        move(admin_client, guest_id, 800)
        ada = make_participant("ada@example.com")
        make_booking(ada, [])
        login(client, outbox)
        assert "Anna" not in client.get("/api/me").text


class TestMovementsCsv:
    def test_one_row_per_movement_with_voided_ones_marked(self, admin_client, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        pay = move(admin_client, guest_id, 1000, note="contanti").json()["movements"][0]["id"]
        move(admin_client, guest_id, 200, kind="refund")
        wrong = move(admin_client, guest_id, 50, channel="paypal").json()["movements"][2]["id"]
        admin_client.post(f"{URL}/movements/{wrong}/void", json={"reason": "Doppione"})
        header, *rows = parse(admin_client.get(f"{URL}/movements?format=csv"))
        assert header[:5] == ["Data", "Cognome", "Nome", "Tipo di movimento", "Importo"]
        assert [(r[3], r[4], r[6]) for r in rows] == [
            ("Pagamento", "10,00", "Valido"),
            ("Restituzione", "2,00", "Valido"),
            ("Pagamento", "0,50", "Annullato"),
        ]
        assert rows[2][7] == "Doppione"
        assert pay

    def test_the_file_follows_the_language(self, admin_client, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        move(admin_client, guest_id, 100)
        response = admin_client.get(f"{URL}/movements?format=csv&lang=en")
        header, *rows = parse(response)
        assert header[3] == "Type of movement"
        assert rows[0][3] == "Payment"
        assert "guest-movements" in response.headers["content-disposition"]


def report(client):
    return client.get("/api/admin/views/report").json()["revenue"]


class TestReport:
    def test_six_euro_from_a_guest_raise_the_event_total_and_nothing_else(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        from tests.test_report import pay

        booking = make_booking(make_participant("ada@example.com"), [], amount_due_cents=1100)
        pay(db, booking, 1100)
        before = report(admin_client)
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        move(admin_client, guest_id, 600)
        after = report(admin_client)
        for key in ("due_cents", "paid_cents", "net_cents", "to_collect_cents", "credits_cents"):
            assert after[key] == before[key], key
        assert after["external_due_cents"] == 800
        assert after["external_paid_cents"] == 600
        assert after["external_to_collect_cents"] == 200
        assert after["event_net_cents"] == before["net_cents"] + 600
        # The payments of the bookings are the same rows as before.
        assert db.scalar(select(func.count()).select_from(Payment)) == 1

    def test_a_voided_movement_leaves_the_report(self, admin_client, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        movement_id = move(admin_client, guest_id, 600).json()["movements"][0]["id"]
        admin_client.post(f"{URL}/movements/{movement_id}/void", json={"reason": "x"})
        revenue = report(admin_client)
        assert (revenue["external_paid_cents"], revenue["event_net_cents"]) == (0, 0)

    def test_provider_costs_are_in_neither_total(self, admin_client, db, edition):
        db.add(
            MealSetting(
                edition_id=edition.id,
                date=d(13),
                kind="lunch",
                payment_mode="provider",
                price_cents=900,
                payment_instructions="Paga al ristorante",
            )
        )
        db.commit()
        make_guest(admin_client, meals=[("13", "lunch")])
        revenue = report(admin_client)
        assert (revenue["external_due_cents"], revenue["due_cents"]) == (0, 0)

    def test_a_refund_lowers_the_event_total(self, admin_client, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")], payer="non_paying")
        move(admin_client, guest_id, 800)
        move(admin_client, guest_id, 300, kind="refund")
        revenue = report(admin_client)
        assert revenue["external_refunded_cents"] == 300
        assert revenue["event_net_cents"] == 500
        assert revenue["external_credit_cents"] == 500

    def test_the_csv_has_the_guest_section_and_the_event_total(self, admin_client, edition):
        guest_id = make_guest(admin_client, meals=[("13", "lunch")])
        move(admin_client, guest_id, 600)
        rows = parse(admin_client.get("/api/admin/views/report?format=csv"))[1:]
        by_label = {r[1]: r for r in rows}
        assert by_label["Versato dagli esterni"][4] == "6,00"
        assert by_label["Ancora da incassare dagli esterni"][4] == "2,00"
        total = by_label["Incassato dall'evento (quote più esterni)"]
        assert (total[0], total[4]) == ("Totale evento", "6,00")
        english = parse(admin_client.get("/api/admin/views/report?format=csv&lang=en"))[1:]
        assert any(r[0] == "Event total" and r[4] == "6,00" for r in english)
