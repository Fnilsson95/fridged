"""Product shapes used in API responses"""


from typing import Literal

from pydantic import BaseModel, ConfigDict

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