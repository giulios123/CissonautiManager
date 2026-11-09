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
