"""
Shared pytest fixtures
pytest loads this file automatically. A test gets a fixture by naming is as a parameter
I.e. "def test_health(client)"

Fixtures:
    * engine - a fresh SQLite db in a temporary folder, with all tables
    * db - a session on that databate, for tests that use the models directly.
    * client - a "TestClient" whose "get_db" dependency uses that database
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.db import get_db, make_engine
from app.main import app
from app.models import Base


@pytest.fixture
def engine(tmp_path):
    """A fresh, empty SQLite database for each test (in pytest's temp folder).
    Creates an empty DB with all tables and closes it afterwards
    """
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)  # create the tables straight from the models
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine):
    """A database session for tests that talk to the database directly."""
    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        yield session


@pytest.fixture
def client(engine):
    """A test client that calls the API without starting a server,
    using the temporary database instead of the real one."""
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db  # swap the real dependency
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()  # always restore after the test


@pytest.fixture
def scan(client):
    """Return a function that sends one scan to the API, like the device would"""

    def _scan(mode, barcode, *, occurred_at="2026-11-06T18:00:00+01:00"):
        payload = {
            "barcode": barcode,
            "mode": mode,
            "client_event_id": str(uuid64()),
            "occured_at": occurred_at,
        }
        response = client.post("/api/scans", json=payload)
        assert response.status_code == 200, response.text
        return response.json()

    return _scan