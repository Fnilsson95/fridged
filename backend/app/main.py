"""
FastAPI application entry point

Creates the "app" object that uvicorn runs and registers the routes.

"uvicorn app.main:app" and the tests "TestClient(app)"

"""

from fastapi import FastAPI

from app.routers import health, scans

# Application - title appears at the top of docs and openapi.json
app = FastAPI(title="fridged")

app.include_router(health.router)
app.include_router(scans.router)


