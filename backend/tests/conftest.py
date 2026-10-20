"""Shared fixtures for the TriPlan backend test suite.

The tests run against the app in-process, so no server needs to be running.

Every test writes to a throwaway database file, so running the suite never
fills the real `data/trips.db` with test trips. The path is set through the
TRIP_DB_PATH environment variable, which `app/database.py` reads at import
time, so it has to be set before the app is imported.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Make sure the backend package is importable when pytest is run from anywhere.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Point the app at a temporary database before anything imports app.database.
# The handle is kept open so the file is not removed while the tests run.
_TMP_DIR = tempfile.TemporaryDirectory(prefix="triplan-tests-")
_TEST_DB = Path(_TMP_DIR.name) / "test-trips.db"
os.environ["TRIP_DB_PATH"] = str(_TEST_DB)


@pytest.fixture(scope="session", autouse=True)
def _clean_test_database():
    """Give the test suite a fresh database and remove it afterwards."""
    yield
    _TMP_DIR.cleanup()


@pytest.fixture(scope="session")
def app():
    """The FastAPI application under test."""
    from app.main import app as fastapi_app

    return fastapi_app


@pytest.fixture(scope="session")
def client(app):
    """A test client bound to the application.

    `raise_server_exceptions` stays on so an unexpected crash surfaces as a
    real error instead of being swallowed by the global error handler.
    """
    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def trip_payload():
    """A valid trip request body."""
    return {
        "origin": "Mumbai",
        "destination": "Paris",
        "days": 3,
        "budget": 20000,
        "people": 2,
        "travel_date": "2026-12-01",
        "interests": ["culture", "food"],
        "diet": "none",
    }


@pytest.fixture
def created_trip(client, trip_payload):
    """A trip that has been created, so its id can be used for lookups."""
    response = client.post("/api/trips", json=trip_payload)
    assert response.status_code == 200, response.text
    return response.json()
