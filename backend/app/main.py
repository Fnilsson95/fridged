"""
FastAPI application entry point

Creates the "app" object that uvicorn runs and registers the routes.

"uvicorn app.main:app" and the tests "TestClient(app)"

"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import ConflictError, DomainError, InvalidRequestError, NotFoundError
from app.routers import health, products, scans

# Application - title appears at the top of docs and openapi.json
app = FastAPI(title="fridged")

app.include_router(health.router)
app.include_router(scans.router)
app.include_router(products.router)

def handle_domain_error(_request: Request, exc: DomainError) -> JSONResponse:
    """Turn an error raised by a service into an HTTP response
    
    FastAPI calls this for DomainError and every subclass of it. 
    Body is same shape as FastAPIs own errors
    """


    if isinstance(exc, NotFoundError):
        status_code = 404
    elif isinstance(exc, ConflictError):
        status_code = 409
    elif isinstance(exc, InvalidRequestError):
        status_code = 422
    else:
        status_code = 400
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})
