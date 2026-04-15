from typing import Any

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root() -> Any:
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()

def test_health() -> Any:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
