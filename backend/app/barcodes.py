"""
Barcode Normalization

Turns whatever the scanner (or a person) sends into the device
so same product always ends up with the same ""products.barcode" value

* Remove all whitespace (scanners might add a newline, people type spaces)
* Reject anything that is not only digits
* 12-digit barcodes get a leading 0 so they match the 13-digit European version.
  8-digit barcodes stay as they are.
* Check the GTIN check digit. The last digit of the barcode is a checksum.
  Drop the last digit. Multiply each number by 3 and 1 alternative. Sum it up and
  the sum should need the last digit to reach a value that is a multiple of 10.

"""

import logging

logger = logging.getLogger(__name__)

# Valid GTIN (Global Trade Item Number) lenghts (EAN-8, UPC-A, EAN-13 and GTIN-14)
GTIN_LENGTHS = {8, 12, 13, 14}


def normalize_barcode(raw: str) -> str:
    """Return a standard form of a scanned barcode"""

    # Split on any whitespace
    # remove spaces, tabs and newlines anywhere in the string
    code = "".join(raw.split())

    if not code:
        raise ValueError("Barcode is empty")

    # isdigit() also accepts "²" and other not pure 0-9 digits.
    # so we require plain ASCII also
    if not (code.isascii() and code.isdigit()):
        raise ValueError("Barcode must contain only digit 0-9")

    # UPC-A -> GTIN-13
    if len(code) == 12:
        code = "0" + code

    if len(code) not in GTIN_LENGTHS:
        logger.warning("Barcode %s has an unusual length (%d digits)", code, len(code))
    elif not has_valid_check_digit(code):
        logger.warning("Barcode %s has an invalid check digit", code)
    return code


def has_valid_check_digit(code: str) -> bool:
    """Check the last digit of a GTIN

    The check digit lets a scanner detect most misreads
    Going from right to left, multiply by 3 and 1, alternating, and add them up.
    The check digit is the number that brings that sum up to next multiple of 10.

    Example:
    "7310865004703"" has a weighted sum of 67, where the next multiple of 10 is 70.
    So the check digit must be 3, which it is.
    (7*1 + 3*3 + 1*1 + 0*3 + 8*1 + 6*3 + 5*1 + 0*3 + 0*1 + 4*3 + 7*1 + 0*3 = 67)
    """

    # Turn each character into a number
    digits = []
    for character in code:
        digits.append(int(character))

    # Split off the check digit (last) from the payload (the rest)
    check = digits[-1]
    payload = digits[:-1]

    # Go from right to left
    payload.reverse()

    # Multiply by 3 and 1 alternating, and add everything up
    total = 0
    for position in range(len(payload)):
        digit = payload[position]
        if position % 2 == 0:
            weight = 3
        else:
            weight = 1
        total = total + digit * weight

    # How much is missing to the next multiple of 10?
    expected = (10 - total % 10) % 10

    return expected == check
