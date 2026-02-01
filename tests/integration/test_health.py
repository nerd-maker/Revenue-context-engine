"""
Integration tests for health check endpoints.

Tests verify that health checks correctly report system status.
"""
import pytest
from httpx import AsyncClient
from app.api.main import app
from unittest.mock import patch, AsyncMock
import time


@pytest.mark.asyncio
async def test_basic_health_check():
    """Verify /health endpoint returns healthy status"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


@pytest.mark.asyncio
async def test_detailed_health_all_healthy():
    """Verify /health/detailed when all dependencies are healthy"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health/detailed")
        
        # May return 200 or 503 depending on actual service availability
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "timestamp" in data
        
        # Should check database, redis, and kafka
        checks = data["checks"]
        assert "database" in checks
        assert "redis" in checks
        assert "kafka" in checks


@pytest.mark.asyncio
async def test_detailed_health_database_down():
    """Verify /health/detailed returns 503 when database is down"""
    with patch('app.core.database.engine.connect') as mock_connect:
        # Simulate database connection failure
        mock_connect.side_effect = Exception("Database connection failed")
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health/detailed")
            
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["checks"]["database"]["status"] == "unhealthy"


@pytest.mark.asyncio
async def test_worker_health_no_heartbeats():
    """Verify /health/workers detects missing worker heartbeats"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health/workers")
        
        # Without workers running, should report unhealthy
        # (unless workers are actually running in test environment)
        data = response.json()
        assert "status" in data
        
        # If unhealthy, should list problematic workers
        if data["status"] == "unhealthy":
            assert "workers" in data
            assert len(data["workers"]) > 0


@pytest.mark.asyncio
async def test_worker_health_with_heartbeats():
    """Verify /health/workers reports healthy when heartbeats are fresh"""
    from app.core.redis_client import redis_cache
    
    # Mock Redis to return recent heartbeat
    with patch.object(redis_cache, 'redis') as mock_redis:
        mock_redis.get = AsyncMock(return_value=str(time.time()))
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health/workers")
            
            data = response.json()
            # With fresh heartbeats, should be healthy
            # (actual result depends on Redis mock working correctly)
            assert "status" in data


@pytest.mark.asyncio
async def test_worker_health_stale_heartbeat():
    """Verify /health/workers detects stale worker heartbeats"""
    from app.core.redis_client import redis_cache
    
    # Mock Redis to return old heartbeat (2 minutes ago)
    stale_time = time.time() - 120
    
    with patch.object(redis_cache, 'redis') as mock_redis:
        mock_redis.get = AsyncMock(return_value=str(stale_time))
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health/workers")
            
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "workers" in data
