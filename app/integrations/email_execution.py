import asyncio
import logging
try:
    from aiokafka import AIOKafkaConsumer
except ImportError:
    AIOKafkaConsumer = None
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.models.core import AuditLog, Signal
from datetime import datetime
import json
import uuid
from sqlalchemy import text

DATABASE_URL = settings.DATABASE_URL.replace('postgresql+psycopg2', 'postgresql+asyncpg')
engine = create_async_engine(DATABASE_URL, echo=True, future=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

KAFKA_BOOTSTRAP_SERVERS = settings.KAFKA_BOOTSTRAP_SERVERS
ACTIONS_APPROVED_TOPIC = "actions.approved"

logger = logging.getLogger("email_execution")

RATE_LIMIT = 10  # req/sec
RETRIES = 3

async def mock_outreach_api(prospect_id, subject, body, from_user, sequence_id):
    # Simulate API call and rate limiting
    await asyncio.sleep(0.1)
    return {"status": "sent", "email_id": str(uuid.uuid4())}

async def update_action_executed(session, action_id):
    # Use parameterized query to prevent SQL injection
    # SQLAlchemy text() with parameter binding ensures user input is properly escaped
    result = await session.execute(
        text("SELECT * FROM audit_logs WHERE id = :id"), 
        {"id": action_id}
    )
    action = result.first()
    if not action:
        logger.error(f"Action not found: {action_id}")
        return
    action = action[0]
    action.compliance_tag = "executed"
    action.payload["executed_at"] = datetime.utcnow().isoformat()
    await session.commit()
    logger.info(f"Action executed: {action_id}")

async def create_email_sent_signal(session, account_id):
    signal_id = str(uuid.uuid4())
    signal = Signal(
        id=signal_id,
        account_id=account_id,
        source="orchestration_engine",
        type="email_sent",
        payload={"desc": "Email sent via Outreach API"},
        confidence_score=1.0,
        timestamp=datetime.utcnow(),
        expires_at=datetime.utcnow(),
        consent_id=None,
        audit_id=None,
    )
    session.add(signal)
    await session.commit()
    logger.info(f"Signal created: email_sent for {account_id}")

async def email_execution_worker():
    consumer = AIOKafkaConsumer(
        ACTIONS_APPROVED_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="email_execution_group",
        value_deserializer=lambda m: json.loads(m.decode()),
        auto_offset_reset="earliest",
    )
    await consumer.start()
    try:
        async for msg in consumer:
            action = msg.value
            if action.get("action") != "send_email":
                continue
            account_id = action["account_id"]
            payload = action.get("payload", {})
            subject = payload.get("email", {}).get("subject", "")
            body = payload.get("email", {}).get("body", "")
            from_user = "noreply@company.com"
            sequence_id = "seq-001"
            # Rate limit and retry logic
            for attempt in range(RETRIES):
                try:
                    await asyncio.sleep(1.0 / RATE_LIMIT)
                    result = await mock_outreach_api(account_id, subject, body, from_user, sequence_id)
                    if result["status"] == "sent":
                        async with AsyncSessionLocal() as session:
                            await update_action_executed(session, action["id"])
                            await create_email_sent_signal(session, account_id)
                        break
                except Exception as e:
                    logger.error(f"Email send failed (attempt {attempt+1}): {e}")
                    await asyncio.sleep(2 ** attempt)
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(email_execution_worker())
