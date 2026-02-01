import aioredlock
from app.core.config import settings
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger("distributed_lock")

lock_manager = aioredlock.Aioredlock([settings.REDIS_URL])

@asynccontextmanager
async def with_account_lock(account_id: str, timeout: int = 60):
    lock_key = f"lock:context:{account_id}"
    lock = None
    try:
        lock = await lock_manager.lock(lock_key, lock_timeout=timeout)
        logger.debug(f"Acquired lock for account {account_id}")
        yield
    except aioredlock.LockError as e:
        logger.warning(f"Failed to acquire lock for {account_id}: {e}")
        raise
    finally:
        if lock:
            try:
                await lock_manager.unlock(lock)
                logger.debug(f"Released lock for account {account_id}")
            except Exception as e:
                logger.error(f"Failed to release lock: {e}")

async def close_lock_manager():
    await lock_manager.destroy()
