"""Database tables (SQLAlchemy models)

Defines tables and the rules of the database itself enforces.

Tables:
    * products - one per barcode, in either the unknown or the known register
    * events - an append-only log of every recorded scan

Conventions:
    * Money is integer öre (1250 = 12,50kr), never a float (UI will convert it)
    * Timestamps are UTC ISO-8601 strings in one fixed format so they sort correctly as text
    * Stock and totals are not stored, they are computed from "events"
"""

from sqlalchemy import CheckConstraint, ForeignKey, Index, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.timeutils import utc_now_iso

# Naming rules for constraints and indexes. Without names, SQLite constraint are anonymous
# and Alembic can't change or drop them later
# The "ck" rule uses the name we give each CheckConstraint below
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Parent class of all tables. Alembic reads Base.metadata to see the schema"""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Product(Base):
    """One row per barcode: what an item is.
    status 'unknown' = only the barcode is known, needs manual handling on the website.
    status 'known'   = name, brand and price are filled in.
    """

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("status IN ('unknown', 'known')", name="status_valid"),
        CheckConstraint(
            "current_price_ore IS NULL OR current_price_ore >= 0", name="price_non_negative"
        ),
        # The rule from data-model.md and enforced by the database itself:
        # a known product must always have name, brand and price.
        CheckConstraint(
            "status = 'unknown' OR (name IS NOT NULL AND brand IS NOT NULL "
            "AND current_price_ore IS NOT NULL)",
            name="known_requires_info",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Normalized barcode stored as text so leading zeros are kept
    barcode: Mapped[str] = mapped_column(unique=True)
    status: Mapped[str] = mapped_column(default="unknown", server_default="unknown")

    # These are NULL while unknown
    name: Mapped[str | None]
    brand: Mapped[str | None]
    size_label: Mapped[str | None]  # Example: 500g - 1l
    image_url: Mapped[str | None]
    # Money is always integer öre (1250 = 12,50kr) The UI converts to SEK
    current_price_ore: Mapped[int | None]

    created_at: Mapped[str] = mapped_column(default=utc_now_iso)
    updated_at: Mapped[str] = mapped_column(default=utc_now_iso, onupdate=utc_now_iso)


class Event(Base):
    """A log of every recorded scan. Append-only: rows are never edited or deleted
    An undo only sets reverted_at.
    """

    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("type IN ('in', 'out', 'stocktake')", name="type_valid"),
        CheckConstraint("unit_price_ore IS NULL OR unit_price_ore >= 0", name="price_non_negative"),
        # Indexes for the queries we will run most (stock per product, totals per period).
        Index("ix_events_product_time", "product_id", "occurred_at"),
        Index("ix_events_type_time", "type", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # UUID made by the devide. A repeated scan with the same id is a duplicate
    client_event_id: Mapped[str] = mapped_column(unique=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    type: Mapped[str]  # "in", "out, "stocktake"
    # Price at the time of scanning, so old totals never change when a price changes
    # NULL while the product is unknown. Filled in when product is handled manually
    unit_price_ore: Mapped[int | None]
    occurred_at: Mapped[str]  # when it was scanned (device clock, UTC)
    received_at: Mapped[str] = mapped_column(default=utc_now_iso)  # when the backend got it
    reverted_at: Mapped[str | None]  # set by undo. NULL = the event counts
