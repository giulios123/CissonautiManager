from datetime import datetime, timedelta
from typing import Literal

Reminder = Literal["mid", "final"]

FINAL_REMINDER_BEFORE_DEADLINE = timedelta(hours=24)
# Below this hold length the two thresholds overlap, so only the middle reminder exists.
MIN_HOLD_FOR_FINAL_REMINDER = 2 * FINAL_REMINDER_BEFORE_DEADLINE


def due_reminder(
    hold_started_at: datetime,
    hold_expires_at: datetime,
    mid_sent_at: datetime | None,
    final_sent_at: datetime | None,
    now: datetime,
) -> Reminder | None:
    """Which payment reminder is due now for a pending booking, if any.

    Two reminders per hold, each sent at most once: at half of the hold and 24 hours before
    the deadline. A late run sends only the final one. Holds shorter than 48 hours get only
    the middle one. After the deadline nothing is due: the booking is expired.
    """
    if now >= hold_expires_at:
        return None
    hold = hold_expires_at - hold_started_at
    has_final = hold >= MIN_HOLD_FOR_FINAL_REMINDER
    if (
        has_final
        and final_sent_at is None
        and now >= hold_expires_at - FINAL_REMINDER_BEFORE_DEADLINE
    ):
        return "final"
    # Once the final reminder went out, the middle one would be stale.
    if mid_sent_at is None and final_sent_at is None and now >= hold_started_at + hold / 2:
        return "mid"
    return None
