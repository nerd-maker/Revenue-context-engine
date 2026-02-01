"""
Health check endpoints for monitoring and orchestration.

Provides liveness, readiness, and comprehensive dependency health checks.
"""
from fastapi import APIRouter, Response
from sqlalchemy import text
from app.core.redis_client import redis_cache
from app.core.database import engine
from app.core.kafka import kafka_manager
from app.core.config import settings
import time
import logging
import json
import asyncio

router = APIRouter()
logger = logging.getLogger("health")

WORKER_HEARTBEAT_TIMEOUT = 60  # seconds


@router.get('/health')
async def health_check():
    """
    Basic liveness check - returns 200 if application is running.
    
    Use this for Kubernetes liveness probes.
    """
    return {"status": "healthy", "timestamp": time.time()}


async def check_database() -> dict:
    """Check database connectivity and measure latency."""
    start = time.time()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency = time.time() - start
        return {
            "status": "healthy",
            "latency_ms": round(latency * 1000, 2)
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "latency_ms": round((time.time() - start) * 1000, 2)
        }


async def check_redis() -> dict:
    """Check Redis connectivity and measure latency."""
    start = time.time()
    try:
        await redis_cache.connect()
        await redis_cache.redis.ping()
        latency = time.time() - start
        return {
            "status": "healthy",
            "latency_ms": round(latency * 1000, 2)
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "latency_ms": round((time.time() - start) * 1000, 2)
        }


async def check_kafka() -> dict:
    """Check Kafka connectivity with 5-second timeout."""
    start = time.time()
    try:
        # Use asyncio.wait_for to enforce 5-second timeout
        async def list_topics():
            producer = await kafka_manager.get_producer()
            if producer:
                # Try to get cluster metadata
                metadata = await producer.client.fetch_all_metadata()
                return len(metadata.topics) if metadata else 0
            return None
        
        topic_count = await asyncio.wait_for(list_topics(), timeout=5.0)
        latency = time.time() - start
        
        if topic_count is not None:
            return {
                "status": "healthy",
                "latency_ms": round(latency * 1000, 2),
                "topics": topic_count
            }
        else:
            return {
                "status": "unhealthy",
                "error": "Kafka producer not available",
                "latency_ms": round(latency * 1000, 2)
            }
    except asyncio.TimeoutError:
        logger.error("Kafka health check timed out after 5 seconds")
        return {
            "status": "unhealthy",
            "error": "Timeout after 5 seconds",
            "latency_ms": 5000
        }
    except Exception as e:
        logger.error(f"Kafka health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "latency_ms": round((time.time() - start) * 1000, 2)
        }


@router.get('/health/ready')
async def readiness_check():
    """
    Comprehensive readiness check - validates all dependencies.
    
    Checks database, Redis, and Kafka connectivity concurrently.
    Returns "healthy" if all pass, "degraded" if any fail.
    
    Use this for Kubernetes readiness probes.
    """
    # Run all checks concurrently for faster response
    db_check, redis_check, kafka_check = await asyncio.gather(
        check_database(),
        check_redis(),
        check_kafka(),
        return_exceptions=True
    )
    
    # Handle any exceptions from gather
    checks = {}
    
    if isinstance(db_check, Exception):
        checks['database'] = {"status": "unhealthy", "error": str(db_check)}
    else:
        checks['database'] = db_check
    
    if isinstance(redis_check, Exception):
        checks['redis'] = {"status": "unhealthy", "error": str(redis_check)}
    else:
        checks['redis'] = redis_check
    
    if isinstance(kafka_check, Exception):
        checks['kafka'] = {"status": "unhealthy", "error": str(kafka_check)}
    else:
        checks['kafka'] = kafka_check
    
    # Determine overall status
    all_healthy = all(
        check.get('status') == 'healthy' 
        for check in checks.values()
    )
    
    overall_status = "healthy" if all_healthy else "degraded"
    status_code = 200 if all_healthy else 503
    
    # Calculate total latency
    total_latency = sum(
        check.get('latency_ms', 0) 
        for check in checks.values()
    )
    
    response_data = {
        "status": overall_status,
        "checks": checks,
        "total_latency_ms": round(total_latency, 2),
        "timestamp": time.time()
    }
    
    return Response(
        content=json.dumps(response_data, indent=2),
        status_code=status_code,
        media_type="application/json"
    )


@router.get('/health/workers')
async def worker_health():
    """
    Check if background workers are running.
    Uses Redis heartbeats to detect stale workers.
    """
    workers = ['context_engine', 'orchestration_engine', 'email_orchestration']
    unhealthy = []
    
    try:
        await redis_cache.connect()
        
        for worker in workers:
            key = f"worker:{worker}:last_heartbeat"
            last_heartbeat = await redis_cache.redis.get(key)
            
            if not last_heartbeat:
                unhealthy.append({
                    'worker': worker,
                    'status': 'unknown',
                    'reason': 'never started'
                })
            elif time.time() - float(last_heartbeat) > WORKER_HEARTBEAT_TIMEOUT:
                stale_duration = int(time.time() - float(last_heartbeat))
                unhealthy.append({
                    'worker': worker,
                    'status': 'stale',
                    'reason': f'last seen {stale_duration}s ago'
                })
        
        if unhealthy:
            return Response(
                content=json.dumps({
                    "status": "unhealthy",
                    "workers": unhealthy,
                    "timestamp": time.time()
                }),
                status_code=503,
                media_type="application/json"
            )
        
        return {
            "status": "healthy",
            "workers": workers,
            "timestamp": time.time()
        }
    
    except Exception as e:
        logger.error(f"Worker health check failed: {e}")
        return Response(
            content=json.dumps({
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }),
            status_code=503,
            media_type="application/json"
        )
