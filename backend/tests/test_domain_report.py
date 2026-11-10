from datetime import date

import pytest

from app.domain.report import (
    ActivityFacts,
    BookingFacts,
    EditionFacts,
    GuestFacts,
    PaymentFacts,
    Split,
    WaitlistFacts,
    edition_report,
)
from app.models import (
    CLOSE_BOOKED,
    CLOSE_CANCELLED,
    CLOSE_LEFT,
    CLOSE_PROMOTED,
    CLOSE_REMOVED,
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    STATUS_REFUNDED,
)

MON, TUE = date(2026, 7, 13), date(2026, 7, 14)
SLOTS = tuple((day, period) for day in (MON, TUE) for period in ("morning", "afternoon", "evening"))


def edition(**over) -> EditionFacts:
    values = dict(
        slots=SLOTS,
        base_fee_cents=1000,
        per_day_fee_cents=100,
        lunch_price_cents=800,
        dinner_price_cents=1200,
    )
    return EditionFacts(**{**values, **over})


def booking(booking_id, person_id, status, **over) -> BookingFacts:
    values = dict(
        amount_due_cents=1100,
        paid_cents=0,
        refund_cents=0,
        slots=((MON, "morning"),),
        meals=(),
        activity_ids=(),
        diet=None,
        has_allergies=False,
        contributions=(),
    )
    return BookingFacts(booking_id, person_id, status, **{**values, **over})


HIKE = ActivityFacts(1, "Trekking", MON, "morning", 1500, 10)
QUIZ = ActivityFacts(2, "Quiz", TUE, "evening", 0, None)

BOOKINGS = [
    # Ada: confirmed, the whole Monday (so Monday evening too), both meals, the hike.
    booking(
        1,
        1,
        STATUS_CONFIRMED,
        amount_due_cents=4600,
        paid_cents=4600,
        slots=((MON, "morning"), (MON, "afternoon")),
        meals=((MON, "lunch"), (MON, "dinner")),
        activity_ids=(1,),
        diet="vegetarian",
        has_allergies=True,
        contributions=("talk",),
    ),
    # Bob: still to pay, Monday morning and lunch.
    booking(
        2,
        2,
        STATUS_PENDING,
        amount_due_cents=1900,
        paid_cents=500,
        meals=((MON, "lunch"),),
        contributions=("skill",),
    ),
    # Cy: expired with a partial payment; nothing of his counts as presence.
    booking(
        3,
        3,
        STATUS_EXPIRED,
        paid_cents=700,
        meals=((MON, "lunch"),),
        activity_ids=(1,),
        contributions=("topic",),
    ),
    # Di: asked to cancel, has paid and nothing was refunded yet.
    booking(4, 4, STATUS_CANCEL_REQUESTED, paid_cents=1100, slots=((TUE, "morning"),)),
    # Eli: refunded in full.
    booking(5, 5, STATUS_REFUNDED, paid_cents=1100, refund_cents=1100),
    # Flo: confirmed and overpaid by 4 euros, Tuesday afternoon and evening.
    booking(
        6,
        6,
        STATUS_CONFIRMED,
        paid_cents=1500,
        slots=((TUE, "afternoon"), (TUE, "evening")),
    ),
]


@pytest.fixture
def report():
    waitlist = [
        WaitlistFacts(None, False),
        WaitlistFacts(CLOSE_PROMOTED, True),
        WaitlistFacts(CLOSE_PROMOTED, False),
        WaitlistFacts(CLOSE_LEFT, False),
        WaitlistFacts(CLOSE_REMOVED, False),
        WaitlistFacts(CLOSE_CANCELLED, True),
        WaitlistFacts(CLOSE_BOOKED, False),
    ]
    payments = [
        PaymentFacts("iban", 4600),
        PaymentFacts("satispay", 500),
        PaymentFacts("iban", 100),
    ]
    return edition_report(edition(), BOOKINGS, [HIKE, QUIZ], waitlist, payments)


class TestEnrollment:
    def test_bookings_by_effective_status_with_every_status_listed(self, report):
        assert report.enrollment.by_status == {
            STATUS_CONFIRMED: 2,
            STATUS_PENDING: 1,
            STATUS_EXPIRED: 1,
            STATUS_CANCEL_REQUESTED: 1,
            STATUS_REFUNDED: 1,
        }

    def test_people_counted_are_those_with_a_seat(self, report):
        assert report.enrollment.people_with_seat == 3


