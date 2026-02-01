import pytest
import uuid
from datetime import datetime
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures(salesforce_breaker, call_salesforce_api):
    """Verify circuit opens after 5 failures"""
    from pybreaker import CircuitBreakerError
    salesforce_breaker._state = 'closed'

    # Simulate 5 failures
    for _ in range(5):
        with pytest.raises(Exception):
            await call_salesforce_api('https://httpstat.us/500')

    # Circuit should now be OPEN
    assert salesforce_breaker.current_state == 'open'

    # Next call should fail immediately (no API call)
    with pytest.raises(CircuitBreakerError):
        await call_salesforce_api('https://httpstat.us/200')
