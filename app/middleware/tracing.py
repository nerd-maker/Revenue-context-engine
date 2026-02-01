"""
Request ID tracing middleware for distributed tracing.

Propagates request IDs through HTTP requests, logs, and Kafka events.
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from contextvars import ContextVar
import logging

# Context variable for request ID (accessible across async contexts)
request_id_var = ContextVar('request_id', default=None)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add X-Request-ID header to all requests.
    Propagates through logs and downstream services.
    """
    
    async def dispatch(self, request, call_next):
        # Get or generate request ID
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        
        # Store in context var (accessible by all code in this request)
        request_id_var.set(request_id)
        
        # Store in request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add to response headers
        response.headers['X-Request-ID'] = request_id
        
        return response

class RequestIDFilter(logging.Filter):
    """Add request_id to all log records"""
    
    def filter(self, record):
        record.request_id = request_id_var.get() or 'no-request-id'
        return True

def setup_logging():
    """
    Configure logging to include request_id in all log messages.
    Call this during application startup.
    """
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(request_id)s] - %(levelname)s - %(message)s'
    )
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())
    
    # Apply to root logger
    logger = logging.getLogger()
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    logging.info("Logging configured with request ID tracing")
