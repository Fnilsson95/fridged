"""Product shapes used in API responses"""

from typing import Literal, Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Url = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]


class ProductSummary(BaseModel):
    """The product fields the devide and the website need"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    barcode: str
    status: Literal["unknown", "known"]
    name: str | None
    brand: str | None
    size_label: str | None
    image_url: str | None
    current_price_ore: int | None


class ProductWithStock(ProductSummary):
    """A product plus the numbers computed from the events"""

    # Packages in the fridge right now
    stock: int
    # stock x current price
    value_ore: int | None
    # Scans that count
    scan_count: int
    # Time of latest scan // Time it was created/updated
    last_scanned_at: str | None
    created_at: str
    updated_at: str


class ProductUpdate(BaseModel):
    """Fields that can be changed with PATCH. Send only what we need"""

    model_config = ConfigDict(extra="forbid")

    # Default set to none --> Not sending any value
    name: Text | None = None
    brand: Text | None = None
    size_label: Text | None = None
    image_url: Url | None = None
    current_price_ore: Annotated[int, Field(ge=0)] | None = None
