import pytest
import uuid
import asyncio
from app.core.dlq import send_to_dlq

@pytest.mark.asyncio
async def test_send_to_dlq(monkeypatch):
    sent = {}
    async def fake_send_and_wait(topic, value):
        sent['topic'] = topic
        sent['value'] = value
    class FakeProducer:
        async def send_and_wait(self, topic, value):
            await fake_send_and_wait(topic, value)
    monkeypatch.setattr('app.core.kafka.kafka_manager.get_producer', lambda: FakeProducer())
    await send_to_dlq('signals.raw', {'foo': 'bar'}, 'test-error', retry_count=1)
    assert sent['topic'] == 'signals.raw.dlq'
    assert b'test-error' in sent['value']
