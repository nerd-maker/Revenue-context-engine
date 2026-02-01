import logging
import json
from datetime import datetime
from app.core.kafka import kafka_manager
from prometheus_client import Counter

logger = logging.getLogger("dlq")

DLQ_MESSAGES = Counter(
    'dlq_messages_total',
    'Total messages sent to DLQ',
    ['topic']
)

async def send_to_dlq(topic: str, message: dict, error: str, retry_count: int = 0):
    """
    Send failed message to Dead Letter Queue.
    DLQ topic naming: {original_topic}.dlq
    """
    dlq_topic = f"{topic}.dlq"
    dlq_event = {
        "original_topic": topic,
        "original_message": message,
        "error": str(error),
        "error_timestamp": datetime.utcnow().isoformat(),
        "retry_count": retry_count,
        "can_retry": retry_count < 3,
    }
    producer = await kafka_manager.get_producer()
    await producer.send_and_wait(dlq_topic, json.dumps(dlq_event).encode())
    logger.error(f"Sent message to DLQ: {dlq_topic}, error: {error}")
    DLQ_MESSAGES.labels(topic=topic).inc()
