"""Tests for barcode normalisation"""

import logging

import pytest

from app.barcodes import has_valid_check_digit, normalize_barcode


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("7310865004703", "7310865004703"),  # EAN-13 stays as it is
        (" 7310865004703\n", "7310865004703"),  # scanner newline and spaces removed
        ("7310 8650 04703", "7310865004703"),  # spaces typed by a person removed
        ("036000291452", "0036000291452"),  # UPC-A --> GTIN-13
        ("96385074", "96385074"),  # EAN-8 stays 8 digits
    ],
)
def test_noramlize_barcode(raw, expected):
    assert normalize_barcode(raw) == expected

@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "73108650047O3",
        "abc",
        "7310-865004703",
        "²"
    ]
)
def test_normalize_barcode_rejects_non_digits(raw):
    with pytest.raises(ValueError):
        normalize_barcode(raw)

def test_invalid_check_digit_is_accepted_with_a_warning(caplog):
    """A misread must not lose the scan, but should be visible in the logs"""

    # DEBUG < INFO < WARNING < ERROR < CRITICAL
    # Covers Warning and above
    with caplog.at_level(logging.WARNING):
        assert normalize_barcode("7310865004704") == "7310865004704"
    assert "invalid check digit" in caplog.text


def test_unusual_length_is_accepted_with_a_warning(caplog):
    with caplog.at_level(logging.WARNING):
        assert normalize_barcode("12345") == "12345"
    assert "unusual length" in caplog.text
    

@pytest.mark.parametrize(
    ("code", "valid"),
    [
        ("7310865004703", True),
        ("7310865004704", False),
        ("0036000291452", True),
        ("96385074", True),
        ("96385075", False),
    ],
)
def test_has_valid_check_digit(code, valid):
    """Good barcodes pass the check digit test and altered ones fail"""
    assert has_valid_check_digit(code) is valid