import pytest
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

def test_create_experiment():
    resp = client.post("/api/laboratory/experiments", json={
        "name": "Test new intent scoring weights",
        "description": "A/B test new weights",
        "agent_config": {"signal_weights": {"job_posting": 0.9, "web_visit": 0.4}, "decay_lambda": 0.15},
        "signal_filters": {}
    })
    assert resp.status_code == 200
    assert "experiment_id" in resp.json()

def test_run_compare_promote_experiment():
    # Create experiment
    resp = client.post("/api/laboratory/experiments", json={
        "name": "Test run",
        "description": "Replay signals",
        "agent_config": {"signal_weights": {"job_posting": 0.9}, "decay_lambda": 0.15},
        "signal_filters": {}
    })
    eid = resp.json()["experiment_id"]
    # Run
    resp = client.post(f"/api/laboratory/experiments/{eid}/run")
    assert resp.status_code == 200
    # Compare
    resp = client.get(f"/api/laboratory/experiments/{eid}/compare")
    assert resp.status_code == 200
    # Promote
    resp = client.post(f"/api/laboratory/experiments/{eid}/promote")
    assert resp.status_code == 200