class TestPresence:
    def slot(self, report, day, period):
        return next(s for s in report.presence.slots if (s.day, s.period) == (day, period))

    def test_confirmed_and_pending_are_kept_apart(self, report):
        assert self.slot(report, MON, "morning").present == Split(confirmed=1, pending=1)

    def test_the_evening_of_a_whole_day_is_derived_and_flagged(self, report):
        evening = self.slot(report, MON, "evening")
        assert evening.present == Split(confirmed=1, pending=0)
        assert evening.derived == 1

    def test_an_evening_booked_on_its_own_is_not_derived(self, report):
        evening = self.slot(report, TUE, "evening")
        assert evening.present.total == 1 and evening.derived == 0

    def test_expired_cancelled_and_refunded_are_not_present(self, report):
        assert self.slot(report, TUE, "morning").present.total == 0

    def test_every_slot_of_the_edition_is_listed_in_order(self, report):
        assert [(s.day, s.period) for s in report.presence.slots] == list(SLOTS)

    def test_peak_average_and_person_days(self, report):
        # Daytime slots: Mon morning 2, Mon afternoon 1, Tue morning 0, Tue afternoon 1.
        assert report.presence.peak == 2
        assert report.presence.average_per_daytime_slot == 1.0
        assert report.presence.person_days == Split(confirmed=2, pending=1)


class TestMeals:
    def test_meals_per_day_and_in_total_with_the_split(self, report):
        monday, tuesday = report.meals.days
        assert (monday.lunches, monday.dinners) == (Split(1, 1), Split(1, 0))
        assert (tuesday.lunches, tuesday.dinners) == (Split(), Split())
        assert (report.meals.lunches, report.meals.dinners) == (Split(1, 1), Split(1, 0))

    def test_diets_per_meal_count_who_did_not_say_as_none(self, report):
        assert report.meals.lunch_diets == {"omnivore": 0, "vegetarian": 1, "vegan": 0, "none": 1}
        assert report.meals.dinner_diets == {"omnivore": 0, "vegetarian": 1, "vegan": 0, "none": 0}

    def test_allergies_are_only_a_number(self, report):
        assert report.meals.people_with_allergies == 1
        assert not hasattr(report.meals, "allergies")

    def test_an_expired_booking_does_not_eat(self, report):
        assert report.meals.lunches.total == 2  # Ada and Bob, not Cy


class TestActivities:
    def test_joined_split_and_expected_income(self, report):
        hike, quiz = report.activities
        assert (hike.title, hike.joined, hike.expected_cents) == ("Trekking", Split(1, 0), 1500)
        assert (quiz.title, quiz.joined, quiz.expected_cents) == ("Quiz", Split(), 0)
        assert (hike.capacity, quiz.capacity) == (10, None)

    def test_an_expired_booking_does_not_take_part(self, report):
        assert report.activities[0].joined.total == 1


def test_contributions_count_only_bookings_with_a_seat(report):
    assert report.contributions == {"talk": 1, "topic": 0, "skill": 1}


def test_waitlist_counts_each_way_out_and_the_plus_ones_among_the_promoted(report):
    wl = report.waitlist
    assert (wl.waiting, wl.promoted, wl.promoted_plus_one) == (1, 2, 1)
    assert (wl.left, wl.removed, wl.cancelled, wl.booked) == (1, 1, 1, 1)


class TestRevenue:
    def test_what_is_owed_only_counts_bookings_with_a_seat_and_is_broken_down(self, report):
        revenue = report.revenue
        assert revenue.due_cents == 4600 + 1900 + 1100
        assert revenue.due_fee_cents == 3 * 1100
        assert revenue.due_meals_cents == (800 + 1200) + 800
        assert revenue.due_activities_cents == 1500
        assert revenue.due_difference_cents == 0

    def test_the_parts_always_add_up_even_when_a_price_changed_after_sign_up(self):
        report = edition_report(edition(lunch_price_cents=900), BOOKINGS, [HIKE, QUIZ], [], [])
        revenue = report.revenue
        parts = (
            revenue.due_fee_cents
            + revenue.due_meals_cents
            + revenue.due_activities_cents
            + revenue.due_difference_cents
        )
        assert parts == revenue.due_cents
        assert revenue.due_difference_cents == -200  # two lunches were booked at 8, now cost 9

    def test_paid_refunded_and_net_count_every_booking(self, report):
        revenue = report.revenue
        assert revenue.paid_cents == 4600 + 500 + 700 + 1100 + 1100 + 1500
        assert revenue.refunded_cents == 1100
        assert revenue.net_cents == revenue.paid_cents - 1100

    def test_paid_by_channel_comes_from_the_payments(self, report):
        assert report.revenue.paid_by_channel == {"iban": 4700, "satispay": 500}

    def test_to_collect_credits_and_to_refund(self, report):
        assert report.revenue.to_collect_cents == 1400  # Bob owes 19 and paid 5
        assert report.revenue.credits_cents == 400  # Flo paid 15 on 11
        assert report.revenue.to_refund_cents == 1100  # Di asked to cancel, nothing refunded


def test_an_empty_edition_is_all_zeros_and_does_not_fail():
    report = edition_report(edition(slots=()), [], [], [], [])
    assert report.presence.slots == [] and report.presence.peak == 0
    assert report.presence.average_per_daytime_slot == 0.0
    assert report.meals.days == [] and report.meals.lunches == Split()
    assert report.activities == [] and report.days == []
    assert report.waitlist.waiting == 0
    assert report.revenue.due_cents == 0 and report.revenue.net_cents == 0
    assert report.contributions == {"talk": 0, "topic": 0, "skill": 0}
    assert report.enrollment.people_with_seat == 0


