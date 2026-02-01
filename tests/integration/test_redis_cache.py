import pytest
import asyncio
from app.core.redis_client import redis_cache

@pytest.mark.asyncio
async def test_redis_intent_score_cache():
    account_id = "test-account-redis"
    await redis_cache.connect()
    await redis_cache.invalidate_intent_score(account_id)
    # Should be None
    assert await redis_cache.get_intent_score(account_id) is None
    # Set and get
    await redis_cache.set_intent_score(account_id, 0.77, ttl=2)
    assert await redis_cache.get_intent_score(account_id) == 0.77
    # Expiry
    await asyncio.sleep(2.1)
    assert await redis_cache.get_intent_score(account_id) is None
    await redis_cache.close()
