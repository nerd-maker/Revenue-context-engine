"""
Integration tests for Prometheus metrics.

Tests verify that metrics are properly exposed and updated.
"""
import pytest
from httpx import AsyncClient
from prometheus_client import REGISTRY
from app.api.main import app


@pytest.mark.asyncio
async def test_metrics_endpoint_accessible():
    """Verify /metrics endpoint is accessible and returns Prometheus format"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/metrics")
        
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_metrics_exposed():
    """Verify expected metrics are exposed"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/metrics")
        content = response.text
        
        # Check for key metrics
        assert "intent_score_calculation_seconds" in content
        assert "context_update_seconds" in content
        assert "email_generation_seconds" in content
        assert "api_request_seconds" in content
        assert "signals_processed_total" in content
        assert "actions_created_total" in content
        assert "cache_hits_total" in content
        assert "cache_misses_total" in content
        assert "kafka_consumers_active" in content


@pytest.mark.asyncio
async def test_api_request_latency_tracked():
    """Verify API requests update latency metrics"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Make a request to health endpoint
        await client.get("/health")
        
        # Check metrics
        response = await client.get("/metrics")
        content = response.text
        
        # Should have api_request_seconds metric with health endpoint
        assert "api_request_seconds" in content
        assert 'endpoint="/health"' in content


@pytest.mark.asyncio
async def test_signal_processing_increments_counter():
    """Verify signal processing updates metrics counter"""
    # Get initial count
    initial = REGISTRY.get_sample_value(
        'signals_processed_total',
        {'source': 'test', 'type': 'web_visit', 'status': 'success'}
    ) or 0
    
    # Import and call signal processing (mocked)
    from app.monitoring.metrics import SIGNALS_PROCESSED
    
    # Simulate signal processing
    SIGNALS_PROCESSED.labels(
        source='test',
        type='web_visit',
        status='success'
    ).inc()
    
    # Verify counter incremented
    final = REGISTRY.get_sample_value(
        'signals_processed_total',
        {'source': 'test', 'type': 'web_visit', 'status': 'success'}
    )
    
    assert final == initial + 1


@pytest.mark.asyncio
async def test_cache_metrics():
    """Verify cache hit/miss metrics work"""
    from app.monitoring.metrics import CACHE_HITS, CACHE_MISSES
    
    initial_hits = REGISTRY.get_sample_value('cache_hits_total') or 0
    initial_misses = REGISTRY.get_sample_value('cache_misses_total') or 0
    
    # Simulate cache operations
    CACHE_HITS.inc()
    CACHE_MISSES.inc()
    
    final_hits = REGISTRY.get_sample_value('cache_hits_total')
    final_misses = REGISTRY.get_sample_value('cache_misses_total')
    
    assert final_hits == initial_hits + 1
    assert final_misses == initial_misses + 1
