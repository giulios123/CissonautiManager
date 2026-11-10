from sqlalchemy import func, select

from app.models import (
    STATUS_CONFIRMED,
    STATUS_PENDING,
    AuditLog,
    BookingMeal,
    Payment,
    Slot,
)
from app.services.amounts import recompute_amount
from tests.helpers import d
from tests.test_activities_me import activity
from tests.test_auth import login
from tests.test_change_slots import pay

REG = "/api/admin/registrations"


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


def make(db, edition, make_participant, make_booking, email="ada@example.com", **kw):
    """Monday morning (fee 11 €), lunch (8 €) and dinner (12 €) on Monday, a 15 € hike."""
    policy = kw.pop("policy", "registration_fee")
    edition.confirmation_policy = policy
    db.commit()
    hike = activity(db, edition, "Escursione", 13, "morning", price=1500)
    booking = make_booking(
        make_participant(email),
        [slot(db, 13), slot(db, 13, "afternoon")],
        **kw,
    )
    booking.meals = [BookingMeal(date=d(13), kind="lunch"), BookingMeal(date=d(13), kind="dinner")]
    booking.activities = [hike]
    db.commit()
    recompute_amount(edition, booking)
    db.commit()
    return booking, hike


def body(**over):
    return {"category": "ordinary", "fee_exempt": False, "meals": [], "activity_ids": [], **over}


def preview(client, booking, **over):
    response = client.post(f"{REG}/{booking.id}/exemptions/preview", json=body(**over))
    assert response.status_code == 200, response.text
    return response.json()


def apply(client, booking, token, **over):
    return client.post(
        f"{REG}/{booking.id}/exemptions/apply", json={**body(**over), "preview_token": token}
    )


