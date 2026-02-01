import asyncio
import logging
import random
from app.core.config import settings
from app.integrations.circuit_breaker import call_clearbit_api, CircuitBreakerError
try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
except ImportError:
    AsyncSession = create_async_engine = sessionmaker = None
from app.models.core import Signal, AuditLog
from datetime import datetime
import uuid
try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None
try:
    import httpx
except ImportError:
    httpx = None


if create_async_engine and sessionmaker and AsyncSession:
    DATABASE_URL = settings.DATABASE_URL.replace('postgresql+psycopg2', 'postgresql+asyncpg')
    engine = create_async_engine(DATABASE_URL, echo=True, future=True)
    AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
else:
    engine = AsyncSessionLocal = None

REDIS_URL = settings.REDIS_URL
redis_client = aioredis.from_url(REDIS_URL)

logger = logging.getLogger("context_enrichment_agent")

ENRICHMENT_BUDGET = float(settings.ENRICHMENT_BUDGET_PER_ACCOUNT)
BUDGET_PERIOD = settings.ENRICHMENT_BUDGET_PERIOD
CLEARBIT_API_KEY = settings.CLEARBIT_API_KEY

async def get_enrichment_spend(account_id, month):
    key = f"enrichment:spend:{account_id}:{month}"
    val = await redis_client.get(key)
    return float(val or 0)

async def increment_enrichment_spend(account_id, month, amount):
    key = f"enrichment:spend:{account_id}:{month}"
    await redis_client.incrbyfloat(key, amount)

async def call_clearbit(domain):
    # Use circuit breaker for real API call
    try:
        enrichment = await call_clearbit_api(
            url="https://company.clearbit.com/v2/companies/find",
            params={"domain": domain}
        )
        return enrichment
    except CircuitBreakerError:
        logger.error("Clearbit API circuit breaker OPEN")
        raise
    except Exception as e:
        logger.error(f"Clearbit API error: {e}")
        raise

async def context_enrichment_worker():
    # This would subscribe to context.updated or be triggered by API
    # For demo, just run once for a test account
    account_id = "test-account-001"
    month = datetime.utcnow().strftime("%Y-%m")
    spend = await get_enrichment_spend(account_id, month)
    if spend >= ENRICHMENT_BUDGET:
        logger.warning(f"Budget exceeded for {account_id}")
        return
    try:
        enrichment = await call_clearbit("test.com")
    except CircuitBreakerError:
        logger.error("Clearbit circuit breaker is OPEN. Skipping enrichment.")
        return
    except Exception as e:
        logger.error(f"Enrichment API failed: {e}")
        return
    if enrichment["confidence_score"] < 0.7 or enrichment["data_completeness"] < 60:
        logger.info(f"Enrichment data not valid for {account_id}")
        return
    async with AsyncSessionLocal() as session:
        # Create signals for enrichment
        signal1 = Signal(
            id=str(uuid.uuid4()),
            account_id=account_id,
            source="enrichment_agent",
            type="tech_stack_detected",
            payload={"technologies": enrichment["tech_stack"]},
            confidence_score=0.8,
            timestamp=datetime.utcnow(),
            expires_at=datetime.utcnow(),
            consent_id=None,
            audit_id=None,
        )
        signal2 = Signal(
            id=str(uuid.uuid4()),
            account_id=account_id,
            source="enrichment_agent",
            type="firmographic_update",
            payload={"employee_count": enrichment["employee_count"]},
            confidence_score=0.9,
            timestamp=datetime.utcnow(),
            expires_at=datetime.utcnow(),
            consent_id=None,
            audit_id=None,
        )
        session.add(signal1)
        session.add(signal2)
        # Log audit event
        audit = AuditLog(
            id=str(uuid.uuid4()),
            event_type="enrichment_call",
            actor_id="context_enrichment_agent",
            payload={"account_id": account_id, "cost": 0.25, "enrichment": enrichment},
            created_at=datetime.utcnow(),
            compliance_tag="lab" if settings.EXECUTION_MODE == "laboratory" else "prod"
        )
        session.add(audit)
        await session.commit()
    await increment_enrichment_spend(account_id, month, 0.25)
    logger.info(f"Enrichment signals created for {account_id}")

if __name__ == "__main__":
    asyncio.run(context_enrichment_worker())