class TestExternalGuests:
    def facts(self):
        return EditionFacts(
            slots=((MON, "morning"), (MON, "afternoon"), (MON, "evening")),
            base_fee_cents=1000,
            per_day_fee_cents=100,
            lunch_price_cents=800,
            dinner_price_cents=1200,
        )

    def test_guests_are_in_the_meal_totals_and_apart(self):
        guest = GuestFacts(1, ((MON, "lunch"), (MON, "dinner")), (), "vegan", True)
        other = GuestFacts(2, ((MON, "lunch"),), (), None, False)
        report = edition_report(self.facts(), [], [], [], [], [guest, other])
        monday = report.meals.days[0]
        assert monday.lunches == Split(0, 0, 2)
        assert monday.lunches.total == 2
        assert monday.dinners.external == 1
        assert report.meals.lunch_diets["vegan"] == 1
        assert report.meals.people_with_allergies == 1

    def test_a_guest_without_meals_does_not_count_for_allergies(self):
        guest = GuestFacts(1, (), (), None, True)
        report = edition_report(self.facts(), [], [], [], [], [guest])
        assert report.meals.people_with_allergies == 0

    def test_the_same_meal_twice_for_a_guest_counts_once(self):
        guest = GuestFacts(1, ((MON, "lunch"), (MON, "lunch")), (), None, False)
        report = edition_report(self.facts(), [], [], [], [], [guest])
        assert report.meals.lunches.external == 1

    def test_activities_count_guests_but_expect_no_money_from_them(self):
        hike = ActivityFacts(7, "Trekking", MON, "morning", 1500, 10)
        guest = GuestFacts(1, (), (7,), None, False)
        report = edition_report(self.facts(), [], [hike], [], [], [guest])
        row = report.activities[0]
        assert row.joined == Split(0, 0, 1)
        assert row.expected_cents == 0

    def test_guests_change_neither_presence_nor_money(self):
        guest = GuestFacts(1, ((MON, "lunch"),), (), None, False)
        base = edition_report(self.facts(), [], [], [], [], [])
        with_guest = edition_report(self.facts(), [], [], [], [], [guest])
        assert with_guest.presence == base.presence
        assert with_guest.enrollment == base.enrollment
        assert with_guest.revenue == base.revenue


class TestExternalMoney:
    def facts(self):
        return EditionFacts(
            slots=((MON, "morning"),),
            base_fee_cents=1000,
            per_day_fee_cents=100,
            lunch_price_cents=800,
            dinner_price_cents=1200,
        )

    def booking(self, **over):
        defaults = dict(
            booking_id=1,
            person_id=1,
            status=STATUS_CONFIRMED,
            amount_due_cents=1100,
            paid_cents=1100,
            refund_cents=0,
            slots=((MON, "morning"),),
            meals=(),
            activity_ids=(),
            diet=None,
            has_allergies=False,
            contributions=(),
        )
        return BookingFacts(**{**defaults, **over})

    def test_guest_money_is_apart_and_joins_only_in_the_event_total(self):
        base = edition_report(self.facts(), [self.booking()], [], [], [], [])
        guest = GuestFacts(1, (), (), None, False, due_cents=800, paid_cents=600)
        with_guest = edition_report(self.facts(), [self.booking()], [], [], [], [guest])
        before, after = base.revenue, with_guest.revenue
        # The figures of the bookings do not move.
        assert (after.due_cents, after.paid_cents, after.net_cents, after.to_collect_cents) == (
            before.due_cents,
            before.paid_cents,
            before.net_cents,
            before.to_collect_cents,
        )
        assert (after.external_due_cents, after.external_paid_cents) == (800, 600)
        assert after.external_to_collect_cents == 200
        assert after.event_net_cents == before.net_cents + 600

    def test_refunds_and_credits_of_guests(self):
        guests = [
            GuestFacts(1, (), (), None, False, due_cents=0, paid_cents=800, refunded_cents=300),
            GuestFacts(2, (), (), None, False, due_cents=500, paid_cents=500),
        ]
        revenue = edition_report(self.facts(), [], [], [], [], guests).revenue
        assert revenue.external_refunded_cents == 300
        assert revenue.external_net_cents == 500 + 500
        assert revenue.external_credit_cents == 500  # guest 1 holds 800 - 300 against 0 due
        assert revenue.external_to_collect_cents == 0
        assert revenue.event_net_cents == 1000

    def test_no_guests_no_external_money(self):
        revenue = edition_report(self.facts(), [self.booking()], [], [], [], []).revenue
        assert revenue.external_due_cents == revenue.external_net_cents == 0
        assert revenue.event_net_cents == revenue.net_cents
