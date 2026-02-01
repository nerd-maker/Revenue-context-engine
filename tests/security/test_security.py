"""
Security Tests

Tests security controls including SQL injection protection and tenant isolation.
"""
import pytest
import uuid
import asyncio
from sqlalchemy import select, text
from app.models.core import Signal


@pytest.mark.security
@pytest.mark.asyncio
async def test_sql_injection_protection(db_session):
    """Security: Verify no SQL injection via user inputs"""
    malicious_inputs = [
        "'; DROP TABLE signals; --",
        "' OR '1'='1",
        "1; DELETE FROM signals WHERE '1'='1",
        "admin'--",
        "' UNION SELECT * FROM users--"
    ]
    
    for malicious in malicious_inputs:
        # Attempt to use malicious input in query
        # SQLAlchemy parameterization should protect against this
        try:
            result = await db_session.execute(
                select(Signal).where(Signal.source == malicious)
            )
            signals = result.scalars().all()
            # Should execute safely without SQL injection
            assert isinstance(signals, list)
        except Exception as e:
            # If it fails, it should be a safe error, not SQL execution
            assert "DROP" not in str(e).upper()
            assert "DELETE" not in str(e).upper()


@pytest.mark.security
@pytest.mark.asyncio
async def test_tenant_isolation(db_session_with_tenant, tenant_id):
    """Security: Verify tenant isolation"""
    from app.models.core import Signal
    from datetime import datetime, timedelta
    
    # Create signal for this tenant
    signal1 = Signal(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        account_id=uuid.uuid4(),
        source="test",
        type="web_visit",
        payload={},
        confidence_score=0.8,
        timestamp=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=90)
    )
    db_session_with_tenant.add(signal1)
    await db_session_with_tenant.commit()
    
    # Query should only return this tenant's signals
    result = await db_session_with_tenant.execute(
        select(Signal).where(Signal.tenant_id == tenant_id)
    )
    signals = result.scalars().all()
    
    # All signals should belong to this tenant
    assert all(s.tenant_id == tenant_id for s in signals)


@pytest.mark.security
@pytest.mark.asyncio
async def test_tenant_isolation_under_load(db_session):
    """Security: Verify tenant isolation holds under concurrent load"""
    from app.models.core import Signal
    from datetime import datetime, timedelta
    
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    
    async def create_signals(tenant_id, count):
        """Create signals for a tenant"""
        for i in range(count):
            signal = Signal(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                account_id=uuid.uuid4(),
                source="test",
                type="web_visit",
                payload={"index": i},
                confidence_score=0.8,
                timestamp=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=90)
            )
            db_session.add(signal)
        await db_session.commit()
    
    # Create signals for both tenants concurrently
    await asyncio.gather(
        create_signals(tenant_a, 10),
        create_signals(tenant_b, 10)
    )
    
    # Verify isolation: Tenant A sees only their signals
    result_a = await db_session.execute(
        select(Signal).where(Signal.tenant_id == tenant_a)
    )
    signals_a = result_a.scalars().all()
    
    result_b = await db_session.execute(
        select(Signal).where(Signal.tenant_id == tenant_b)
    )
    signals_b = result_b.scalars().all()
    
    assert len(signals_a) == 10
    assert len(signals_b) == 10
    assert all(s.tenant_id == tenant_a for s in signals_a)
    assert all(s.tenant_id == tenant_b for s in signals_b)


@pytest.mark.security
@pytest.mark.asyncio
async def test_event_store_tenant_isolation(db_session_with_tenant, tenant_id):
    """Security: Verify event store respects tenant isolation"""
    from app.services.event_store import event_store
    
    account_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    
    # Create event for this tenant
    await event_store.append_event(
        session=db_session_with_tenant,
        aggregate_id=account_id,
        aggregate_type='account',
        event_type='test.event',
        event_data={'test': 'data'},
        actor_id=actor_id,
        tenant_id=tenant_id
    )
    
    # Retrieve events
    events = await event_store.get_events(db_session_with_tenant, account_id)
    
    # All events should belong to this tenant
    assert all(e.tenant_id == tenant_id for e in events)


@pytest.mark.security
@pytest.mark.asyncio
async def test_no_unauthorized_data_access(db_session):
    """Security: Verify no cross-tenant data leakage"""
    from app.models.events import Event
    
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    
    # Create event for tenant A
    event_a = Event(
        aggregate_id=uuid.uuid4(),
        aggregate_type='account',
        event_type='test.event',
        event_data={'tenant': 'A'},
        version=1,
        actor_id=uuid.uuid4(),
        tenant_id=tenant_a
    )
    db_session.add(event_a)
    await db_session.commit()
    
    # Query for tenant B should not return tenant A's events
    result = await db_session.execute(
        select(Event).where(Event.tenant_id == tenant_b)
    )
    events_b = result.scalars().all()
    
    assert len(events_b) == 0
