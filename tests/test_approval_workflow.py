import pytest
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

def test_approval_queue_endpoints():
    # List pending actions (should be empty for fresh DB)
    resp = client.get("/api/actions/pending")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    # Approve/reject endpoints (simulate not found)
    resp = client.post("/api/actions/nonexistent/approve")
    assert resp.status_code == 404
    resp = client.post("/api/actions/nonexistent/reject", json={"reason": "Not valid"})
    assert resp.status_code == 404
