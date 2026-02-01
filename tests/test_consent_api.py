import pytest
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

def test_consent_crud():
    email = "test@example.com"
    # Grant consent
    resp = client.post("/api/consent", json={"email": email, "consent_type": "marketing"})
    assert resp.status_code == 200
    # Check consent
    resp = client.get(f"/api/consent/{email}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "granted"
    # Revoke consent
    resp = client.delete(f"/api/consent/{email}")
    assert resp.status_code == 200
    # Check consent again
    resp = client.get(f"/api/consent/{email}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "revoked"
