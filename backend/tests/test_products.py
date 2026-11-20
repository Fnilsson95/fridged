"""Tests for the product endpoints: list, get, PATCH and DELETE."""

import pytest
from sqlalchemy import select

from app.models import Event, Product

COKE = "5000112696578"
MILK = "7310865004703"

REGISTER_COKE = {"name": "Coca-Cola Zero", "brand": "Coca-Cola", "current_price_ore": 1250}


def register(client, product_id, **fields):
    """Handle an unknown product (name, brand, price) and return the response."""
    return client.patch(f"/api/products/{product_id}", json={**REGISTER_COKE, **fields})


def test_empty_list(client):
    assert client.get("/api/products").json() == []


def test_stock_value_and_scan_count(client, scan):
    product_id = scan("in", COKE)["product"]["id"]
    scan("in", COKE)
    register(client, product_id)
    scan("out", COKE, occurred_at="2026-11-07T08:00:00+01:00")

    [coke] = client.get("/api/products").json()

    assert coke["stock"] == 1
    assert coke["value_ore"] == 1250  # 1 package x 12,50 kr
    assert coke["scan_count"] == 3
    assert coke["last_scanned_at"] == "2026-11-07T07:00:00.000+00:00"


def test_unknown_product_has_no_value(client, scan):
    scan("in", COKE)
    [coke] = client.get("/api/products").json()
    assert coke["stock"] == 1
    assert coke["value_ore"] is None


def test_undone_scans_do_not_count(client, db, scan):
    scan("in", COKE)
    scan("in", COKE)
    event = db.scalars(select(Event)).first()
    event.reverted_at = "2026-11-06T17:05:00.000+00:00"
    db.commit()

    [coke] = client.get("/api/products").json()
    assert coke["stock"] == 1
    assert coke["scan_count"] == 1


def test_filters(client, scan):
    coke_id = scan("in", COKE)["product"]["id"]
    register(client, coke_id)
    scan("in", MILK)  # stays unknown
    scan("out", MILK)  # stock 0

    def barcodes(query):
        return [p["barcode"] for p in client.get(f"/api/products?{query}").json()]

    assert barcodes("status=unknown") == [MILK]
    assert barcodes("status=known") == [COKE]
    assert barcodes("in_stock=true") == [COKE]
    assert barcodes("in_stock=false") == [MILK]
    assert barcodes("search=zero") == [COKE]  # name, case-insensitive
    assert barcodes("search=coca") == [COKE]  # brand
    assert barcodes("search=731086") == [MILK]  # part of a barcode


def test_unknown_products_are_listed_first(client, scan):
    coke_id = scan("in", COKE)["product"]["id"]
    register(client, coke_id)
    scan("in", MILK)

    assert [p["status"] for p in client.get("/api/products").json()] == ["unknown", "known"]


def test_get_missing_product_is_404(client):
    response = client.get("/api/products/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Product 999 not found"}


def test_registering_makes_it_known_and_backfills_prices(client, db, scan):
    product_id = scan("in", COKE)["product"]["id"]
    scan("stocktake", COKE)
    scan("out", COKE)

    response = register(client, product_id)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "known"
    assert body["name"] == "Coca-Cola Zero"
    prices = db.scalars(select(Event.unit_price_ore).order_by(Event.id)).all()
    assert prices == [1250, None, 1250]  # in, stocktake (never priced), out


@pytest.mark.parametrize("missing", ["name", "brand", "current_price_ore"])
def test_registering_requires_name_brand_and_price(client, db, scan, missing):
    product_id = scan("in", COKE)["product"]["id"]
    fields = {k: v for k, v in REGISTER_COKE.items() if k != missing}

    response = client.patch(f"/api/products/{product_id}", json=fields)

    assert response.status_code == 422
    assert missing in response.json()["detail"]
    db.expire_all()
    assert db.get(Product, product_id).status == "unknown"
    assert db.scalar(select(Event.unit_price_ore)) is None  # nothing backfilled


def test_new_price_only_affects_future_scans(client, db, scan):
    product_id = scan("in", COKE)["product"]["id"]
    register(client, product_id)

    client.patch(f"/api/products/{product_id}", json={"current_price_ore": 1500})
    scan("in", COKE)

    prices = db.scalars(select(Event.unit_price_ore).order_by(Event.id)).all()
    assert prices == [1250, 1500]


def test_known_product_cannot_lose_its_name(client, scan):
    product_id = scan("in", COKE)["product"]["id"]
    register(client, product_id)

    response = client.patch(f"/api/products/{product_id}", json={"name": None})
    assert response.status_code == 422


def test_optional_fields_can_be_cleared(client, scan):
    product_id = scan("in", COKE)["product"]["id"]
    register(client, product_id, size_label="33 cl")

    body = client.patch(f"/api/products/{product_id}", json={"size_label": None}).json()
    assert body["size_label"] is None
    assert body["name"] == "Coca-Cola Zero"  # fields not sent are unchanged


@pytest.mark.parametrize(
    "changes",
    [
        {"current_price_ore": -1},
        {"name": "   "},
        {"price": 1250},  # unknown field (typo)
        {"status": "unknown"},  # status is not editable
        {"barcode": "123"},  # barcode is not editable
    ],
    ids=["negative-price", "blank-name", "unknown-field", "status", "barcode"],
)
def test_invalid_changes_are_rejected(client, scan, changes):
    product_id = scan("in", COKE)["product"]["id"]
    register(client, product_id)

    response = client.patch(f"/api/products/{product_id}", json=changes)
    assert response.status_code == 422


def test_patch_missing_product_is_404(client):
    assert client.patch("/api/products/999", json=REGISTER_COKE).status_code == 404


def test_product_without_events_can_be_deleted(client, scan):
    # An OUT scan of a never-seen barcode creates the product but no event.
    product_id = scan("out", COKE)["product"]["id"]

    response = client.delete(f"/api/products/{product_id}")

    assert response.status_code == 204
    assert client.get(f"/api/products/{product_id}").status_code == 404
    # Scanned again later, it starts fresh as a new unknown item.
    assert scan("in", COKE)["result"] == "new_item"


def test_product_with_events_cannot_be_deleted(client, db, scan):
    product_id = scan("in", COKE)["product"]["id"]
    # Even an undone scan is still an event, so it still blocks deletion.
    event = db.scalar(select(Event))
    event.reverted_at = "2026-11-06T17:05:00.000+00:00"
    db.commit()

    response = client.delete(f"/api/products/{product_id}")

    assert response.status_code == 409
    assert client.get(f"/api/products/{product_id}").status_code == 200


def test_delete_missing_product_is_404(client):
    assert client.delete("/api/products/999").status_code == 404
