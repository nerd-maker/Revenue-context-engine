import aioredis
from app.core.config import settings
import logging
from typing import Optional

logger = logging.getLogger("redis_cache")

class RedisCache:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
    async def connect(self):
        if self.redis is None:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Connected to Redis")
    async def close(self):
        if self.redis:
            await self.redis.close()
    async def get_intent_score(self, account_id: str) -> Optional[float]:
        key = f"intent_score:{account_id}"
        cached = await self.redis.get(key)
        return float(cached) if cached else None
    async def set_intent_score(self, account_id: str, score: float, ttl: int = 300):
        key = f"intent_score:{account_id}"
        await self.redis.setex(key, ttl, score)
    async def invalidate_intent_score(self, account_id: str):
        key = f"intent_score:{account_id}"
        await self.redis.delete(key)
    async def acquire_lock(self, lock_key: str, timeout: int = 60) -> bool:
        return await self.redis.set(lock_key, "locked", ex=timeout, nx=True)
    async def release_lock(self, lock_key: str):
        await self.redis.delete(lock_key)

redis_cache = RedisCache()

async def startup_redis():
    await redis_cache.connect()

async def shutdown_redis():
    await redis_cache.close()
