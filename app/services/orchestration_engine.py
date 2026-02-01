

# SECURITY: All DB queries must use SQLAlchemy ORM, never raw SQL.
import asyncio
import logging
import os
import time
try:
    from aiokafka import AIOKafkaConsumer
except ImportError:
    AIOKafkaConsumer = None
from app.core.config import settings
from app.models.core import AuditLog
from app.core.database import engine, AsyncSessionLocal
from app.core.kafka import publish_event
from app.core.dlq import send_to_dlq
from app.core.redis_client import redis_cache
from datetime import datetime
import json
import uuid

# Metrics imports
from app.monitoring.metrics import (
    ACTIONS_CREATED,
    ACTIVE_KAFKA_CONSUMERS
)

UPDATED_TOPIC = "context.updated"
ACTION_TOPIC = "action.executed"

logger = logging.getLogger("orchestration_engine")

HIGH_INTENT_THRESHOLD = 70.0

async def create_task_in_salesforce(account_id, account_name):
    # Placeholder for Salesforce Task creation (mocked)
    logger.info(f"Creating Salesforce Task for account {account_id} ({account_name})")
    # Simulate API call
    await asyncio.sleep(0.5)
    return {"task_id": str(uuid.uuid4()), "status": "created"}

async def log_action(session, account_id, account_name, action_type, risk, status):
    audit = AuditLog(
        id=str(uuid.uuid4()),
        event_type=action_type,
        actor_id="orchestration_engine",
        payload={"account_id": account_id, "account_name": account_name, "risk": risk, "status": status},
        created_at=datetime.utcnow(),
        compliance_tag="auto-approved"
    )
    session.add(audit)
    await session.commit()
    logger.info(f"Audit event logged for {account_id}: {action_type}")
    
    # Track action created
    ACTIONS_CREATED.labels(
        action_type=action_type,
        risk_level=risk,
        status=status
    ).inc()

async def publish_action_executed(account_id, account_name, task_id):
    event = {
        "account_id": account_id,
        "account_name": account_name,
        "task_id": task_id,
        "timestamp": datetime.utcnow().isoformat(),
        "action": "create_task"
    }
    await publish_event(ACTION_TOPIC, event)
    logger.info(f"Published action.executed for {account_id}")

async def update_heartbeat():
    """Update worker heartbeat in Redis"""
    worker_id = os.getenv('WORKER_ID', 'unknown')
    await redis_cache.connect()
    await redis_cache.redis.set(
        'worker:orchestration_engine:last_heartbeat',
        time.time(),
        ex=120  # 2-minute expiration
    )
    logger.debug(f"Worker {worker_id} heartbeat updated")

async def orchestration_engine_worker():
    worker_id = os.getenv('WORKER_ID', 'unknown')
    logger.info(f"Starting orchestration engine worker {worker_id}")
    
    consumer = AIOKafkaConsumer(
        UPDATED_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="orchestration_engine_group",
        value_deserializer=lambda m: json.loads(m.decode()),
        auto_offset_reset="earliest",
        enable_auto_commit=False,  # Manual commit for safety
        max_poll_records=10,  # Batch processing
        session_timeout_ms=30000,
        heartbeat_interval_ms=10000,
    )
    
    await consumer.start()
    ACTIVE_KAFKA_CONSUMERS.inc()
    
    # Initial heartbeat
    await update_heartbeat()
    
    message_count = 0
    batch_size = 10
    
    try:
        async for msg in consumer:
            context = msg.value
            account_id = context["account_id"]
            intent_score = context["intent_score"]
            account_name = f"Account-{account_id[:8]}"  # Placeholder
            
            try:
                if intent_score > HIGH_INTENT_THRESHOLD:
                    logger.info(f"High-intent detected for {account_id} ({account_name}), score={intent_score}")
                    async with AsyncSessionLocal() as session:
                        # Create Task in Salesforce
                        result = await create_task_in_salesforce(account_id, account_name)
                        # Log action
                        await log_action(session, account_id, account_name, "create_task", "low", "approved")
                        # Publish action.executed
                        await publish_action_executed(account_id, account_name, result["task_id"])
                
                message_count += 1
                
                # Batch commit offsets
                if message_count >= batch_size:
                    await consumer.commit()
                    message_count = 0
                    logger.debug(f"Committed batch of {batch_size} messages")
                
                # Update heartbeat every 5 messages
                if message_count % 5 == 0:
                    await update_heartbeat()
                    
            except Exception as e:
                logger.exception(f"Failed to process context: {e}")
                await send_to_dlq(UPDATED_TOPIC, msg.value, str(e), retry_count=msg.value.get('retry_count', 0))
                # Still commit to avoid reprocessing
                await consumer.commit()
    finally:
        await consumer.stop()
        ACTIVE_KAFKA_CONSUMERS.dec()
        logger.info(f"Orchestration engine worker {worker_id} stopped")

if __name__ == "__main__":
    asyncio.run(orchestration_engine_worker())
