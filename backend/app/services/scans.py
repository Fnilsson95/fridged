"""

Scan handling - what one scan from the device does. Turns one scan from the device into
a database change and a result. The logic behind POST /api/scans



Implements the scan rules. Every scan ends in one of six results:
    * stocked - IN scan of a product that already exists
    * stocktaken - STOCKTAKE scan on a product that already exists
    * used - OUT scan with stock > 0
    * new_item - IN scan of a barcode never seen before
    * not_in_stock - OUT scan with no stock. No event is recorded
    * duplicate - a client_event_id already processed

(Scan flow)
Scan arrives
    |
    |__ already seen? --> duplicate
    |
    |__ find/create product
    |
    |__ OUT and no stock? --> not_in_stock (no event)
    |
    |__ record event, commit --> new_item / stocked / stocktaken / used
"""

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Event, Product
from app.services.stock import get_stock

# Literal --> exactly these specific values
ScanMode = Literal["in", "out", "stocktake"]
ScanResult = Literal["stocked", "stocktaken", "used", "new_item", "not_in_stock", "duplicate"]


@dataclass(frozen=True)
class ScanOutcome:
    """What happened to one scan. The router turns this into the JSON response


    Attributes:
        * result - one of the six scans
        * product - the product the barcode belongs to
        * stock - the product's stock after the scan
        event_id - the recorded event or None
    """

    result: ScanResult
    product: Product
    stock: int
    event_id: int | None


def process_scan(
    db: Session,
    *,
    barcode: str,
    mode: ScanMode,
    client_event_id: str,
    occurred_at: str,
) -> ScanOutcome:
    """Apply one scan and commit it"""

    # Seen this scan before. Then record nothing
    duplicate = _find_duplicate(db, client_event_id)
    if duplicate is not None:
        return duplicate

    try:
        outcome = _record_scan(
            db,
            barcode=barcode,
            mode=mode,
            client_event_id=client_event_id,
            occurred_at=occurred_at,
        )
        db.commit()
    except IntegrityError:
        # The same scan arrived twice at the same time (a retry while first still running)
        # Rollback this request and undo
        db.rollback()
        duplicate = _find_duplicate(db, client_event_id)

        if duplicate is None:
            raise
        return duplicate
    return outcome


def _find_duplicate(db: Session, client_event_id: str) -> ScanOutcome | None:
    """Return a "duplicate" outcome if this scan was already recorded"""

    event = db.scalar(select(Event).where(Event.client_event_id == client_event_id))
    if event is None:
        return None
    return ScanOutcome(
        result="duplicate",
        product=db.get(Product, event.product_id),
        stock=get_stock(db, event.product_id),
        event_id=event.id,
    )


def _record_scan(
    db: Session, *, barcode: str, mode: ScanMode, client_event_id: str, occurred_at: str
) -> ScanOutcome:
    """Find or create the product and record the event. Does not commit"""

    product = db.scalar(select(Product).where(Product.barcode == barcode))

    # Store true or false, exists or not
    is_new = product is None
    if product is None:
        # Never seen. Create it in the unknown register
        product = Product(barcode=barcode)
        db.add(product)
        db.flush()  # Send the INSERT now (still uncommited) so product.id is set

    if mode == "out":
        stock = get_stock(db, product.id)
        if stock <= 0:
            # Nothing to use up. Record no event so stock don't go negative
            return ScanOutcome(result="not_in_stock", product=product, stock=stock, event_id=None)

    event = Event(
        client_event_id=client_event_id,
        product_id=product.id,
        type=mode,
        unit_price_ore=None if mode == "stocktake" else product.current_price_ore,
        occurred_at=occurred_at,
    )
    db.add(event)
    db.flush()  # set event.id and make the event count in the stock query below

    return ScanOutcome(
        result=_result_for(mode, is_new=is_new),
        product=product,
        stock=get_stock(db, product.id),
        event_id=event.id,
    )


def _result_for(mode: ScanMode, *, is_new: bool) -> ScanResult:
    """Pick the result name for a scan that recorded an event"""

    if is_new:
        return "new_item"
    return {"in": "stocked", "stocktake": "stocktaken", "out": "used"}[mode]
