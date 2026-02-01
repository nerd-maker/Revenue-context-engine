import pytest
import uuid
import asyncio
from app.core.distributed_lock import with_account_lock
import aioredlock

@pytest.mark.asyncio
async def test_distributed_lock_prevents_concurrent_updates():
    account_id = str(uuid.uuid4())
    results = []
    async def worker(worker_id: int):
        try:
            async with with_account_lock(account_id, timeout=5):
                results.append(f"worker_{worker_id}_start")
                await asyncio.sleep(1)
                results.append(f"worker_{worker_id}_end")
        except aioredlock.LockError:
            results.append(f"worker_{worker_id}_blocked")
    await asyncio.gather(
        worker(1),
        worker(2),
        worker(3)
    )
    completed = [r for r in results if 'end' in r]
    blocked = [r for r in results if 'blocked' in r]
    assert len(completed) == 1, "Only one worker should complete"
    assert len(blocked) == 2, "Two workers should be blocked"
