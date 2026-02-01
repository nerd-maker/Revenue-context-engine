import pytest
import uuid
from datetime import datetime
import asyncio

@pytest.mark.asyncio
async def test_duplicate_signal_detection(client):
    """Verify duplicate signals are rejected"""
    signal_data = {
        "account_id": str(uuid.uuid4()),
        "source": "salesforce",
        "type": "crm_stage_change",
        "payload": {"id": "opp-123", "stage": "Demo"},
        "confidence_score": 1.0,
        "timestamp": datetime.utcnow().isoformat()
    }

    # First request: Success
    response1 = await client.post("/api/signals", json=signal_data)
    assert response1.status_code == 202
    signal_id_1 = response1.json()["signal_id"]

    # Second request: Duplicate detected
    response2 = await client.post("/api/signals", json=signal_data)
    assert response2.status_code == 202
    assert response2.json()["status"] == "duplicate"
    assert response2.json()["signal_id"] == signal_id_1

@pytest.mark.asyncio
async def test_concurrent_signal_ingestion(client):
    """Verify race condition handling"""
    signal_data = {
        "account_id": str(uuid.uuid4()),
        "source": "salesforce",
        "type": "crm_stage_change",
        "payload": {"id": "opp-456", "stage": "Demo"},
        "confidence_score": 1.0,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Send 10 identical requests concurrently
    tasks = [client.post("/api/signals", json=signal_data) for _ in range(10)]
    responses = await asyncio.gather(*tasks)

    # Verify only 1 succeeded, rest are duplicates
    success_count = sum(1 for r in responses if r.json()["status"] == "queued")
    duplicate_count = sum(1 for r in responses if r.json()["status"] == "duplicate")

    assert success_count == 1
    assert duplicate_count == 9
