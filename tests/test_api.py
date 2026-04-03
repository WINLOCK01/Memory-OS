import pytest
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_stats():
    response = client.get("/stats")
    assert response.status_code == 200
    assert "total_chunks" in response.json()

def test_ingest_text():
    response = client.post("/ingest/text", json={"content": "Unit testing MemoryOS pipeline", "title": "Test Plan"})
    assert response.status_code == 200
    assert response.json()["chunks_stored"] >= 1
