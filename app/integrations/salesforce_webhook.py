try:
    from fastapi import APIRouter, Request, status, HTTPException
except ImportError:
    APIRouter = Request = status = HTTPException = None
from app.models.core import Signal
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import hashlib
import uuid
import logging
from sqlalchemy import text
try:
    from aiokafka import AIOKafkaProducer
except ImportError:
    AIOKafkaProducer = None
import json
import hmac
import base64

router = APIRouter()
logger = logging.getLogger("signal_ingestion")

DATABASE_URL = settings.DATABASE_URL.replace('postgresql+psycopg2', 'postgresql+asyncpg')
engine = create_async_engine(DATABASE_URL, echo=True, future=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

KAFKA_TOPIC = "signals.raw"
KAFKA_BOOTSTRAP_SERVERS = settings.KAFKA_BOOTSTRAP_SERVERS

async def get_kafka_producer():
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    return producer

async def normalize_salesforce_opportunity(payload: dict) -> dict:
    # Example normalization logic
    return {
        "account_id": payload.get("AccountId"),
        "source": "salesforce",
        "type": "crm_stage_change",
        "payload": payload,
        "confidence_score": 0.7,
        "timestamp": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "consent_id": None,
    }

def signal_hash(signal: dict) -> str:
    # Hash relevant fields for idempotency
    key = f"{signal['account_id']}-{signal['type']}-{signal['payload'].get('Id', '')}-{signal['timestamp']}"
    return hashlib.sha256(key.encode()).hexdigest()

@router.post("/integrations/salesforce/webhook", status_code=status.HTTP_202_ACCEPTED)
async def salesforce_webhook(request: Request):
    org_id = request.headers.get('Salesforce-Org-Id')
    signature = request.headers.get('X-Salesforce-Signature')
    if not org_id or not signature:
        raise HTTPException(status_code=400, detail='Missing org_id or signature')
    body = await request.body()
    session: AsyncSession = request.state.db
    # Use parameterized query to prevent SQL injection
    result = await session.execute(
        text("SELECT * FROM integrations WHERE org_id = :org_id"), 
        {"org_id": org_id}
    )
    integration = result.first()
    if not integration:
        raise HTTPException(status_code=403, detail='Unknown Salesforce org')
    key = integration[0].refresh_token.encode()
    expected_sig = base64.b64encode(hmac.new(key, body, hashlib.sha256).digest()).decode()
    if not hmac.compare_digest(signature, expected_sig):
        raise HTTPException(status_code=403, detail='Invalid signature')
    payload = await request.json()
    logger.info(f"Received Salesforce webhook: {payload}")
    normalized = await normalize_salesforce_opportunity(payload)
    sig_hash = signal_hash(normalized)
    async with AsyncSessionLocal() as session:
        # Check for duplicate signal using parameterized query
        # Parameterized queries prevent SQL injection by properly escaping user input
        existing = await session.execute(
            text("SELECT id FROM signals WHERE id = :id"), 
            {"id": sig_hash}
        )
        if existing.scalar():
            logger.info(f"Duplicate signal detected: {sig_hash}")
            return {"status": "duplicate", "signal_id": sig_hash}
        # Store signal
        signal_obj = Signal(
            id=sig_hash,
            account_id=normalized["account_id"],
            source=normalized["source"],
            type=normalized["type"],
            payload=normalized["payload"],
            confidence_score=normalized["confidence_score"],
            timestamp=datetime.fromisoformat(normalized["timestamp"]),
            expires_at=datetime.fromisoformat(normalized["expires_at"]),
            consent_id=None,
            audit_id=None,
        )
        session.add(signal_obj)
        await session.commit()
        logger.info(f"Signal stored: {sig_hash}")
    # Publish to Kafka
    producer = await get_kafka_producer()
    await producer.send_and_wait(KAFKA_TOPIC, json.dumps(normalized).encode())
    await producer.stop()
    logger.info(f"Signal published to Kafka: {sig_hash}")
    return {"status": "queued", "signal_id": sig_hash}
