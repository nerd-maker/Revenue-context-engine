try:
    from aiokafka import AIOKafkaProducer
except ImportError:
    AIOKafkaProducer = None
from app.core.config import settings
import asyncio
import logging

logger = logging.getLogger("kafka_manager")

class KafkaProducerManager:
    """
    Singleton Kafka producer manager.
    Reuses single producer across all services for performance.
    """
    def __init__(self):
        self._producer = None
        self._lock = asyncio.Lock()

    async def get_producer(self) -> AIOKafkaProducer:
        # Check if Kafka is enabled
        if not settings.KAFKA_ENABLED:
            logger.warning("Kafka is disabled - returning None")
            return None
        
        if self._producer is None:
            async with self._lock:
                if self._producer is None:
                    logger.info("Initializing global Kafka producer")
                    self._producer = AIOKafkaProducer(
                        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                        compression_type='gzip',
                        acks='all',
                        max_batch_size=16384,
                        linger_ms=10,
                        retries=3,
                    )
                    await self._producer.start()
                    logger.info("Kafka producer started")
        return self._producer

    async def close(self):
        if self._producer:
            logger.info("Closing Kafka producer")
            await self._producer.stop()
            self._producer = None

kafka_manager = KafkaProducerManager()

async def publish_event(topic: str, event: dict):
    """
    Publish event with request_id for tracing.
    Automatically adds request_id and published_at timestamp.
    If Kafka is disabled, logs the event instead.
    """
    import json
    from datetime import datetime
    from app.middleware.tracing import request_id_var
    
    # Check if Kafka is enabled
    if not settings.KAFKA_ENABLED:
        logger.debug(f"Kafka disabled - event not published to {topic}: {event.get('type', 'unknown')}")
        return
    
    # Add tracing metadata
    event['request_id'] = request_id_var.get() or 'no-request-id'
    event['published_at'] = datetime.utcnow().isoformat()
    
    producer = await kafka_manager.get_producer()
    if producer:  # Additional safety check
        await producer.send_and_wait(topic, json.dumps(event).encode())
    else:
        logger.warning(f"Kafka producer not available - event not published: {topic}")

