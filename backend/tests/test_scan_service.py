"""Service-level tests for app.services.scans.

These call ""process_scan"" directly with a session, without HTTP. That is
possible because services know nothing about FastAPI.
"""

from uuid import uuid4

from app.models import Product
from app.services import scans as scan_service

MILK = "7310865004703"
SCANNED_AT = "2026-11-06T17:00:00.000+00:00"


def test_simultaneous_duplicate_is_reported_as_duplicate(db, monkeypatch):
    """Two requests with the same scan ID at the same moment.

    The second request's duplicate check runs before the first one has
    committed, so it finds nothing. Its INSERT then hits the unique
    constraint on client_event_id. The service must report "duplicate",
    not crash.

    We simulate the timing by making the first duplicate check "miss".
    """
    db.add(Product(barcode=MILK, status="known", name="Milk", brand="Arla", current_price_ore=1250))
    db.commit()
    scan_id = str(uuid4())
    first = scan_service.process_scan(
        db, barcode=MILK, mode="in", client_event_id=scan_id, occurred_at=SCANNED_AT
    )

    real_find_duplicate = scan_service._find_duplicate
    calls = []

    def miss_the_first_check(session, client_event_id):
        calls.append(client_event_id)
        if len(calls) == 1:
            return None  # "the other request hasn't committed yet"
        return real_find_duplicate(session, client_event_id)

    # monkeypatch swaps the function for this test only, and restores it after.
    monkeypatch.setattr(scan_service, "_find_duplicate", miss_the_first_check)

    second = scan_service.process_scan(
        db, barcode=MILK, mode="in", client_event_id=scan_id, occurred_at=SCANNED_AT
    )

    assert second.result == "duplicate"
    assert second.event_id == first.event_id
    assert second.stock == 1
    assert len(calls) == 2  # missed once, then found it after the rollback