try:
    from fastapi import APIRouter, HTTPException, status
except ImportError:
    APIRouter = HTTPException = status = None
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import uuid


import logging
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.models.core import Signal
from app.core.database import get_db, AsyncSessionLocal
from app.core.kafka import publish_event
import asyncio

logger = logging.getLogger("signal_ingestion")

class SIGNALS_PROCESSED:
    @staticmethod
    def labels(source, type, status):
        class Dummy:
            def inc(self):
                pass
        return Dummy()

class SignalIngestRequest(BaseModel):
    account_id: uuid.UUID
    source: str
    type: str
    payload: dict
    confidence_score: float = Field(..., ge=0, le=1)
    timestamp: datetime
    expires_in_seconds: int = 3600
    consent_id: uuid.UUID | None = None

router = APIRouter()


@router.post('/signals', status_code=status.HTTP_202_ACCEPTED)
async def ingest_signal(
    signal: SignalIngestRequest,
):
    # Generate idempotency key
    external_id = signal.payload.get('id') or signal.payload.get('external_id') or str(uuid.uuid4())
    idempotency_key = f"{signal.source}:{external_id}:{signal.timestamp.isoformat()}"

    async with AsyncSessionLocal() as session:
        # Check for duplicate
        result = await session.execute(
            select(Signal).where(Signal.idempotency_key == idempotency_key)
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(f"Duplicate signal detected: {idempotency_key}")
            SIGNALS_PROCESSED.labels(source=signal.source, type=signal.type, status='duplicate').inc()
            return {
                "status": "duplicate",
                "signal_id": str(existing.id),
                "message": "Signal already processed"
            }

        # Create new signal
        try:
            new_signal = Signal(
                id=uuid.uuid4(),
                idempotency_key=idempotency_key,
                tenant_id=None,  # Set from session.info or middleware if available
                account_id=signal.account_id,
                source=signal.source,
                type=signal.type,
                payload=signal.payload,
                confidence_score=signal.confidence_score,
                timestamp=signal.timestamp,
                expires_at=signal.timestamp + timedelta(seconds=signal.expires_in_seconds),
            )
            session.add(new_signal)
            await session.commit()

            # Publish to Kafka
            await publish_event('signals.raw', {
                'id': str(new_signal.id),
                'idempotency_key': idempotency_key,
                'account_id': str(signal.account_id),
                'source': signal.source,
                'type': signal.type,
                'payload': signal.payload,
                'confidence_score': signal.confidence_score,
                'timestamp': signal.timestamp.isoformat(),
            })

            SIGNALS_PROCESSED.labels(source=signal.source, type=signal.type, status='success').inc()

            return {
                "status": "queued",
                "signal_id": str(new_signal.id)
            }

        except IntegrityError as e:
            # Race condition: Another request created same signal
            await session.rollback()
            logger.warning(f"Race condition on signal creation: {idempotency_key}")
            SIGNALS_PROCESSED.labels(source=signal.source, type=signal.type, status='race_condition').inc()

            # Fetch existing signal
            result = await session.execute(
                select(Signal).where(Signal.idempotency_key == idempotency_key)
            )
            existing = result.scalar_one()
            return {
                "status": "duplicate",
                "signal_id": str(existing.id)
            }
