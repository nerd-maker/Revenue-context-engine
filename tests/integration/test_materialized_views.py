"""
Materialized Views Integration Tests

Tests CQRS read model performance and correctness.
"""
import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_materialized_view_exists(db_session):
    """Test that materialized views are created"""
    # Check account_intent_scores view exists
    result = await db_session.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_matviews 
            WHERE matviewname = 'account_intent_scores'
        );
    """))
    exists = result.scalar()
    assert exists is True


@pytest.mark.asyncio
async def test_high_intent_accounts_view(db_session):
    """Test high_intent_accounts materialized view"""
    result = await db_session.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_matviews 
            WHERE matviewname = 'high_intent_accounts'
        );
    """))
    exists = result.scalar()
    assert exists is True


@pytest.mark.asyncio
async def test_view_query_performance(db_session, tenant_id):
    """Test that materialized view queries are fast"""
    import time
    
    # Query materialized view
    start = time.time()
    result = await db_session.execute(text("""
        SELECT account_id, intent_score
        FROM high_intent_accounts
        WHERE tenant_id = :tenant_id
        ORDER BY intent_score DESC
        LIMIT 100
    """), {"tenant_id": tenant_id})
    duration = time.time() - start
    
    rows = result.fetchall()
    
    # Should be very fast (< 100ms)
    assert duration < 0.1, f"Query too slow: {duration*1000:.0f}ms"
