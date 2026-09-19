"""
School-calendar date helpers.

"Today" is the school's day, not the server's: the boxes run in UTC and the
school is in IST, so late in the evening they disagree on the date. Every
"not in the past" rule compares against IST so a teacher is never told that
today is yesterday.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

SCHOOL_TZ = ZoneInfo("Asia/Kolkata")


def today() -> date:
    return datetime.now(SCHOOL_TZ).date()


def reject_past(value: date | None, label: str) -> date | None:
    """Pydantic-validator helper: raise if `value` is before today (IST)."""
    if value is not None and value < today():
        raise ValueError(f"{label} cannot be in the past")
    return value
