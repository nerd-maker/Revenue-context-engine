try:
	from fastapi import FastAPI
except ImportError:
	FastAPI = None
from app.services.signal_ingestion import router as signal_router
from app.integrations.salesforce_webhook import router as salesforce_router
from app.approval.api import router as approval_api_router
from app.approval.ui import router as approval_ui_router
from app.consent.api import router as consent_router
from app.laboratory.middleware import LaboratoryRoutingMiddleware
from app.laboratory.api import router as laboratory_router
from app.mock.clearbit_api import router as mock_clearbit_router
from app.integrations.salesforce_oauth import router as salesforce_oauth_router
from app.auth.api import router as auth_router
from app.middleware.tenant import TenantContextMiddleware
from app.middleware.ratelimit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.tenants.usage import router as usage_router
from app.middleware.security import add_cors
from app.middleware.validation import RequestValidationMiddleware
from app.compliance.gdpr import router as gdpr_router
from app.compliance.audit_export import router as audit_export_router

# Monitoring imports
from prometheus_client import make_asgi_app, REGISTRY
from app.monitoring.health import router as health_router
from app.middleware.tracing import RequestIDMiddleware, setup_logging
from app.monitoring.metrics import API_REQUEST_LATENCY

import logging
import time
from app.core.config import validate_settings, settings
from app.core.kafka import kafka_manager
from app.core.redis_client import redis_cache

# Setup logging with request ID tracing
setup_logging()

app = FastAPI(title="Unified Revenue Context Engine")

# Include routers
app.include_router(signal_router, prefix="/api")
app.include_router(salesforce_router, prefix="/api")
app.include_router(approval_api_router, prefix="/api")
app.include_router(approval_ui_router, prefix="/api")
app.include_router(consent_router, prefix="/api")
app.include_router(laboratory_router, prefix="/api")
app.include_router(mock_clearbit_router, prefix="/api")
app.include_router(salesforce_oauth_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(usage_router, prefix="/api")
app.include_router(gdpr_router, prefix="/api")
app.include_router(audit_export_router, prefix="/api")
app.include_router(health_router)  # Health checks at root level

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app(registry=REGISTRY)
app.mount("/metrics", metrics_app)

# Middleware to track request latency
@app.middleware("http")
async def track_requests(request, call_next):
    start = time.time()
    response = await call_next(request)
    
    # Track latency
    latency = time.time() - start
    API_REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).observe(latency)
    
    return response

# Add middleware (order matters - last added is executed first)
app.add_middleware(SecurityHeadersMiddleware)  # Security headers for all responses
app.add_middleware(RequestIDMiddleware)  # Request tracing
app.add_middleware(LaboratoryRoutingMiddleware)
app.add_middleware(TenantContextMiddleware)
app.add_middleware(RateLimitMiddleware, redis_client=redis_cache)  # Pass Redis client
app.add_middleware(RequestValidationMiddleware)

add_cors(app)

# Validate config at startup
@app.on_event("startup")
async def startup_event():
	validate_settings()
	# Connect to Redis for rate limiting and caching
	await redis_cache.connect()
	logging.getLogger("uvicorn").info(f"Starting in {settings.ENV} mode")

# Graceful shutdown for Kafka
@app.on_event("shutdown")
async def shutdown_event():
	await kafka_manager.close()
	await redis_cache.close()
	logging.getLogger("uvicorn").info("Application shutdown complete")

