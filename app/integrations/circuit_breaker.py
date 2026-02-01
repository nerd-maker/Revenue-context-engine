from pybreaker import CircuitBreaker, CircuitBreakerError
import httpx
from prometheus_client import Gauge
import logging

logger = logging.getLogger("circuit_breaker")

# Metrics
CIRCUIT_BREAKER_STATE = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ['service']
)

# Circuit breakers for each external service
def _state_listener_factory(service):
    return lambda breaker, state: CIRCUIT_BREAKER_STATE.labels(service=service).set(
        0 if state == 'closed' else (1 if state == 'open' else 2)
    )

salesforce_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=60,
    name='salesforce_api',
    listeners=[_state_listener_factory('salesforce')]
)

clearbit_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=60,
    name='clearbit_api',
    listeners=[_state_listener_factory('clearbit')]
)

outreach_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=60,
    name='outreach_api',
    listeners=[_state_listener_factory('outreach')]
)

@salesforce_breaker
async def call_salesforce_api(url: str, method: str = 'POST', data: dict = None, headers: dict = None):
    """Make Salesforce API call with circuit breaker"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        if method == 'POST':
            response = await client.post(url, data=data, headers=headers)
        elif method == 'GET':
            response = await client.get(url, params=data, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        response.raise_for_status()
        return response.json()

@clearbit_breaker
async def call_clearbit_api(url: str, params: dict = None):
    """Make Clearbit API call with circuit breaker"""
    from app.core.config import settings
    headers = {"Authorization": f"Bearer {settings.CLEARBIT_API_KEY}"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

@outreach_breaker
async def call_outreach_api(url: str, method: str = 'POST', data: dict = None):
    """Make Outreach API call with circuit breaker"""
    from app.core.config import settings
    headers = {"Authorization": f"Bearer {settings.OUTREACH_API_KEY}"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        if method == 'POST':
            response = await client.post(url, json=data, headers=headers)
        else:
            response = await client.get(url, params=data, headers=headers)
        response.raise_for_status()
        return response.json()
