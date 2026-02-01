import pytest
from app.integrations.salesforce_webhook import signal_hash

def test_signal_hash_idempotency():
    signal1 = {
        "account_id": "A1",
        "type": "crm_stage_change",
        "payload": {"Id": "O1"},
        "timestamp": "2026-01-28T12:00:00"
    }
    signal2 = {
        "account_id": "A1",
        "type": "crm_stage_change",
        "payload": {"Id": "O1"},
        "timestamp": "2026-01-28T12:00:00"
    }
    assert signal_hash(signal1) == signal_hash(signal2)
