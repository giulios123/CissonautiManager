import re
from datetime import UTC, date, datetime, timedelta

from app.domain.booking import (
    available_seats,
    can_reactivate,
    effective_status,
    hold_deadline,
    occupies_seats,
)
from app.domain.codes import CODE_ALPHABET, generate_personal_code
from app.domain.fees import balance_cents, compute_fee, is_covered
from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    STATUS_PENDING,
    STATUS_REFUNDED,
)

NOW = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)


class TestFee:
    def test_default_fee_for_three_days(self):
        days = [date(2026, 7, 13), date(2026, 7, 14), date(2026, 7, 16)]
        assert compute_fee(days, base_cents=1000, per_day_cents=100) == 1300

    def test_morning_and_afternoon_of_same_day_count_once(self):
        same_day = [date(2026, 7, 13), date(2026, 7, 13)]
        assert compute_fee(same_day, 1000, 100) == 1100

    def test_no_slots_costs_only_base_fee(self):
        assert compute_fee([], 1000, 100) == 1000

    def test_non_contiguous_days_are_all_counted(self):
        days = [date(2026, 7, 13), date(2026, 7, 17)]
        assert compute_fee(days, 1000, 100) == 1200

    def test_balance_is_due_minus_paid(self):
        assert balance_cents(1300, 500) == 800
        assert balance_cents(1300, 1500) == -200

    def test_covered_when_paid_reaches_due(self):
        assert is_covered(1300, 1300)
        assert is_covered(1300, 1400)
        assert not is_covered(1300, 1299)


class TestHold:
    def test_deadline_is_n_times_24_hours_after_creation(self):
        assert hold_deadline(NOW, 3) == NOW + timedelta(hours=72)

    def test_pending_before_deadline_stays_pending(self):
        expires = NOW + timedelta(minutes=1)
        assert effective_status(STATUS_PENDING, expires, NOW) == STATUS_PENDING

    def test_pending_at_deadline_is_expired(self):
        assert effective_status(STATUS_PENDING, NOW, NOW) == STATUS_EXPIRED

    def test_pending_after_deadline_is_expired(self):
        expires = NOW - timedelta(seconds=1)
        assert effective_status(STATUS_PENDING, expires, NOW) == STATUS_EXPIRED

    def test_confirmed_never_expires(self):
        expires = NOW - timedelta(days=30)
        assert effective_status(STATUS_CONFIRMED, expires, NOW) == STATUS_CONFIRMED


class TestSeats:
    def test_only_pending_and_confirmed_occupy_seats(self):
        assert occupies_seats(STATUS_PENDING)
        assert occupies_seats(STATUS_CONFIRMED)
        assert not occupies_seats(STATUS_EXPIRED)
        assert not occupies_seats(STATUS_CANCEL_REQUESTED)
        assert not occupies_seats(STATUS_REFUNDED)

    def test_available_seats(self):
        assert available_seats(25, 20) == 5
        assert available_seats(25, 25) == 0

    def test_available_seats_never_negative(self):
        assert available_seats(25, 27) == 0

    def test_reactivation_needs_a_free_seat_in_every_slot(self):
        assert can_reactivate([3, 1, 10])
        assert not can_reactivate([3, 0, 10])

    def test_reactivation_of_booking_without_slots_is_allowed(self):
        assert can_reactivate([])


class TestPersonalCode:
    def test_format(self):
        for _ in range(200):
            assert re.fullmatch(r"CSC-[A-Z2-9]{4}", generate_personal_code())

    def test_no_ambiguous_characters(self):
        for char in "01OIL":
            assert char not in CODE_ALPHABET

    def test_codes_are_varied(self):
        assert len({generate_personal_code() for _ in range(100)}) > 90
