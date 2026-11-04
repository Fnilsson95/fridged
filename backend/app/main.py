"""
FastAPI application entry point

Creates the "app" object that uvicorn runs and registers the routes.

"uvicorn app.main:app" and the tests "TestClient(app)"

"""

from fastapi import FastAPI

# Application - title appears at the top of docs and openapi.json
app = FastAPI(title="fridged")


@app.get("/api/health")
def health() -> dict[str, str]:
    """Used to check that the backend is running"""
    return {"status": "ok"}
