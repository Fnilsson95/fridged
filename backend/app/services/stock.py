"""
Stock calculation

Stock is never stored. It is computed from the events.
    * stock = (in + stocktake events) - (out events)
"""

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import Event


def get_stock(db: Session, product_id: int) -> int:
    """Return how many packages of a product are in the fridge

    Count every scan for the product in/out
    Undone events (reverted) are skipped and coalesce turn NULL into 0
    """

    change = case((Event.type == "out", -1), else_=1)
    stmt = select(func.coalesce(func.sum(change), 0)).where(
        Event.product_id == product_id,
        Event.reverted_at.is_(None),
    )
    return db.scalar(stmt)
