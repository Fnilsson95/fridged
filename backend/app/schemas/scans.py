"""Request and response shapes for POST /api/scans"""


from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field, field_validator

from app.barcodes import normalize_barcode
from app.schemas.products import ProductSummary
from app.services.scans import ScanMode, ScanResult


class ScanRequest(BaseModel):
    """One scan, as sent by the device"""

    barcode: str = Field(min_length=1, max_length=64, examples=[7310865004703])
    mode: ScanMode
    # The devices unique ID for this scan. A retry sends the same ID
    client_event_id: UUID
    # When the item was scanned. Must include TZ
    # Example: "2026-11-06T18:00:00+01:00" or "2026-11-06T17:00:00Z"
    occurred_at: AwareDatetime

    @field_validator("barcode")
    @classmethod
    def _normalize_barcode(cls, value: str) -> str:
        """Normalize the bardoe. A ValueError here becomes a 422 response."""
        return normalize_barcode(value)


class ScanReponse(BaseModel):
    """What happened to the scan - Every result should be normal 200"""

    result: ScanResult
    # The recorded event. Can undo later and None when
    # nothing was recorded (not_in_stock)
    event_id: int | None
    # The products stock after the scan
    stock: int
    product: ProductSummary