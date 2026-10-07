import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import Base, engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup after test if needed

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "TaskBoard API"

def test_ready():
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "READY"}

def test_create_task():
    payload = {
        "title": "Configure production ingress",
        "description": "Setup SSL certificates and TLS ingress routing",
        "priority": "HIGH",
        "assignee": "Shreeya Reddy"
    }
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["status"] == "TODO"
    assert data["assignee"] == "Shreeya Reddy"
    assert "id" in data

def test_list_tasks():
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_task_by_id():
    # First create
    create_resp = client.post("/api/tasks", json={"title": "Test task for get", "priority": "MEDIUM", "assignee": "Student"})
    task_id = create_resp.json()["id"]

    response = client.get(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["id"] == task_id
    assert response.json()["title"] == "Test task for get"

def test_update_task_status():
    create_resp = client.post("/api/tasks", json={"title": "Task to update", "priority": "LOW", "assignee": "Student"})
    task_id = create_resp.json()["id"]

    update_resp = client.put(f"/api/tasks/{task_id}", json={"status": "IN_PROGRESS"})
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "IN_PROGRESS"

def test_delete_task():
    create_resp = client.post("/api/tasks", json={"title": "Task to delete", "priority": "LOW", "assignee": "Student"})
    task_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/tasks/{task_id}")
    assert delete_resp.status_code == 204

    # Verify 404 after deletion
    get_resp = client.get(f"/api/tasks/{task_id}")
    assert get_resp.status_code == 404

def test_task_stats():
    response = client.get("/api/tasks/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "todo" in data
    assert "inProgress" in data
    assert "done" in data

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests" in response.text or "http_request" in response.text or "python_info" in response.text
