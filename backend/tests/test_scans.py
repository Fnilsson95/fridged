"""Tests for POST /api/scans.

""test_scan_rules"" has one case per row of the scan-rules table in
docs/data-model.md. The other tests cover duplicates, undo, normalization,
price snapshots and input validation.
"""

from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.models import Event, Product

MILK = "7310865004703"
SCANNED_AT = "2026-11-06T18:00:00+01:00"  # 17:00 UTC


def scan(client, mode, barcode=MILK, *, client_event_id=None, occurred_at=SCANNED_AT):
    """Send one scan to the API, like the device would."""
    payload = {
        "barcode": barcode,
        "mode": mode,
        "client_event_id": client_event_id or str(uuid4()),
        "occurred_at": occurred_at,
    }
    return client.post("/api/scans", json=payload)


def make_product(db, state, stock):
    """Prepare the database with a product in the given state with "stock" packages.

    state: "never_seen" (no product), "unknown" (barcode only) or "known".
    """
    if state == "never_seen":
        return
    if state == "known":
        product = Product(
            barcode=MILK, status="known", name="Mellanmjölk", brand="Arla", current_price_ore=1250
        )
    else:
        product = Product(barcode=MILK)
    db.add(product)
    db.flush()
    for _ in range(stock):
        db.add(
            Event(
                client_event_id=str(uuid4()),
                product_id=product.id,
                type="in",
                unit_price_ore=product.current_price_ore,
                occurred_at="2026-11-01T12:00:00.000+00:00",
            )
        )
    # Commit, so the API's own session (same database) sees the data.
    db.commit()


def count_events(db):
    return db.scalar(select(func.count()).select_from(Event))


@pytest.mark.parametrize(
    ("state", "stock_before", "mode", "result", "event_type", "price", "stock_after"),
    [
        ("known", 0, "in", "stocked", "in", 1250, 1),
        ("known", 0, "stocktake", "stocktaken", "stocktake", None, 1),
        ("known", 1, "out", "used", "out", 1250, 0),
        ("known", 0, "out", "not_in_stock", None, None, 0),
        ("never_seen", 0, "in", "new_item", "in", None, 1),
        ("never_seen", 0, "stocktake", "new_item", "stocktake", None, 1),
        ("never_seen", 0, "out", "not_in_stock", None, None, 0),
        ("unknown", 0, "in", "stocked", "in", None, 1),
        ("unknown", 0, "stocktake", "stocktaken", "stocktake", None, 1),
        ("unknown", 1, "out", "used", "out", None, 0),
        ("unknown", 0, "out", "not_in_stock", None, None, 0),
    ],
    ids=[
        "known-in",
        "known-stocktake",
        "known-out-with-stock",
        "known-out-no-stock",
        "new-in",
        "new-stocktake",
        "new-out",
        "unknown-in",
        "unknown-stocktake",
        "unknown-out-with-stock",
        "unknown-out-no-stock",
    ],
)
def test_scan_rules(client, db, state, stock_before, mode, result, event_type, price, stock_after):
    make_product(db, state, stock_before)
    events_before = count_events(db)

    response = scan(client, mode)

    assert response.status_code == 200
    body = response.json()
    assert body["result"] == result
    assert body["stock"] == stock_after

    # The product always exists afterwards, even for a never-seen OUT scan.
    db.expire_all()  # forget cached objects, read fresh from the database
    product = db.scalar(select(Product).where(Product.barcode == MILK))
    assert product is not None
    assert body["product"]["id"] == product.id

    if event_type is None:
        assert body["event_id"] is None
        assert count_events(db) == events_before
    else:
        event = db.get(Event, body["event_id"])
        assert event.type == event_type
        assert event.unit_price_ore == price
        assert count_events(db) == events_before + 1


def test_same_scan_twice_is_recorded_once(client, db):
    make_product(db, "known", 0)
    scan_id = str(uuid4())

    first = scan(client, "in", client_event_id=scan_id).json()
    second = scan(client, "in", client_event_id=scan_id).json()

    assert first["result"] == "stocked"
    assert second["result"] == "duplicate"
    assert second["event_id"] == first["event_id"]
    assert second["stock"] == 1
    assert count_events(db) == 1


def test_reverted_events_do_not_count(client, db):
    make_product(db, "known", 1)
    event = db.scalar(select(Event))
    event.reverted_at = "2026-11-01T12:05:00.000+00:00"
    db.commit()

    assert scan(client, "out").json()["result"] == "not_in_stock"


def test_stock_never_goes_negative(client, db):
    make_product(db, "known", 1)

    assert scan(client, "out").json()["result"] == "used"
    second = scan(client, "out").json()

    assert second["result"] == "not_in_stock"
    assert second["stock"] == 0


def test_upc_a_and_its_gtin_13_form_are_the_same_product(client):
    first = scan(client, "in", barcode="036000291452").json()
    second = scan(client, "out", barcode="0036000291452").json()

    assert first["product"]["barcode"] == "0036000291452"
    assert second["result"] == "used"
    assert second["product"]["id"] == first["product"]["id"]


def test_price_is_a_snapshot_at_scan_time(client, db):
    make_product(db, "known", 0)
    scan(client, "in")
    product = db.scalar(select(Product))
    product.current_price_ore = 1500
    db.commit()
    scan(client, "in")

    prices = db.scalars(select(Event.unit_price_ore).order_by(Event.id)).all()
    assert prices == [1250, 1500]


def test_occurred_at_is_stored_in_utc(client, db):
    body = scan(client, "in", occurred_at="2026-11-06T18:00:00+01:00").json()

    event = db.get(Event, body["event_id"])
    assert event.occurred_at == "2026-11-06T17:00:00.000+00:00"


@pytest.mark.parametrize(
    "overrides",
    [
        {"barcode": "abc"},
        {"barcode": ""},
        {"mode": "used"},
        {"client_event_id": "not-a-uuid"},
        {"occurred_at": "2026-11-06T18:00:00"},  # no time zone
    ],
    ids=["letters", "empty-barcode", "bad-mode", "bad-uuid", "naive-time"],
)
def test_invalid_input_is_rejected(client, db, overrides):
    payload = {
        "barcode": MILK,
        "mode": "in",
        "client_event_id": str(uuid4()),
        "occurred_at": SCANNED_AT,
        **overrides, # unpacks parametrized dictionary and overrides and replaces one field at a time
    }
    response = client.post("/api/scans", json=payload)

    assert response.status_code == 422 # Error code - unprocessable content
    assert count_events(db) == 0