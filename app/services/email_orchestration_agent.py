def build_email_prompt(account_name, industry, deal_stage, signals, brand_voice, do_not_say):
    return PROMPT_TEMPLATE.format(
        account_name=account_name,
        industry=industry,
        deal_stage=deal_stage,
        signals=signals,
        brand_voice=brand_voice,
        do_not_say=", ".join(do_not_say)
    )

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
from datetime import datetime, timedelta
import json
import uuid
try:
    from google import genai
except ImportError:
    genai = None

# Metrics imports
from app.monitoring.metrics import (
    EMAIL_GENERATION_LATENCY,
    LLM_API_CALLS,
    ACTIONS_CREATED,
    ACTIVE_KAFKA_CONSUMERS,
    track_latency
)

UPDATED_TOPIC = "context.updated"

logger = logging.getLogger("email_orchestration_agent")

HIGH_INTENT_THRESHOLD = 75.0
DO_NOT_SAY = ["pricing", "competitor", "synergy", "game-changer"]
BRAND_VOICE = "Professional, concise, no buzzwords."

# Configure Gemini API
if genai:
    genai.configure(api_key=settings.GEMINI_API_KEY)

PROMPT_TEMPLATE = """
You are an expert B2B sales assistant. Write a personalized, compliant outbound email for the following account.

Account: {account_name}
Industry: {industry}
Deal Stage: {deal_stage}
Recent Signals (last 7d):
{signals}

Constraints:
- Brand voice: {brand_voice}
- Do NOT mention: {do_not_say}
- No pricing, competitor names, or buzzwords

Output JSON:
{{
    "subject": "...",
    "body": "...",
    "reasoning": "..."
}}
"""

