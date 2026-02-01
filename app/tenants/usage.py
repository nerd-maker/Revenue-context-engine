try:
    from fastapi import APIRouter, Request
except ImportError:
    APIRouter = Request = None
import aioredis
from app.core.config import settings
import time

router = APIRouter()
REDIS_URL = settings.REDIS_URL
redis = aioredis.from_url(REDIS_URL)

@router.get('/tenants/{tenant_id}/usage')
async def get_usage(tenant_id: str):
    today = time.strftime('%Y-%m-%d')
    signals = await redis.get(f"ratelimit:{tenant_id}:signals_per_day:{today}") or 0
    actions = await redis.get(f"ratelimit:{tenant_id}:actions_per_day:{today}") or 0
    return {
        "tenant_id": tenant_id,
        "signals_today": int(signals),
        "actions_today": int(actions)
    }
