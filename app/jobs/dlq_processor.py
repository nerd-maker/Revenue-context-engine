"""
Cron job: Process DLQ messages and retry
Schedule: */5 * * * * (every 5 minutes)
"""
from aiokafka import AIOKafkaConsumer
import asyncio
import json
import logging
from app.core.config import settings
from app.core.kafka import publish_event

logger = logging.getLogger("dlq_processor")

async def process_dlq():
    consumer = AIOKafkaConsumer(
        'signals.raw.dlq',
        'context.updated.dlq',
        'actions.proposed.dlq',
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id='dlq_processor',
        auto_offset_reset='earliest',
    )
    await consumer.start()
    try:
        async for msg in consumer:
            dlq_event = json.loads(msg.value.decode())
            if not dlq_event.get('can_retry', False):
                logger.info(f"Skipping non-retryable message: {dlq_event}")
                await consumer.commit()
                continue
            original_topic = dlq_event['original_topic']
            original_message = dlq_event['original_message']
            original_message['retry_count'] = dlq_event['retry_count'] + 1
            try:
                await publish_event(original_topic, original_message)
                logger.info(f"Retried message from DLQ: {original_topic}")
                await consumer.commit()
            except Exception as e:
                logger.error(f"Failed to retry DLQ message: {e}")
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(process_dlq())