class TestAmounts:
    def test_no_exemption_means_the_usual_amounts(
        self, db, edition, make_participant, make_booking
    ):
        booking, _ = make(db, edition, make_participant, make_booking)
        # fee 11 + lunch 8 + dinner 12 + hike 15
        assert (booking.registration_fee_cents, booking.amount_due_cents) == (1100, 4600)
        assert booking.category == "ordinary" and not booking.fee_exempt

    def test_an_exempt_fee_makes_the_fee_zero_and_leaves_the_rest(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, _ = make(db, edition, make_participant, make_booking)
        result = preview(admin_client, booking, fee_exempt=True)
        assert result["registration_fee_after_cents"] == 0
        assert result["amount_due_after_cents"] == 4600 - 1100

    def test_exempt_meals_and_activities_are_worth_zero_and_the_others_stay_due(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, hike = make(db, edition, make_participant, make_booking)
        result = preview(
            admin_client,
            booking,
            meals=[{"date": "2026-07-13", "kind": "dinner"}],
            activity_ids=[hike.id],
        )
        assert result["registration_fee_after_cents"] == 1100
        assert result["amount_due_after_cents"] == 1100 + 800  # fee and lunch remain

    def test_the_included_meal_skips_an_exempt_one(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        edition.included_meal_policy = "first_organizer_meal"
        booking, _ = make(db, edition, make_participant, make_booking)
        # The lunch is covered by the fee: total = 11 + 12 + 15.
        assert booking.amount_due_cents == 1100 + 1200 + 1500
        result = preview(admin_client, booking, meals=[{"date": "2026-07-13", "kind": "lunch"}])
        # The exempt lunch is not wasted as the covered meal: the dinner is covered instead.
        assert result["included_meal"] == ["2026-07-13", "dinner"]
        assert result["amount_due_after_cents"] == 1100 + 1500

    def test_everything_exempt_leaves_a_zero_total(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, hike = make(db, edition, make_participant, make_booking)
        result = preview(
            admin_client,
            booking,
            fee_exempt=True,
            meals=[
                {"date": "2026-07-13", "kind": "lunch"},
                {"date": "2026-07-13", "kind": "dinner"},
            ],
            activity_ids=[hike.id],
        )
        assert result["amount_due_after_cents"] == 0


class TestPreview:
    def test_a_preview_writes_nothing(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, _ = make(db, edition, make_participant, make_booking)
        preview(admin_client, booking, fee_exempt=True)
        db.refresh(booking)
        assert (booking.fee_exempt, booking.amount_due_cents) == (False, 4600)
        assert (
            db.scalar(
                select(func.count())
                .select_from(AuditLog)
                .where(AuditLog.action == "exemptions_applied")
            )
            == 0
        )

    def test_it_shows_before_after_balance_and_status(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, _ = make(db, edition, make_participant, make_booking)
        pay(db, booking, 1100)  # covers the fee
        result = preview(admin_client, booking, fee_exempt=True)
        assert (
            result["status_before"] == STATUS_CONFIRMED or result["status_before"] == STATUS_PENDING
        )
        assert result["paid_cents"] == 1100
        assert result["balance_before_cents"] == 4600 - 1100
        assert result["balance_after_cents"] == 3500 - 1100

    def test_an_item_that_is_not_on_the_booking_is_refused(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, _ = make(db, edition, make_participant, make_booking)
        response = admin_client.post(
            f"{REG}/{booking.id}/exemptions/preview",
            json=body(meals=[{"date": "2026-07-14", "kind": "lunch"}]),
        )
        assert response.status_code == 422
        other = admin_client.post(
            f"{REG}/{booking.id}/exemptions/preview", json=body(activity_ids=[999])
        )
        assert other.status_code == 422

    def test_expired_or_closed_bookings_are_refused(
        self, admin_client, db, edition, make_participant, make_booking, clock
    ):
        booking, _ = make(db, edition, make_participant, make_booking)
        booking.status = "disdetta_richiesta"
        db.commit()
        response = admin_client.post(f"{REG}/{booking.id}/exemptions/preview", json=body())
        assert response.status_code == 409


class TestApply:
    def test_applying_a_preview_changes_only_the_chosen_items_and_no_payment(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, hike = make(db, edition, make_participant, make_booking)
        pay(db, booking, 500)
        token = preview(admin_client, booking, fee_exempt=True, activity_ids=[hike.id])[
            "preview_token"
        ]
        response = apply(admin_client, booking, token, fee_exempt=True, activity_ids=[hike.id])
        assert response.status_code == 200, response.text
        db.refresh(booking)
        assert booking.fee_exempt is True
        assert (booking.registration_fee_cents, booking.amount_due_cents) == (0, 2000)
        # The meals are still due.
        assert all(not m.exempt for m in booking.meals)
        assert [(p.amount_cents, p.voided_at) for p in booking.payments] == [(500, None)]
        log = db.scalar(select(AuditLog).where(AuditLog.action == "exemptions_applied"))
        assert "Quota esente: sì" in log.detail

    def test_a_pending_booking_that_becomes_covered_is_confirmed_once_with_one_email(
        self, admin_client, db, edition, make_participant, make_booking, outbox
    ):
        booking, _ = make(db, edition, make_participant, make_booking)
        assert booking.status == STATUS_PENDING
        outbox.sent.clear()
        token = preview(admin_client, booking, fee_exempt=True)["preview_token"]
        assert preview(admin_client, booking, fee_exempt=True)["status_after"] == STATUS_CONFIRMED
        assert apply(admin_client, booking, token, fee_exempt=True).status_code == 200
        db.refresh(booking)
        assert booking.status == STATUS_CONFIRMED
        # No payment was invented to confirm it.
        assert db.scalar(select(func.count()).select_from(Payment)) == 0
        assert len([m for m in outbox.sent if "ada@example.com" in str(m.to)]) == 1
        # Applying the same preview again does nothing and sends nothing more.
        before = len(outbox.sent)
        again = apply(admin_client, booking, token, fee_exempt=True)
        assert again.status_code == 200
        assert len(outbox.sent) == before

    def test_a_confirmed_booking_stays_confirmed_when_an_exemption_is_removed(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, _ = make(db, edition, make_participant, make_booking)
        booking.fee_exempt = True
        booking.status = STATUS_CONFIRMED
        db.commit()
        recompute_amount(edition, booking)
        db.commit()
        assert booking.registration_fee_cents == 0
        token = preview(admin_client, booking)["preview_token"]
        assert apply(admin_client, booking, token).status_code == 200
        db.refresh(booking)
        assert booking.status == STATUS_CONFIRMED
        assert booking.amount_due_cents == 4600  # a balance, not a lost place

    def test_a_stale_preview_is_refused_and_writes_nothing(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, _ = make(db, edition, make_participant, make_booking)
        token = preview(admin_client, booking, fee_exempt=True)["preview_token"]
        pay(db, booking, 100)  # something changed after the preview
        response = apply(admin_client, booking, token, fee_exempt=True)
        assert response.status_code == 409
        db.refresh(booking)
        assert booking.fee_exempt is False

    def test_a_token_for_a_different_change_is_refused(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, _ = make(db, edition, make_participant, make_booking)
        token = preview(admin_client, booking, fee_exempt=True)["preview_token"]
        response = apply(admin_client, booking, token, fee_exempt=False)
        assert response.status_code == 409

    def test_the_exemption_is_lost_if_the_item_is_removed_and_chosen_again(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, _ = make(db, edition, make_participant, make_booking)
        meal = {"date": "2026-07-13", "kind": "lunch"}
        token = preview(admin_client, booking, meals=[meal])["preview_token"]
        apply(admin_client, booking, token, meals=[meal])
        assert (
            admin_client.put(
                f"{REG}/{booking.id}/meals",
                json={"meals": [{"date": "2026-07-13", "kind": "dinner"}]},
            ).status_code
            == 200
        )
        assert (
            admin_client.put(
                f"{REG}/{booking.id}/meals",
                json={
                    "meals": [
                        {"date": "2026-07-13", "kind": "lunch"},
                        {"date": "2026-07-13", "kind": "dinner"},
                    ]
                },
            ).status_code
            == 200
        )
        db.refresh(booking)
        assert all(not m.exempt for m in booking.meals)

    def test_a_kept_exempt_item_stays_exempt_when_others_change(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, hike = make(db, edition, make_participant, make_booking)
        meal = {"date": "2026-07-13", "kind": "lunch"}
        token = preview(admin_client, booking, meals=[meal], activity_ids=[hike.id])[
            "preview_token"
        ]
        apply(admin_client, booking, token, meals=[meal], activity_ids=[hike.id])
        # Drop the dinner: the exempt lunch and hike stay exempt and the total follows.
        assert (
            admin_client.put(f"{REG}/{booking.id}/meals", json={"meals": [meal]}).status_code == 200
        )
        db.refresh(booking)
        assert booking.amount_due_cents == 1100  # fee only
        assert [m.exempt for m in booking.meals] == [True]

    def test_non_admins_cannot_touch_exemptions_or_category(
        self, db, edition, make_participant, make_booking, client, outbox
    ):
        booking, _ = make(db, edition, make_participant, make_booking)
        login(client, outbox)
        for call in (
            client.post(f"{REG}/{booking.id}/exemptions/preview", json=body()),
            client.post(
                f"{REG}/{booking.id}/exemptions/apply", json={**body(), "preview_token": "0" * 64}
            ),
            client.put(f"{REG}/{booking.id}/category", json={"category": "internal_non_paying"}),
            client.post(
                f"{REG}/{booking.id}/refunds", json={"amount_cents": 100, "channel": "revolut"}
            ),
        ):
            assert call.status_code == 403

    def test_legacy_total_policy_also_honours_exemptions(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, hike = make(db, edition, make_participant, make_booking, policy="legacy_total")
        token = preview(admin_client, booking, activity_ids=[hike.id])["preview_token"]
        apply(admin_client, booking, token, activity_ids=[hike.id])
        db.refresh(booking)
        assert booking.amount_due_cents == 4600 - 1500


class TestCategory:
    def test_the_category_alone_changes_no_amount_and_is_recorded(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, _ = make(db, edition, make_participant, make_booking)
        response = admin_client.put(
            f"{REG}/{booking.id}/category", json={"category": "internal_non_paying"}
        )
        assert response.status_code == 200
        assert response.json()["category"] == "internal_non_paying"
        db.refresh(booking)
        assert booking.amount_due_cents == 4600 and not booking.fee_exempt
        log = db.scalar(select(AuditLog).where(AuditLog.action == "category_changed"))
        assert "interno non pagante" in log.detail

    def test_an_unknown_category_is_refused(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, _ = make(db, edition, make_participant, make_booking)
        response = admin_client.put(f"{REG}/{booking.id}/category", json={"category": "vip"})
        assert response.status_code == 422

    def test_the_participant_never_sees_the_category(
        self, admin_client, db, edition, make_participant, make_booking, client, outbox
    ):
        booking, _ = make(db, edition, make_participant, make_booking)
        admin_client.put(f"{REG}/{booking.id}/category", json={"category": "internal_non_paying"})
        login(client, outbox)
        assert "internal_non_paying" not in client.get("/api/me").text


class TestParticipantView:
    def test_exempt_items_are_marked_and_worth_zero_on_the_personal_page(
        self, admin_client, db, edition, make_participant, make_booking, client, outbox
    ):
        booking, hike = make(db, edition, make_participant, make_booking)
        meal = {"date": "2026-07-13", "kind": "lunch"}
        token = preview(
            admin_client, booking, fee_exempt=True, meals=[meal], activity_ids=[hike.id]
        )["preview_token"]
        apply(admin_client, booking, token, fee_exempt=True, meals=[meal], activity_ids=[hike.id])
        login(client, outbox)
        mine = client.get("/api/me").json()["bookings"][0]
        assert mine["fee_exempt"] is True
        lunch = next(m for m in mine["meals"] if m["kind"] == "lunch")
        dinner = next(m for m in mine["meals"] if m["kind"] == "dinner")
        assert (lunch["exempt"], lunch["collectable_cents"]) == (True, 0)
        assert (dinner["exempt"], dinner["collectable_cents"]) == (False, 1200)
        assert (mine["activities"][0]["exempt"], mine["activities"][0]["collectable_cents"]) == (
            True,
            0,
        )
        assert mine["amount_due_cents"] == 1200


class TestPeopleList:
    def test_the_list_shows_category_and_exempt_fee_and_filters_by_category(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        first, _ = make(db, edition, make_participant, make_booking)
        second, _ = make(db, edition, make_participant, make_booking, email="bob@example.com")
        admin_client.put(f"{REG}/{second.id}/category", json={"category": "internal_non_paying"})
        rows = {r["id"]: r for r in admin_client.get(REG).json()}
        assert (rows[first.id]["category"], rows[second.id]["category"]) == (
            "ordinary",
            "internal_non_paying",
        )
        only = admin_client.get(REG, params={"category": "internal_non_paying"}).json()
        assert [r["id"] for r in only] == [second.id]

    def test_the_csv_has_the_category_and_the_exempt_fee_in_both_languages(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        import csv
        import io

        booking, _ = make(db, edition, make_participant, make_booking)
        token = preview(admin_client, booking, category="internal_non_paying", fee_exempt=True)[
            "preview_token"
        ]
        apply(admin_client, booking, token, category="internal_non_paying", fee_exempt=True)

        def rows(url):
            text = admin_client.get(url).content.decode("utf-8-sig")
            return list(csv.reader(io.StringIO(text), delimiter=";"))

        italian = rows(f"{REG}?format=csv")
        assert italian[0][-2:] == ["Categoria", "Quota esente"]
        assert italian[1][-2:] == ["Interno non pagante", "sì"]
        english = rows(f"{REG}?format=csv&lang=en")
        assert english[0][-2:] == ["Category", "Fee exempt"]
        assert english[1][-2:] == ["Internal, not paying", "yes"]


class TestReport:
    def revenue(self, client):
        return client.get("/api/admin/views/report").json()["revenue"]

    def test_exempt_value_internal_count_and_refunds_are_reported_apart(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        booking, hike = make(db, edition, make_participant, make_booking, status=STATUS_CONFIRMED)
        pay(db, booking, 4600)
        before = self.revenue(admin_client)
        assert (before["exempt_value_cents"], before["internal_non_paying"]) == (0, 0)
        meal = {"date": "2026-07-13", "kind": "lunch"}
        token = preview(
            admin_client,
            booking,
            category="internal_non_paying",
            fee_exempt=True,
            meals=[meal],
            activity_ids=[hike.id],
        )["preview_token"]
        apply(
            admin_client,
            booking,
            token,
            category="internal_non_paying",
            fee_exempt=True,
            meals=[meal],
            activity_ids=[hike.id],
        )
        after = self.revenue(admin_client)
        assert after["exempt_value_cents"] == 1100 + 800 + 1500
        assert after["internal_non_paying"] == 1
        # Dovuto: only the dinner is left; the payments are what they were.
        assert (after["due_cents"], after["paid_cents"]) == (1200, 4600)
        assert after["credits_cents"] == 4600 - 1200
        refund_response = admin_client.post(
            f"{REG}/{booking.id}/refunds", json={"amount_cents": 3000, "channel": "revolut"}
        )
        assert refund_response.status_code == 201
        refunded = self.revenue(admin_client)
        assert refunded["credit_refunded_cents"] == 3000
        assert refunded["refunded_cents"] == 3000
        assert (refunded["paid_cents"], refunded["net_cents"]) == (4600, 1600)
        assert refunded["credits_cents"] == 400
        assert refunded["to_collect_cents"] == 0

    def test_the_csv_has_the_new_rows(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        make(db, edition, make_participant, make_booking)
        text = admin_client.get("/api/admin/views/report?format=csv&lang=en").text
        for label in (
            "Value exempted",
            "Internal, not paying bookings",
            "Refunds on active bookings (included in Refunded)",
        ):
            assert label in text


class TestReviewFindings:
    """Exemptions must show up the same way in every view and export."""

    def exempt_lunch_and_hike(
        self, admin_client, db, edition, make_participant, make_booking, **kw
    ):
        booking, hike = make(db, edition, make_participant, make_booking, **kw)
        meal = {"date": "2026-07-13", "kind": "lunch"}
        token = preview(admin_client, booking, meals=[meal], activity_ids=[hike.id])[
            "preview_token"
        ]
        apply(admin_client, booking, token, meals=[meal], activity_ids=[hike.id])
        return booking, hike

    def test_the_meals_view_and_csv_count_an_exempt_meal_as_zero_and_say_so(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        import csv
        import io

        self.exempt_lunch_and_hike(admin_client, db, edition, make_participant, make_booking)
        view = admin_client.get("/api/admin/views/meals").json()
        lunch = next(m for m in view["days"][0]["meals"] if m["kind"] == "lunch")
        person = lunch["people"][0]
        assert (person["exempt"], person["collectable_cents"]) == (True, 0)
        dinner = next(m for m in view["days"][0]["meals"] if m["kind"] == "dinner")
        assert (dinner["people"][0]["exempt"], dinner["people"][0]["collectable_cents"]) == (
            False,
            1200,
        )
        text = admin_client.get("/api/admin/views/meals?format=csv").content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text), delimiter=";"))
        header, lunch_row = rows[0], next(r for r in rows[1:] if r[1] == "Pranzo")
        assert lunch_row[header.index("Dovuto")] == "0,00"
        assert lunch_row[header.index("Tipo di incasso")] == "Esente"
        dinner_row = next(r for r in rows[1:] if r[1] == "Cena")
        assert dinner_row[header.index("Dovuto")] == "12,00"

    def test_the_report_money_leaves_out_exempt_meals_and_activities(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        self.exempt_lunch_and_hike(admin_client, db, edition, make_participant, make_booking)
        report = admin_client.get("/api/admin/views/report").json()
        revenue = report["revenue"]
        # fee 11 + dinner 12 remain; the lunch and the hike are worth zero.
        assert revenue["due_cents"] == 2300
        assert revenue["due_meals_cents"] == 1200
        assert revenue["due_activities_cents"] == 0
        assert revenue["due_difference_cents"] == 0
        # People are still counted: attendance is not money.
        assert report["meals"]["lunches"]["total"] == 1
        assert report["activities"][0]["joined"]["total"] == 1
        assert report["activities"][0]["expected_cents"] == 0

    def test_the_expected_income_of_an_activity_counts_only_the_non_exempt(
        self, admin_client, db, edition, make_participant, make_booking
    ):
        _, hike = self.exempt_lunch_and_hike(
            admin_client, db, edition, make_participant, make_booking
        )
        other = make_booking(
            make_participant("bob@example.com"), [slot(db, 13)], status=STATUS_CONFIRMED
        )
        other.activities = [hike]
        db.commit()
        row = admin_client.get("/api/admin/views/report").json()["activities"][0]
        assert row["joined"]["total"] == 2
        assert row["expected_cents"] == 1500  # only Bob's seat is collected

    def test_the_category_filter_leaves_out_people_only_on_a_waitlist(
        self, admin_client, db, edition, make_participant, make_booking, add_entry, clock
    ):
        booking, _ = make(db, edition, make_participant, make_booking)
        admin_client.put(f"{REG}/{booking.id}/category", json={"category": "internal_non_paying"})
        waiting = make_participant("wait@example.com", first_name="Wanda")
        add_entry(slot(db, 13, "evening"), waiting, clock())
        everyone = {r["email"] for r in admin_client.get(REG).json()}
        assert "wait@example.com" in everyone
        internal = admin_client.get(REG, params={"category": "internal_non_paying"}).json()
        assert [r["email"] for r in internal] == ["ada@example.com"]
        ordinary_csv = admin_client.get(f"{REG}?format=csv&category=ordinary").content.decode(
            "utf-8-sig"
        )
        assert "wait@example.com" not in ordinary_csv

    def test_the_activity_offers_charge_nothing_for_an_exempt_activity(
        self, admin_client, db, edition, make_participant, make_booking, client, outbox
    ):
        booking, _ = self.exempt_lunch_and_hike(
            admin_client, db, edition, make_participant, make_booking
        )
        login(client, outbox)
        offer = client.get("/api/me").json()["activities"][0]
        assert (offer["joined"], offer["exempt"], offer["collectable_cents"]) == (True, True, 0)
        detail = admin_client.get(f"{REG}/{booking.id}").json()
        assert detail["activity_offers"][0]["collectable_cents"] == 0
