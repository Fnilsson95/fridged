import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Event, Product


def test_unknown_product_needs_only_a_barcode(db):
    # An unknown product has no name, brand or price yet. This must be allowed.
    db.add(Product(barcode="7310865004703"))
    db.commit()


def test_known_product_requires_name_brand_and_price(db):
    # Status 'known' without a brand must be rejected by the database rule.
    db.add(Product(barcode="7310865004703", status="known", name="Milk", current_price_ore=1250))
    with pytest.raises(IntegrityError):
        db.commit()


def test_event_requires_an_existing_product(db):
    # product_id 999 does not exist. This only fails if foreign keys are switched on,
    # so the test also proves the PRAGMA in db.py works.
    db.add(
        Event(
            client_event_id="11111111-1111-1111-1111-111111111111",
            product_id=999,
            type="in",
            occurred_at="2026-11-01T12:00:00.000+00:00",
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()
