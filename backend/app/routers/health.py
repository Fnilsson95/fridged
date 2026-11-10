"""Health check endpoint

GET /api/health

"""

from fastapi import APIRouter


# every path in this router starts with /api
# tag groups the endpoints under specific heading
router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health")
def health() -> dict[str, str]:
    """Report that the backend is running"""
    return {"status": "ok"}

