"""CampusFix API test suite.

Covers meta endpoints (/, /health, /ready, /metrics), full ticket CRUD,
input validation, 404 handling, the status-workflow rules and statistics.

Every test runs against the temporary SQLite database configured in
``conftest.py``; the PostgreSQL database is never touched.
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient


# --------------------------------------------------------------------------- #
# Meta endpoints
# --------------------------------------------------------------------------- #


def test_health_returns_up(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"


def test_root_reports_service_name(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "CampusFix API"


def test_ready_queries_database(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "READY"}


def test_metrics_endpoint_exposes_prometheus_output(client: TestClient) -> None:
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_request" in response.text or "http_requests_total" in response.text


# --------------------------------------------------------------------------- #
# Create
# --------------------------------------------------------------------------- #


def test_create_ticket_applies_workflow_defaults(client: TestClient, wifi_ticket_payload: dict[str, str]) -> None:
    response = client.post("/api/tickets", json=wifi_ticket_payload)
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == wifi_ticket_payload["title"]
    assert data["status"] == "OPEN"
    assert data["priority"] == "HIGH"
    assert data["category"] == "WI_FI"
    assert data["building"] == "Hostel Block C"
    assert data["reporter"] == "Aarav Sharma"
    assert isinstance(data["id"], int)
    assert data["created_at"]


def test_create_ticket_defaults_when_optional_fields_omitted(client: TestClient) -> None:
    response = client.post("/api/tickets", json={"title": "Corridor light flickering near lifts"})
    assert response.status_code == 201

    data = response.json()
    assert data["status"] == "OPEN"
    assert data["priority"] == "MEDIUM"
    assert data["category"] == "IT_SUPPORT"
    assert data["description"] == ""


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"title": ""}, id="blank-title"),
        pytest.param({"title": "   "}, id="whitespace-title"),
        pytest.param({"title": "ab"}, id="title-too-short"),
        pytest.param({"title": "Valid title", "category": "NOT_A_CATEGORY"}, id="bad-category"),
        pytest.param({"title": "Valid title", "priority": "URGENT"}, id="bad-priority"),
        pytest.param({"title": "Valid title", "status": "CLOSED"}, id="bad-status"),
    ],
)
def test_create_ticket_rejects_invalid_payload(client: TestClient, payload: dict[str, Any]) -> None:
    response = client.post("/api/tickets", json=payload)
    assert response.status_code == 422


# --------------------------------------------------------------------------- #
# List / filter
# --------------------------------------------------------------------------- #


def test_list_tickets_is_empty_on_clean_database(client: TestClient) -> None:
    response = client.get("/api/tickets")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tickets_filters_by_status(client: TestClient, wifi_ticket_payload: dict[str, str]) -> None:
    client.post("/api/tickets", json=wifi_ticket_payload)
    other = client.post(
        "/api/tickets",
        json={
            "title": "Lab 3 oscilloscope not powering on",
            "category": "LAB_EQUIPMENT",
            "building": "Engineering Block",
            "reporter": "Priya Nair",
        },
    ).json()
    client.put(f"/api/tickets/{other['id']}", json={"status": "IN_PROGRESS"})

    open_only = client.get("/api/tickets", params={"status": "OPEN"}).json()
    assert len(open_only) == 1
    assert open_only[0]["status"] == "OPEN"

    in_progress = client.get("/api/tickets", params={"status": "IN_PROGRESS"}).json()
    assert len(in_progress) == 1
    assert in_progress[0]["id"] == other["id"]


def test_list_tickets_filters_by_category(client: TestClient) -> None:
    client.post("/api/tickets", json={"title": "Wi-Fi dead zone near library", "category": "WI_FI"})
    client.post("/api/tickets", json={"title": "Broken tap in washroom", "category": "PLUMBING"})

    result = client.get("/api/tickets", params={"category": "PLUMBING"}).json()
    assert len(result) == 1
    assert result[0]["category"] == "PLUMBING"


# --------------------------------------------------------------------------- #
# Read
# --------------------------------------------------------------------------- #


def test_get_ticket_by_id(client: TestClient, wifi_ticket_payload: dict[str, str]) -> None:
    created = client.post("/api/tickets", json=wifi_ticket_payload).json()

    response = client.get(f"/api/tickets/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["title"] == wifi_ticket_payload["title"]


def test_get_ticket_missing_returns_404(client: TestClient) -> None:
    response = client.get("/api/tickets/424242")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# --------------------------------------------------------------------------- #
# Update / workflow
# --------------------------------------------------------------------------- #


def test_update_ticket_advances_workflow(client: TestClient, wifi_ticket_payload: dict[str, str]) -> None:
    created = client.post("/api/tickets", json=wifi_ticket_payload).json()

    response = client.put(f"/api/tickets/{created['id']}", json={"status": "IN_PROGRESS"})
    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"

    resolved = client.put(f"/api/tickets/{created['id']}", json={"status": "RESOLVED"})
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "RESOLVED"


def test_update_ticket_rejects_illegal_transition(client: TestClient, wifi_ticket_payload: dict[str, str]) -> None:
    created = client.post("/api/tickets", json=wifi_ticket_payload).json()
    client.put(f"/api/tickets/{created['id']}", json={"status": "RESOLVED"})

    response = client.put(f"/api/tickets/{created['id']}", json={"status": "IN_PROGRESS"})
    assert response.status_code == 409
    assert "Illegal status transition" in response.json()["detail"]


def test_update_ticket_can_change_priority(client: TestClient, wifi_ticket_payload: dict[str, str]) -> None:
    created = client.post("/api/tickets", json=wifi_ticket_payload).json()

    response = client.put(f"/api/tickets/{created['id']}", json={"priority": "CRITICAL"})
    assert response.status_code == 200
    assert response.json()["priority"] == "CRITICAL"


def test_update_ticket_rejects_empty_payload(client: TestClient, wifi_ticket_payload: dict[str, str]) -> None:
    created = client.post("/api/tickets", json=wifi_ticket_payload).json()

    response = client.put(f"/api/tickets/{created['id']}", json={})
    assert response.status_code == 422


def test_update_missing_ticket_returns_404(client: TestClient) -> None:
    response = client.put("/api/tickets/999999", json={"priority": "LOW"})
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# Delete
# --------------------------------------------------------------------------- #


def test_delete_ticket_removes_it(client: TestClient, wifi_ticket_payload: dict[str, str]) -> None:
    created = client.post("/api/tickets", json=wifi_ticket_payload).json()

    deleted = client.delete(f"/api/tickets/{created['id']}")
    assert deleted.status_code == 204
    assert deleted.content == b""

    assert client.get(f"/api/tickets/{created['id']}").status_code == 404
    assert client.get("/api/tickets").json() == []


def test_delete_missing_ticket_returns_404(client: TestClient) -> None:
    response = client.delete("/api/tickets/123456")
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #


def test_stats_reflect_database_contents(client: TestClient) -> None:
    empty = client.get("/api/tickets/stats").json()
    assert empty["total"] == 0
    assert empty["open"] == 0
    assert empty["in_progress"] == 0
    assert empty["resolved"] == 0
    assert empty["by_category"] == []

    a = client.post("/api/tickets", json={"title": "Projector bulb burnt in LH-2", "category": "PROJECTOR", "priority": "CRITICAL"}).json()
    b = client.post("/api/tickets", json={"title": "Wi-Fi dead zone near library", "category": "WI_FI"}).json()
    c = client.post("/api/tickets", json={"title": "Tap leaking in hostel washroom", "category": "PLUMBING"}).json()
    client.put(f"/api/tickets/{b['id']}", json={"status": "IN_PROGRESS"})
    client.put(f"/api/tickets/{c['id']}", json={"status": "RESOLVED"})

    stats = client.get("/api/tickets/stats").json()
    assert stats["total"] == 3
    assert stats["open"] == 1
    assert stats["in_progress"] == 1
    assert stats["resolved"] == 1
    assert stats["critical"] == 1
    assert {entry["category"] for entry in stats["by_category"]} == {"PROJECTOR", "WI_FI", "PLUMBING"}
    assert stats["by_category"][0]["count"] == 1