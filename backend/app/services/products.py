"""Product rules - listing, editing, registering unknown items and deleting"""

from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy import Select, case, exists, func, or_, select, update
from sqlalchemy.orm import Session

from app.errors import ConflictError, InvalidRequestError, NotFoundError
from app.models import Event, Product


# A know product must have these
REQUIRED_FOR_KNOWN = ("name", "brand", "current_price_ore")


@dataclass(frozen=True)
class ProductRow:
    """A product together with the numbers computed from its events"""

    product: Product
    stock: int
    scan_count: int
    last_scanned_at: str | None

    @property
    def value_ore(self) -> int | None:
        """What the packages in the fridge are worht, in öre"""
        if self.product.current_price_ore is None:
            return None
        return self.stock * self.product.current_price_ore


def _event_stats():
    """Subquery for one row per product with stock, scan count and last scan

    SELECT product_id,
               sum(CASE WHEN reverted THEN 0 WHEN type = 'out' THEN -1 ELSE 1 END),
               sum(CASE WHEN reverted THEN 0 ELSE 1 END),
               max(CASE WHEN reverted THEN NULL ELSE occurred_at END)
        FROM events GROUP BY product_id
    """

    counts = Event.reverted_at.is_(None)
    return (
        select(
            Event.product_id.label("product_id"),
            func.sum(case((~counts, 0), (Event.type == "out", -1), else_=1)).label("stock"),
            func.sum(case((counts, 1), else_=0)).label("scan_count"),
            # max() skips nulls so undone events are ignored
            func.max(case((counts, Event.occurred_at))).label("last_scanned_at"),
        )
        .group_by(Event.product_id)
        .subquery()
    )


def _products_query() -> Select:
    """SELECT products with their stats. Products without event get 0"""

    stats = _event_stats()
    return select(
        Product,
        func.coalesce(stats.c.stock, 0).label("stock"),
        func.coalesce(stats.c.scan_count, 0).label("scan_count"),
        stats.c.last_scanned_at,
    ).outerjoin(stats, stats.c.product_id == Product.id)


def _to_rows(result) -> list[ProductRow]:
    return [
        ProductRow(product=p, stock=stock, scan_count=count, last_scanned_at=last)
        for p, stock, count, last in result
    ]


def list_products(
    db: Session,
    *,
    status: Literal["unknown", "known"] | None = None,
    search: str | None = None,
    in_stock: bool | None = None,
) -> list[ProductRow]:
    """Return products with their stock, filtered and sorted"""
    stmt = _products_query()
    stock = stmt.selected_columns.stock

    if status is not None:
        stmt = stmt.where(Product.status == status)
    if search:
        # autoescape: a search for "50%" looks for the text "50%"
        stmt = stmt.where(
            or_(
                Product.name.icontains(search, autoescape=True),
                Product.brand.icontains(search, autoescape=True),
                Product.barcode.contains(search, autoescape=True),
            )
        )
    if in_stock is True:
        stmt = stmt.where(stock > 0)
    elif in_stock is False:
        stmt = stmt.where(stock <= 0)

    stmt = stmt.order_by(
        Product.status.desc(),  # "unknown" sorts after "known", so desc puts it first
        func.lower(Product.name),
        Product.created_at.desc(),
    )
    return _to_rows(db.execute(stmt))


def get_product(db: Session, product_id: int) -> ProductRow:
    """Return one product with its stats"""

    rows = _to_rows(db.execute(_products_query().where(Product.id == product_id)))

    if not rows:
        raise NotFoundError(f"Product {product_id} not found")
    return rows[0]


def update_product(db: Session, product_id: int, changes: dict[str, Any]) -> ProductRow:
    """Apply changes to a product and commit

    An unknown product becomes known when we add name, brand and a price.
    """

    product = db.get(Product, product_id)
    if product is None:
        raise NotFoundError(f"Product {product_id} not found")

    # Check the result before touching the product
    result = {field: changes.get(field, getattr(product, field)) for field in REQUIRED_FOR_KNOWN}
    missing = [field for field, value in result.items() if value is None]
    if missing:
        raise InvalidRequestError(f"A product need {', '.join(missing)} to be known")

    for field, value in changes.items():
        setattr(product, field, value)

    if product.status == "unknown":
        product.status = "known"
        db.execute(
            update(Event)
            .where(
                Event.product_id == product_id,
                Event.unit_price_ore.is_(None),
                Event.type.in_(("in", "out")),
            )
            .values(unit_price_ore=product.current_price_ore)
        )

    db.commit()
    return get_product(db, product_id)


def delete_product(db: Session, product_id: int) -> None:
    """Delete a product that was added by mistake

    Only allowed when the product has no events at all, including undone ones as events are never deleted.
    """

    product = db.get(Product, product_id)

    if product is None:
        raise NotFoundError(f"Product {product_id} not found")

    has_events = db.scalar(select(exists().where(Event.product_id == product_id)))
    if has_events:
        raise ConflictError(f"Product {product_id} has scans and can't be deleted. Edit it instead")

    db.delete(product)
    db.commit()
