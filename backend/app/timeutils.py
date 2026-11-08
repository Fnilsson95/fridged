"""
Time helpers

Every timestamp is stored as UTC ISO-8601 text in one fixed format (Example: 2026-11-08T14:07:00.000Z)
These helpers are the only place that format is produced, so all timestamp in the DB sorts correctly as text
"""

from datetime import UTC, datetime

def to_utc_iso(moment: datetime) -> str:
    """Converts time to the stored UTC text format."""

    if moment.tzinfo is None:
        raise ValueError("datetime must be timezone aware")
    return moment.astimezone(UTC).isoformat(timespec="milliseconds")

def utc_now_iso() -> str:
    """Return the correct time in the stored UTC text format
    
    Passed to model columns as "default=utc_now_iso" (without parentheses)
    so it runs once for each new row
    """

    return to_utc_iso(datetime.now(UTC))