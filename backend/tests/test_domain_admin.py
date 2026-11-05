from datetime import UTC, date, datetime, timedelta

import pytest

from app.domain import admins
from app.domain.admins import can_remove_admin
from app.domain.booking import can_extend_hold, can_refund, status_after_void
from app.domain.payments_review import (
    COLLECT_BALANCE,
    COLLECT_EXPIRED,
    COLLECT_WAITING,
    collect_group,
    review_reason,
)
from app.domain.presence import (
    DaySummary,
    Presence,
    has_evening,
    presence_by_slot,
    presences,
    week_summary,
)
from app.domain.reminders import reminders_to_keep_after_extension
from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    STATUS_REFUNDED,
)

MON, TUE, WED = date(2026, 7, 13), date(2026, 7, 14), date(2026, 7, 15)


class TestEveningPresence:
    def test_explicit_evening(self):
        assert has_evening({"evening"})

    def test_whole_day_implies_evening(self):
        assert has_evening({"morning", "afternoon"})

    def test_a_single_daytime_slot_does_not(self):
        assert not has_evening({"morning"})
        assert not has_evening({"afternoon"})
        assert not has_evening(set())

    def test_derived_evening_is_added_and_marked(self):
        rows = presences([(1, MON, "morning"), (1, MON, "afternoon")])
        assert Presence(1, MON, "evening", derived=True) in rows
        assert len(rows) == 3

    def test_explicit_evening_is_not_duplicated_as_derived(self):
        rows = presences([(1, MON, "morning"), (1, MON, "afternoon"), (1, MON, "evening")])
        evenings = [r for r in rows if r.period == "evening"]
        assert evenings == [Presence(1, MON, "evening", derived=False)]

    def test_each_day_is_derived_on_its_own(self):
        rows = presences([(1, MON, "morning"), (1, TUE, "afternoon")])
        assert all(not r.derived for r in rows)

    def test_people_are_kept_apart(self):
        rows = presences([(1, MON, "morning"), (2, MON, "afternoon")])
        assert not any(r.derived for r in rows)

    def test_grouped_by_slot(self):
        rows = presences([(1, MON, "morning"), (2, MON, "morning"), (1, MON, "afternoon")])
        grouped = presence_by_slot(rows)
        assert [r.person_id for r in grouped[(MON, "morning")]] == [1, 2]
        assert [r.person_id for r in grouped[(MON, "afternoon")]] == [1]
        assert [(r.person_id, r.derived) for r in grouped[(MON, "evening")]] == [(1, True)]


class TestWeekSummary:
    def test_counts_per_period_with_derived_evening_and_distinct_people(self):
        rows = presences(
            [
                (1, MON, "morning"), (1, MON, "afternoon"),  # whole day: evening derived
                (2, MON, "morning"),
                (3, MON, "evening"),
                (1, TUE, "morning"),
            ]
        )  # fmt: skip
        monday, tuesday = week_summary(rows, [MON, TUE])
        assert monday == DaySummary(
            MON, morning=2, afternoon=1, evening=2, evening_derived=1, people=3
        )
        assert tuesday == DaySummary(TUE, 1, 0, 0, 0, 1)

    def test_days_without_anyone_are_listed_with_zeros(self):
        summary = week_summary(presences([(1, MON, "morning")]), [MON, TUE, WED])
        assert [s.day for s in summary] == [MON, TUE, WED]
        assert summary[2] == DaySummary(WED, 0, 0, 0, 0, 0)

    def test_the_same_person_on_two_slots_counts_once_in_people(self):
        summary = week_summary(presences([(1, MON, "morning"), (1, MON, "evening")]), [MON])
        assert summary[0].people == 1


class TestReviewReason:
    @pytest.mark.parametrize(
        ("status", "due", "paid", "reason"),
        [
            (STATUS_EXPIRED, 1100, 500, "scaduta_con_pagamenti"),
            (STATUS_CONFIRMED, 1200, 1100, "saldo_positivo"),
            (STATUS_CONFIRMED, 1100, 1200, "credito"),
            (STATUS_CANCEL_REQUESTED, 1100, 1100, "disdetta_da_rimborsare"),
            (STATUS_CANCEL_REQUESTED, 1100, 0, "disdetta_da_chiudere"),
            (STATUS_PENDING, 1100, 500, "pagamento_parziale"),
        ],
    )
    def test_each_reason(self, status, due, paid, reason):
        assert review_reason(status, due, paid) == reason

    @pytest.mark.parametrize(
        ("status", "due", "paid"),
        [
            (STATUS_CONFIRMED, 1100, 1100),  # settled
            (STATUS_PENDING, 1100, 0),  # nothing paid yet: just waiting
            (STATUS_EXPIRED, 1100, 0),  # expired, nothing to look at
            (STATUS_REFUNDED, 1100, 1100),  # done
        ],
    )
    def test_nothing_to_review(self, status, due, paid):
        assert review_reason(status, due, paid) is None


