"""Product endpoints: list, get, edit and delete"""

from typing import Annotated, Literal

from fastapi import APIRouter, Query, Response, status

from app.db import DbSession
from app.schemas.products import ProductSummary, ProductUpdate, ProductWithStock
from app.services import products as product_service

router = APIRouter(prefix="/api", tags=["products"])


def _to_schema(row: product_service.ProductRow) -> ProductWithStock:
    """Combine the products own fields with its computed numbers"""

    return ProductWithStock(
        **ProductSummary.model_validate(row.product).model_dump(),
        stock=row.stock,
        value_ore=row.value_ore,
        scan_count=row.scan_count,
        last_scanned_at=row.last_scanned_at,
        created_at=row.product.created_at,
        updated_at=row.product.updated_at,
    )


@router.get("/products")
def list_products(
    db: DbSession,
    status: Literal["unknown", "known"] | None = None,
    search: Annotated[str | None, Query(max_length=100)] = None,
    in_stock: bool | None = None,
) -> list[ProductWithStock]:
    """List products with their stock. All filters are optional"""
    rows = product_service.list_products(db, status=status, search=search, in_stock=in_stock)
    return [_to_schema(row) for row in rows]


@router.get("/products/{product_id}")
def get_product(product_id: int, db: DbSession) -> ProductWithStock:
    """Get one product with its stock"""
    return _to_schema(product_service.get_product(db, product_id))


@router.patch("/products/{product_id}")
def update_product(product_id: int, changes: ProductUpdate, db: DbSession) -> ProductWithStock:
    """Edit a product. For an unkown product, send name, brand and price to register it"""
    row = product_service.update_product(db, product_id, changes.model_dump(exclude_unset=True))
    return _to_schema(row)


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: DbSession) -> Response:
    """Delete a product that has no scans (added by mistake)"""
    product_service.delete_product(db, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