class EmailOrchestrationAgent:
    def __init__(self):
        self.high_risk_queue = []

    async def check_consent(self, session, email):
        from sqlalchemy import select
        from app.models.core import Consent
        result = await session.execute(
            select(Consent).where(
                (Consent.subject_id == email) & (Consent.revoked_at == None)
            )
        )
        return result.scalar_one_or_none() is not None

    @track_latency(EMAIL_GENERATION_LATENCY)
    async def generate_email(self, context, signals, deal_stage, industry):
        if not genai:
            raise ImportError("google-generativeai not installed. Install with: pip install google-generativeai")
        
        prompt = build_email_prompt(
            context["account_name"], industry, deal_stage, json.dumps(signals, indent=2), BRAND_VOICE, DO_NOT_SAY
        )
        
        try:
            # Use Gemini Pro model
            model = genai.GenerativeModel('gemini-pro')
            
            # Generate content (Gemini SDK doesn't have async yet, run in executor)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.4,
                        max_output_tokens=512,
                    )
                )
            )
            
            # Track successful LLM call
            LLM_API_CALLS.labels(model="gemini-pro", status="success").inc()
            
            content = response.text
            try:
                email_obj = json.loads(content)
            except Exception:
                logger.error(f"LLM output not valid JSON: {content}")
                raise
            
            # Confidence scoring (LLM self-rating or fallback)
            confidence = float(email_obj.get("confidence", 0.8))
            email_obj["confidence"] = confidence
            return email_obj
            
        except Exception as e:
            # Track failed LLM call
            LLM_API_CALLS.labels(model="gemini-pro", status="error").inc()
            logger.error(f"Gemini API error: {e}")
            raise

    async def create_action(self, session, context, email_obj, risk_level):
        action_id = str(uuid.uuid4())
        audit = AuditLog(
            id=action_id,
            event_type="send_email",
            actor_id="email_orchestration_agent",
            payload={
                "account_id": context["account_id"],
                "account_name": context["account_name"],
                "email": email_obj,
                "reasoning": email_obj.get("reasoning", ""),
                "risk_level": risk_level,
                "signals": context.get("signals", []),
                "intent_score": context.get("intent_score", 0)
            },
            created_at=datetime.utcnow(),
            compliance_tag="proposed" if risk_level == "medium" else "high-risk",
        )
        session.add(audit)
        await session.commit()
        logger.info(f"Proposed email action for {context['account_id']} (risk: {risk_level})")
        
        # Track action created
        ACTIONS_CREATED.labels(
            action_type="send_email",
            risk_level=risk_level,
            status="proposed"
        ).inc()
        
        return action_id

    async def enforce_daily_limit(self, account_id):
        # Use Redis for daily email limit (max 5 per day)
        key = f"email_limit:{account_id}:{datetime.utcnow().date()}"
        await redis_cache.connect()
        count = await redis_cache.redis.get(key)
        if count is None:
            await redis_cache.redis.set(key, 1, ex=86400)
            return True
        elif int(count) < 5:
            await redis_cache.redis.incr(key)
            return True
        else:
            return False

    async def process_context(self, context):
        account_id = context["account_id"]
        intent_score = context["intent_score"]
        if intent_score < HIGH_INTENT_THRESHOLD:
            return
        async with AsyncSessionLocal() as session:
            # Consent check (fail fast)
            consent_ok = await self.check_consent(session, account_id)
            if not consent_ok:
                logger.info(f"Consent not found for {account_id}, skipping email proposal.")
                return
            # Enforce daily limit
            if not await self.enforce_daily_limit(account_id):
                logger.info(f"Daily email limit reached for {account_id}")
                return
            # Gather context (mocked signals, deal stage, industry)
            account_name = f"Account-{account_id[:8]}"
            signals = [
                {"type": "web_visit", "desc": "Visited pricing page", "ts": str(datetime.utcnow() - timedelta(days=1))},
                {"type": "crm_stage_change", "desc": "Moved to Demo Scheduled", "ts": str(datetime.utcnow() - timedelta(days=2))}
            ]
            deal_stage = "Demo Scheduled"
            industry = "SaaS"
            # LLM email generation
            email_obj = await self.generate_email({"account_id": account_id, "account_name": account_name}, signals, deal_stage, industry)
            risk_level = "medium" if email_obj["confidence"] >= 0.7 else "high"
            await self.create_action(session, {
                "account_id": account_id,
                "account_name": account_name,
                "signals": signals,
                "intent_score": intent_score
            }, email_obj, risk_level)

    async def update_heartbeat(self):
        """Update worker heartbeat in Redis"""
        worker_id = os.getenv('WORKER_ID', 'unknown')
        await redis_cache.connect()
        await redis_cache.redis.set(
            'worker:email_orchestration:last_heartbeat',
            time.time(),
            ex=120  # 2-minute expiration
        )
        logger.debug(f"Worker {worker_id} heartbeat updated")

    async def run(self):
        worker_id = os.getenv('WORKER_ID', 'unknown')
        logger.info(f"Starting email orchestration agent worker {worker_id}")
        
        consumer = AIOKafkaConsumer(
            UPDATED_TOPIC,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="email_orchestration_group",
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
        await self.update_heartbeat()
        
        message_count = 0
        batch_size = 10
        
        try:
            async for msg in consumer:
                context = msg.value
                try:
                    await self.process_context(context)
                    
                    message_count += 1
                    
                    # Batch commit offsets
                    if message_count >= batch_size:
                        await consumer.commit()
                        message_count = 0
                        logger.debug(f"Committed batch of {batch_size} messages")
                    
                    # Update heartbeat every 5 messages
                    if message_count % 5 == 0:
                        await self.update_heartbeat()
                        
                except Exception as e:
                    logger.exception(f"Failed to process email orchestration: {e}")
                    await send_to_dlq(UPDATED_TOPIC, msg.value, str(e), retry_count=msg.value.get('retry_count', 0))
                    # Still commit to avoid reprocessing
                    await consumer.commit()
        finally:
            await consumer.stop()
            ACTIVE_KAFKA_CONSUMERS.dec()
            logger.info(f"Email orchestration agent worker {worker_id} stopped")

if __name__ == "__main__":
    agent = EmailOrchestrationAgent()
    asyncio.run(agent.run())
