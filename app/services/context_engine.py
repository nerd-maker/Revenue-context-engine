
import asyncio
import logging
import os
try:
    from aiokafka import AIOKafkaConsumer
except ImportError:
    AIOKafkaConsumer = None
from app.core.config import settings
from app.models.core import AccountContext, Signal
from app.core.database import engine, AsyncSessionLocal
from app.core.kafka import publish_event
from app.core.dlq import send_to_dlq
from app.core.redis_client import redis_cache
from app.core.distributed_lock import with_account_lock
from datetime import datetime
import json
import math
import time

# Metrics imports
from app.monitoring.metrics import (
    INTENT_SCORE_LATENCY,
    CONTEXT_UPDATE_LATENCY,
    SIGNALS_PROCESSED,
    CACHE_HITS,
    CACHE_MISSES,
    INTENT_SCORE_DISTRIBUTION,
    ACTIVE_KAFKA_CONSUMERS,
    track_latency
)

RAW_TOPIC = "signals.raw"
UPDATED_TOPIC = "context.updated"

logger = logging.getLogger("context_engine")

SIGNAL_TYPE_WEIGHTS = {
    "job_posting": 0.8,
    "crm_stage_change": 0.7,
    "web_visit": 0.3,
}
LAMBDA = 0.1

@track_latency(INTENT_SCORE_LATENCY)
async def compute_intent_score(signals):
    now = datetime.utcnow()
    score = 0.0
    for signal in signals:
        t = (now - signal.timestamp).total_seconds() / 3600.0  # hours since signal
        weight = SIGNAL_TYPE_WEIGHTS.get(signal.type, 0.0)
        decay = math.exp(-LAMBDA * t)
        score += weight * decay * 100  # scale to 0-100
    
    final_score = min(score, 100.0)
    
    # Track intent score distribution
    INTENT_SCORE_DISTRIBUTION.observe(final_score)
    
    return final_score

@track_latency(CONTEXT_UPDATE_LATENCY)
async def update_account_context(account_id, session):
    from sqlalchemy import select, update
    from app.models.core import Signal, AccountContext
    
    # Try cache first
    cached_score = await redis_cache.get_intent_score(str(account_id))
    if cached_score is not None:
        CACHE_HITS.inc()
        logger.info(f"Cache HIT for account {account_id}")
        return cached_score
    
    CACHE_MISSES.inc()
    logger.info(f"Cache MISS for account {account_id}")
    
    result = await session.execute(
        select(Signal).where(Signal.account_id == account_id)
    )
    signals = result.scalars().all()
    intent_score = await compute_intent_score(signals)
    
    # Update or create AccountContext
    result = await session.execute(
        select(AccountContext).where(AccountContext.account_id == account_id)
    )
    row = result.scalar_one_or_none()
    if row:
        await session.execute(
            update(AccountContext)
            .where(AccountContext.account_id == account_id)
            .values(intent_score=intent_score, updated_at=datetime.utcnow())
        )
    else:
        context = AccountContext(
            account_id=account_id,
            signals=[s.id for s in signals],
            intent_score=intent_score,
            risk_flags={},
            next_best_action=None,
            updated_at=datetime.utcnow(),
        )
        session.add(context)
    await session.commit()
    
    # Cache the result
    await redis_cache.set_intent_score(str(account_id), intent_score, ttl=300)
    logger.info(f"AccountContext updated for {account_id}: intent_score={intent_score}")
    return intent_score

async def publish_context_updated(account_id, intent_score):
    event = {"account_id": str(account_id), "intent_score": intent_score, "timestamp": datetime.utcnow().isoformat()}
    await publish_event(UPDATED_TOPIC, event)
    logger.info(f"Published context.updated for {account_id}")

async def update_heartbeat(worker_id: str):
    """Update worker heartbeat in Redis"""
    await redis_cache.connect()
    # FIXED: Include worker_id in key to avoid conflicts
    await redis_cache.redis.set(
        f'worker:context_engine:{worker_id}:heartbeat',
        time.time(),
        ex=120  # 2-minute expiration
    )
    logger.debug(f"Worker {worker_id} heartbeat updated")

async def context_engine_worker():
    worker_id = os.getenv('WORKER_ID', 'unknown')
    logger.info(f"Starting context engine worker {worker_id}")
    
    # Graceful shutdown flag
    shutdown_requested = False
    
    def signal_handler(signum, frame):
        nonlocal shutdown_requested
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        shutdown_requested = True
    
    # Register signal handlers
    import signal
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    consumer = None
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries and not shutdown_requested:
        try:
            consumer = AIOKafkaConsumer(
                RAW_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id="context_engine_group",
                value_deserializer=lambda m: json.loads(m.decode()),
                auto_offset_reset="earliest",
                enable_auto_commit=False,  # Manual commit for safety
                max_poll_records=10,  # Batch processing
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
            )
            
            await consumer.start()
            ACTIVE_KAFKA_CONSUMERS.inc()
            logger.info(f"Kafka consumer started successfully")
            retry_count = 0  # Reset on successful connection
            
            # Initial heartbeat
            await update_heartbeat(worker_id)
            
            message_count = 0
            batch_size = 10
            
            try:
                async for msg in consumer:
                    if shutdown_requested:
                        logger.info("Shutdown requested, stopping message processing")
                        break
                    
                    signal = msg.value
                    account_id = signal["account_id"]
                    signal_type = signal.get("type", "unknown")
                    signal_source = signal.get("source", "unknown")
                    
                    try:
                        # Distributed lock
                        async with with_account_lock(account_id, timeout=60):
                            async with AsyncSessionLocal() as session:
                                intent_score = await update_account_context(account_id, session)
                                await publish_context_updated(account_id, intent_score)
                        
                        # Track successful processing
                        SIGNALS_PROCESSED.labels(
                            source=signal_source,
                            type=signal_type,
                            status='success'
                        ).inc()
                        
                        message_count += 1
                        
                        # Batch commit offsets
                        if message_count >= batch_size:
                            await consumer.commit()
                            message_count = 0
                            logger.debug(f"Committed batch of {batch_size} messages")
                        
                        # Update heartbeat every 5 messages
                        if message_count % 5 == 0:
                            await update_heartbeat(worker_id)
                            
                    except Exception as e:
                        logger.exception(f"Failed to process signal: {e}")
                        
                        # Track failed processing
                        SIGNALS_PROCESSED.labels(
                            source=signal_source,
                            type=signal_type,
                            status='failed'
                        ).inc()
                        
                        await send_to_dlq(RAW_TOPIC, msg.value, str(e), retry_count=msg.value.get('retry_count', 0))
                        # Still commit to avoid reprocessing
                        await consumer.commit()
                
                # Commit any remaining messages before shutdown
                if message_count > 0:
                    await consumer.commit()
                    logger.info(f"Committed final batch of {message_count} messages")
                    
            finally:
                if consumer:
                    await consumer.stop()
                    ACTIVE_KAFKA_CONSUMERS.dec()
                # FIXED: Close Redis connection
                await redis_cache.close()
                logger.info(f"Context engine worker {worker_id} stopped")
                
        except Exception as e:
            retry_count += 1
            logger.error(f"Kafka consumer error (attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count < max_retries:
                # Exponential backoff
                wait_time = 2 ** retry_count
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.critical("Max retries exceeded, worker shutting down")
                raise

if __name__ == "__main__":
    asyncio.run(context_engine_worker())
