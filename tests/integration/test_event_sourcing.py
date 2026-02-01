"""
Event Sourcing Integration Tests

Tests event store functionality including:
- Event appending with optimistic locking
- State reconstruction from events
- Point-in-time queries
"""
import pytest
import uuid
from datetime import datetime, timedelta
import asyncio
from app.services.event_store import event_store
from app.models.events import Event


@pytest.mark.asyncio
async def test_append_event(db_session_with_tenant, tenant_id):
    """Test appending events to event store"""
    account_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    
    event = await event_store.append_event(
        session=db_session_with_tenant,
        aggregate_id=account_id,
        aggregate_type='account',
        event_type='account.created',
        event_data={'name': 'Acme Corp', 'domain': 'acme.com'},
        actor_id=actor_id,
        actor_type='system',
        tenant_id=tenant_id
    )
    
    assert event.id is not None
    assert event.aggregate_id == account_id
    assert event.version == 1
    assert event.event_type == 'account.created'


@pytest.mark.asyncio
async def test_optimistic_locking(db_session_with_tenant, tenant_id):
    """Test version-based optimistic locking"""
    account_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    
    # Append first event
    event1 = await event_store.append_event(
        session=db_session_with_tenant,
        aggregate_id=account_id,
        aggregate_type='account',
        event_type='account.created',
        event_data={'name': 'Acme Corp'},
        actor_id=actor_id,
        tenant_id=tenant_id
    )
    
    # Append second event
    event2 = await event_store.append_event(
        session=db_session_with_tenant,
        aggregate_id=account_id,
        aggregate_type='account',
        event_type='signal.received',
        event_data={'id': str(uuid.uuid4()), 'type': 'web_visit'},
        actor_id=actor_id,
        tenant_id=tenant_id
    )
    
    assert event1.version == 1
    assert event2.version == 2


@pytest.mark.asyncio
async def test_rebuild_state(db_session_with_tenant, tenant_id):
    """Verify state can be rebuilt from events"""
    account_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    
    # Append events
    await event_store.append_event(
        session=db_session_with_tenant,
        aggregate_id=account_id,
        aggregate_type='account',
        event_type='account.created',
        event_data={'name': 'Acme Corp', 'domain': 'acme.com', 'industry': 'SaaS'},
        actor_id=actor_id,
        tenant_id=tenant_id
    )
    
    await event_store.append_event(
        session=db_session_with_tenant,
        aggregate_id=account_id,
        aggregate_type='account',
        event_type='signal.received',
        event_data={
            'id': str(uuid.uuid4()),
            'type': 'web_visit',
            'source': 'website',
            'timestamp': datetime.utcnow().isoformat(),
            'confidence_score': 0.8
        },
        actor_id=actor_id,
        tenant_id=tenant_id
    )
    
    await event_store.append_event(
        session=db_session_with_tenant,
        aggregate_id=account_id,
        aggregate_type='account',
        event_type='intent.scored',
        event_data={'score': 85.0, 'scored_at': datetime.utcnow().isoformat()},
        actor_id=actor_id,
        tenant_id=tenant_id
    )
    
    # Rebuild state
    state = await event_store.rebuild_state(db_session_with_tenant, account_id)
    
    assert state['name'] == 'Acme Corp'
    assert state['domain'] == 'acme.com'
    assert len(state['signals']) == 1
    assert state['intent_score'] == 85.0


@pytest.mark.asyncio
async def test_point_in_time_reconstruction(db_session_with_tenant, tenant_id):
    """Verify state can be reconstructed at specific timestamp"""
    account_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    
    # Event at T0
    await event_store.append_event(
        session=db_session_with_tenant,
        aggregate_id=account_id,
        aggregate_type='account',
        event_type='account.created',
        event_data={'name': 'Acme Corp'},
        actor_id=actor_id,
        tenant_id=tenant_id
    )
    
    await asyncio.sleep(0.1)
    timestamp_t1 = datetime.utcnow()
    
    # Event at T1
    await asyncio.sleep(0.1)
    await event_store.append_event(
        session=db_session_with_tenant,
        aggregate_id=account_id,
        aggregate_type='account',
        event_type='signal.received',
        event_data={'id': str(uuid.uuid4()), 'type': 'web_visit'},
        actor_id=actor_id,
        tenant_id=tenant_id
    )
    
    await asyncio.sleep(0.1)
    timestamp_t2 = datetime.utcnow()
    
    # Rebuild at T1 (should only see account.created)
    state_t1 = await event_store.rebuild_state(
        db_session_with_tenant,
        account_id,
        up_to_timestamp=timestamp_t1
    )
    
    # Rebuild at T2 (should see both events)
    state_t2 = await event_store.rebuild_state(
        db_session_with_tenant,
        account_id,
        up_to_timestamp=timestamp_t2
    )
    
    assert 'signals' not in state_t1 or len(state_t1.get('signals', [])) == 0
    assert len(state_t2.get('signals', [])) == 1


@pytest.mark.asyncio
async def test_event_retrieval(db_session_with_tenant, tenant_id):
    """Test retrieving events for an aggregate"""
    account_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    
    # Create 5 events
    for i in range(5):
        await event_store.append_event(
            session=db_session_with_tenant,
            aggregate_id=account_id,
            aggregate_type='account',
            event_type=f'test.event.{i}',
            event_data={'index': i},
            actor_id=actor_id,
            tenant_id=tenant_id
        )
    
    # Get all events
    events = await event_store.get_events(db_session_with_tenant, account_id)
    assert len(events) == 5
    
    # Get events from version 2
    events_from_v2 = await event_store.get_events(
        db_session_with_tenant,
        account_id,
        from_version=2
    )
    assert len(events_from_v2) == 3  # versions 3, 4, 5
