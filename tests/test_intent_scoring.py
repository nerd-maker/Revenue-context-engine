import pytest
import math
from datetime import datetime, timedelta
from app.services.context_engine import compute_intent_score, SIGNAL_TYPE_WEIGHTS, LAMBDA

class DummySignal:
    def __init__(self, type, timestamp):
        self.type = type
        self.timestamp = timestamp

@pytest.mark.asyncio
async def test_intent_scoring_decay():
    now = datetime.utcnow()
    signals = [
        DummySignal("job_posting", now - timedelta(hours=1)),
        DummySignal("crm_stage_change", now - timedelta(hours=2)),
        DummySignal("web_visit", now - timedelta(hours=3)),
    ]
    score = await compute_intent_score(signals)
    expected = (
        SIGNAL_TYPE_WEIGHTS["job_posting"] * math.exp(-LAMBDA * 1) * 100 +
        SIGNAL_TYPE_WEIGHTS["crm_stage_change"] * math.exp(-LAMBDA * 2) * 100 +
        SIGNAL_TYPE_WEIGHTS["web_visit"] * math.exp(-LAMBDA * 3) * 100
    )
    assert abs(score - expected) < 1e-3
