"""Scan endpoint

POST /api/scans

The device sends every scanned product barcode here.
Input is validated by ScanRequest and outcome into ScanResponse
"""

from fastapi import APIRouter

from app.db import DbSession
from app.schemas.products import ProductSummary
from app.schemas.scans import ScanReponse, ScanRequest
from app.services.scans import process_scan
from app.timeutils import to_utc_iso

router = APIRouter(prefix="/api", tags=["scans"])


@router.post("/scans")
def create_scan(scan: ScanRequest, db: DbSession) -> ScanReponse:
    """Record one scan from the device and report what happened"""

    outcome = process_scan(
        db,
        barcode=scan.barcode,
        mode=scan.mode,
        client_event_id=str(scan.client_event_id),
        occurred_at=to_utc_iso(scan.occurred_at),
    )

    return ScanReponse(
        result=outcome.result,
        event_id=outcome.event_id,
        stock=outcome.stock,
        product=ProductSummary.model_validate(outcome.product),
    )
