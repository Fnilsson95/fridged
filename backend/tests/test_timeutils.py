"""Tests for the time helpers"""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.timeutils import to_utc_iso, utc_now_iso


def test_to_utc_iso_converts_to_utc():
    """Test if conversion from another timezone to UTC is correct"""
    stockholm_winter = timezone(timedelta(hours=1))
    moment = datetime(2026, 11, 6, 18, 0, tzinfo=stockholm_winter)
    assert to_utc_iso(moment) == "2026-11-06T17:00:00.000+00:00"


def test_to_utc_iso_rejects_naive_datetimes():
    """Refuse a time that has no timezone - tzinfo"""
    with pytest.raises(ValueError):
        to_utc_iso(datetime(2026, 11, 6, 18, 0))


def test_utc_now_iso_has_the_fixed_format():
    """Always return a valid UTC timestamp in the same shape"""
    value = utc_now_iso()

    # Parses back, is UTC, and has exactly three decimals
    assert datetime.fromisoformat(value).tzinfo == UTC
    assert value.endswith("+00:00")
    assert len(value.split(".")[1]) == len("123+00:00")