class TestRemoveAdmin:
    def check(self, **overrides):
        values = dict(
            target_id=2, actor_id=1, admin_count=3, target_email="b@x.org", seed_email="a@x.org"
        )
        return can_remove_admin(**{**values, **overrides})

    def test_a_normal_admin_can_be_removed(self):
        assert self.check().allowed

    def test_not_yourself(self):
        assert self.check(target_id=1).reason == admins.SELF

    def test_not_the_last_admin(self):
        assert self.check(admin_count=1).reason == admins.LAST

    def test_not_the_seed_admin_whatever_the_case_of_the_email(self):
        assert self.check(target_email=" A@X.org ").reason == admins.SEED

    def test_works_without_a_seed_email(self):
        assert self.check(seed_email=None).allowed


class TestRefundAndVoidRules:
    def test_refund_only_on_a_requested_cancellation(self):
        assert can_refund(STATUS_CANCEL_REQUESTED, 1100, 1100)
        assert not can_refund(STATUS_CONFIRMED, 1100, 1100)
        assert not can_refund(STATUS_REFUNDED, 1100, 1100)

    def test_refund_cannot_exceed_what_was_paid_nor_be_negative(self):
        assert can_refund(STATUS_CANCEL_REQUESTED, 1100, 600)
        assert can_refund(STATUS_CANCEL_REQUESTED, 0, 0)
        assert not can_refund(STATUS_CANCEL_REQUESTED, 1100, 1101)
        assert not can_refund(STATUS_CANCEL_REQUESTED, 1100, -1)

    def test_only_a_pending_booking_can_have_its_hold_extended(self):
        assert can_extend_hold(STATUS_PENDING)
        assert not can_extend_hold(STATUS_CONFIRMED)
        assert not can_extend_hold(STATUS_EXPIRED)

    def test_confirmed_goes_back_to_pending_when_no_longer_covered(self):
        assert status_after_void(STATUS_CONFIRMED, 1100, 500) == STATUS_PENDING

    def test_confirmed_stays_confirmed_when_still_covered(self):
        assert status_after_void(STATUS_CONFIRMED, 1100, 1100) == STATUS_CONFIRMED
        assert status_after_void(STATUS_CONFIRMED, 1100, 1500) == STATUS_CONFIRMED

    @pytest.mark.parametrize("status", [STATUS_PENDING, STATUS_EXPIRED, STATUS_CANCEL_REQUESTED])
    def test_other_statuses_do_not_change(self, status):
        assert status_after_void(status, 1100, 0) == status


class TestHoldExtension:
    START = datetime(2026, 7, 1, 10, 0, tzinfo=UTC)

    def keep(self, now, mid, final, days=6):
        return reminders_to_keep_after_extension(
            self.START, self.START + timedelta(days=days), mid, final, now
        )

    def test_reminders_sent_for_the_old_hold_are_due_again_when_the_new_ones_are_ahead(self):
        sent = self.START + timedelta(hours=40)
        now = self.START + timedelta(hours=70)  # old hold was 3 days: both reminders were sent
        assert self.keep(now, sent, sent) == (None, None)

    def test_a_reminder_whose_new_threshold_has_passed_stays_marked(self):
        sent = self.START + timedelta(hours=40)
        now = self.START + timedelta(hours=100)  # 6 days: middle at 72h and final at 120h
        mid, final = self.keep(now, sent, sent)
        assert mid == sent and final is None

    def test_nothing_sent_stays_nothing(self):
        assert self.keep(self.START + timedelta(hours=70), None, None) == (None, None)


class TestCollectGroup:
    @pytest.mark.parametrize(
        ("status", "due", "paid", "group"),
        [
            (STATUS_PENDING, 1100, 0, COLLECT_WAITING),
            (STATUS_PENDING, 1100, 500, COLLECT_WAITING),
            (STATUS_CONFIRMED, 1200, 1100, COLLECT_BALANCE),
            (STATUS_EXPIRED, 1100, 0, COLLECT_EXPIRED),
            (STATUS_EXPIRED, 1100, 500, COLLECT_EXPIRED),
        ],
    )
    def test_money_still_to_come(self, status, due, paid, group):
        assert collect_group(status, due, paid) == group

    @pytest.mark.parametrize(
        ("status", "due", "paid"),
        [
            (STATUS_CONFIRMED, 1100, 1100),  # settled
            (STATUS_CONFIRMED, 1100, 1200),  # credit: a job for "to review"
            (STATUS_PENDING, 1100, 1100),  # nothing left to pay
            (STATUS_CANCEL_REQUESTED, 1100, 0),
            (STATUS_REFUNDED, 1100, 1100),
        ],
    )
    def test_nothing_to_collect(self, status, due, paid):
        assert collect_group(status, due, paid) is None
