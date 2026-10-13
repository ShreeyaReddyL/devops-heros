"""Shared pytest fixtures for the CampusFix backend test suite.

Database isolation strategy
---------------------------
``app.db`` builds its SQLAlchemy engine at *import time* from
``settings.database_url``. The test database therefore has to be selected before
any application module is imported, which is why ``DATABASE_URL`` is set at the
very top of this file, above the ``app.*`` imports.

Tests run against a temporary SQLite file (never the PostgreSQL database used by
the application). The file is deleted on import and again at the end of the
session, and the ``tickets`` table is emptied before every test, so results do
not depend on execution order or on stale data left by a previous run.
"""

import os
import tempfile
from pathlib import Path
from typing import Iterator

import pytest

# --- Must happen before `app.*` is imported anywhere ------------------------
TEST_DB_PATH = Path(tempfile.gettempdir()) / "campusfix_pytest.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
# ---------------------------------------------------------------------------

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import delete  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Ticket  # noqa: E402


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    """A TestClient bound to the isolated SQLite database."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(autouse=True)
def clean_tickets(client: TestClient) -> Iterator[None]:
    """Give every test an empty `tickets` table, so tests are order-independent."""
    with engine.begin() as conn:
        conn.execute(delete(Ticket))
    yield


@pytest.fixture
def wifi_ticket_payload() -> dict[str, str]:
    """A realistic campus Wi-Fi ticket payload."""
    return {
        "title": "Hostel Block C Wi-Fi keeps dropping",
        "description": "Students on the 3rd floor lose association every few minutes.",
        "category": "WI_FI",
        "building": "Hostel Block C",
        "reporter": "Aarav Sharma",
        "priority": "HIGH",
    }