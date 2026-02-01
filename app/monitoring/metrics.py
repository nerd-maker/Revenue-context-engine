"""
Prometheus metrics definitions for the Unified Revenue Context Engine.

This module defines comprehensive metrics for monitoring business operations,
system health, and performance.
"""
from prometheus_client import Counter, Histogram, Gauge, Summary
import time
from functools import wraps
import logging

logger = logging.getLogger("metrics")

# ============================================================================
# LATENCY METRICS
# ============================================================================

INTENT_SCORE_LATENCY = Histogram(
    'intent_score_calculation_seconds',
    'Time to calculate intent score',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

CONTEXT_UPDATE_LATENCY = Histogram(
    'context_update_seconds',
    'Time to update account context',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

EMAIL_GENERATION_LATENCY = Histogram(
    'email_generation_seconds',
    'Time to generate email with LLM',
    buckets=[1.0, 2.0, 5.0, 10.0, 30.0]
)

API_REQUEST_LATENCY = Histogram(
    'api_request_seconds',
    'API request latency',
    ['method', 'endpoint', 'status'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
)

SIGNAL_PROCESSING_DURATION = Histogram(
    'signal_processing_duration_seconds',
    'Time to process a signal from ingestion to context update',
    ['signal_type'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# ============================================================================
# BUSINESS METRICS - Counters
# ============================================================================

SIGNALS_PROCESSED = Counter(
    'signals_processed_total',
    'Total signals processed',
    ['signal_type', 'status']  # status: success, duplicate, failed
)
"""
Usage Example:
    SIGNALS_PROCESSED.labels(
        signal_type='job_posting',
        status='success'
    ).inc()
"""

EMAILS_SENT = Counter(
    'emails_sent_total',
    'Total emails sent',
    ['status', 'tenant_id']  # status: success, failed, rate_limited
)
"""
Usage Example:
    EMAILS_SENT.labels(
        status='success',
        tenant_id=str(tenant_id)
    ).inc()
    
    # On failure
    EMAILS_SENT.labels(
        status='failed',
        tenant_id=str(tenant_id)
    ).inc()
"""

ACTIONS_CREATED = Counter(
    'actions_created_total',
    'Total actions created',
    ['action_type', 'risk_level', 'status']
)

CACHE_HITS = Counter('cache_hits_total', 'Cache hits')
CACHE_MISSES = Counter('cache_misses_total', 'Cache misses')

DLQ_MESSAGES = Counter(
    'dlq_messages_total',
    'Messages sent to DLQ',
    ['topic']
)

LLM_API_CALLS = Counter(
    'llm_api_calls_total',
    'LLM API calls',
    ['model', 'status']  # status: success, error, rate_limited
)

# ============================================================================
# SYSTEM METRICS - Gauges
# ============================================================================

DB_CONNECTIONS = Gauge(
    'database_connections_active',
    'Number of active database connections'
)
"""
Usage Example:
    # Track active connections
    DB_CONNECTIONS.set(pool.checkedout())
    
    # Or increment/decrement
    DB_CONNECTIONS.inc()  # Connection acquired
    DB_CONNECTIONS.dec()  # Connection released
"""

REDIS_CONNECTIONS = Gauge(
    'redis_connections_active',
    'Number of active Redis connections'
)
"""
Usage Example:
    REDIS_CONNECTIONS.set(redis_pool.size)
"""

API_ERRORS = Counter(
    'api_errors_total',
    'Total API errors',
    ['endpoint', 'error_type']  # error_type: validation, auth, server, timeout
)
"""
Usage Example:
    # On validation error
    API_ERRORS.labels(
        endpoint='/api/signals',
        error_type='validation'
    ).inc()
    
    # On authentication error
    API_ERRORS.labels(
        endpoint='/api/signals',
        error_type='auth'
    ).inc()
    
    # On server error
    API_ERRORS.labels(
        endpoint='/api/signals',
        error_type='server'
    ).inc()
"""

ACTIVE_KAFKA_CONSUMERS = Gauge(
    'kafka_consumers_active',
    'Number of active Kafka consumers'
)

KAFKA_LAG = Gauge(
    'kafka_consumer_lag',
    'Kafka consumer lag',
    ['topic', 'partition']
)

DB_POOL_SIZE = Gauge(
    'db_pool_size',
    'Database connection pool size'
)

DB_POOL_CHECKED_OUT = Gauge(
    'db_pool_checked_out',
    'Checked out database connections'
)

INTENT_SCORE_DISTRIBUTION = Histogram(
    'intent_score_value',
    'Distribution of intent scores',
    buckets=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
)

# ============================================================================
# DECORATORS
# ============================================================================

def track_latency(metric: Histogram):
    """
    Decorator to track function latency.
    
    Usage:
        @track_latency(INTENT_SCORE_LATENCY)
        async def compute_intent_score(signals):
            # Calculate intent score
            return score
        
        @track_latency(EMAIL_GENERATION_LATENCY)
        async def generate_email(context):
            # Generate email with LLM
            return email
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                metric.observe(duration)
                logger.debug(f"{func.__name__} took {duration:.3f}s")
        return wrapper
    return decorator


def track_signal_processing(signal_type: str):
    """
    Decorator to track signal processing duration.
    
    Usage:
        @track_signal_processing('job_posting')
        async def process_job_posting_signal(signal):
            # Process signal
            return result
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                SIGNALS_PROCESSED.labels(
                    signal_type=signal_type,
                    status='success'
                ).inc()
                return result
            except Exception as e:
                SIGNALS_PROCESSED.labels(
                    signal_type=signal_type,
                    status='failed'
                ).inc()
                raise
            finally:
                duration = time.time() - start
                SIGNAL_PROCESSING_DURATION.labels(
                    signal_type=signal_type
                ).observe(duration)
        return wrapper
    return decorator


# ============================================================================
# STRUCTURED LOGGING CONFIGURATION
# ============================================================================

def configure_structured_logging():
    """
    Configure structured logging with JSON formatting.
    
    Call this in your application startup to enable structured logging
    that integrates well with log aggregation systems like ELK, Splunk, etc.
    
    Usage:
        # In app/api/main.py startup
        from app.monitoring.metrics import configure_structured_logging
        
        @app.on_event("startup")
        async def startup_event():
            configure_structured_logging()
    """
    import json
    import sys
    
    class StructuredFormatter(logging.Formatter):
        """JSON formatter for structured logging."""
        
        def format(self, record):
            log_data = {
                'timestamp': self.formatTime(record, self.datefmt),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
            }
            
            # Add extra fields if present
            if hasattr(record, 'extra'):
                log_data.update(record.extra)
            
            # Add exception info if present
            if record.exc_info:
                log_data['exception'] = self.formatException(record.exc_info)
            
            return json.dumps(log_data)
    
    # Configure root logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)
    
    logger.info("Structured logging configured")


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
COMPLETE USAGE EXAMPLES:

1. Track Signal Processing:
    from app.monitoring.metrics import SIGNALS_PROCESSED, SIGNAL_PROCESSING_DURATION
    
    async def process_signal(signal):
        start = time.time()
        try:
            # Process signal
            result = await do_processing(signal)
            
            # Track success
            SIGNALS_PROCESSED.labels(
                signal_type=signal.type,
                status='success'
            ).inc()
            
            return result
        except Exception as e:
            # Track failure
            SIGNALS_PROCESSED.labels(
                signal_type=signal.type,
                status='failed'
            ).inc()
            raise
        finally:
            # Track duration
            duration = time.time() - start
            SIGNAL_PROCESSING_DURATION.labels(
                signal_type=signal.type
            ).observe(duration)

2. Track Email Sending:
    from app.monitoring.metrics import EMAILS_SENT
    
    async def send_email(tenant_id, email_data):
        try:
            await email_api.send(email_data)
            EMAILS_SENT.labels(
                status='success',
                tenant_id=str(tenant_id)
            ).inc()
        except RateLimitError:
            EMAILS_SENT.labels(
                status='rate_limited',
                tenant_id=str(tenant_id)
            ).inc()
            raise
        except Exception:
            EMAILS_SENT.labels(
                status='failed',
                tenant_id=str(tenant_id)
            ).inc()
            raise

3. Track Database Connections:
    from app.monitoring.metrics import DB_CONNECTIONS
    
    async def get_db_connection():
        DB_CONNECTIONS.inc()
        try:
            conn = await pool.acquire()
            return conn
        finally:
            DB_CONNECTIONS.dec()

4. Track API Errors:
    from app.monitoring.metrics import API_ERRORS
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request, exc):
        API_ERRORS.labels(
            endpoint=request.url.path,
            error_type='validation'
        ).inc()
        return JSONResponse(status_code=400, content={"detail": str(exc)})

5. Use Latency Decorator:
    from app.monitoring.metrics import track_latency, INTENT_SCORE_LATENCY
    
    @track_latency(INTENT_SCORE_LATENCY)
    async def compute_intent_score(signals):
        # This function's execution time will be automatically tracked
        score = calculate_score(signals)
        return score
"""
