"""
End-to-End Integration Tests

Tests complete signal-to-action flow with event sourcing.
"""
import pytest
import uuid
import asyncio
from datetime import datetime, timedelta
from app.models.core import Signal, AccountContext, Action
from app.services.event_store import event_store
from sqlalchemy import select


@pytest.mark.asyncio
@pytest.mark.slow
async def test_signal_ingestion_creates_events(db_session_with_tenant, sample_account, tenant_id):
    """Test that signal ingestion creates events"""
    actor_id = uuid.uuid4()
    
    # Create signal event
    await event_store.append_event(
        session=db_session_with_tenant,
        aggregate_id=sample_account.id,
        aggregate_type='account',
        event_type='signal.received',
        event_data={
            'id': str(uuid.uuid4()),
            'type': 'crm_stage_change',
            'source': 'salesforce',
            'timestamp': datetime.utcnow().isoformat(),
            'confidence_score': 1.0
        },
        actor_id=actor_id,
        tenant_id=tenant_id
    )
    
    # Verify event stored
    events = await event_store.get_events(db_session_with_tenant, sample_account.id)
    assert len(events) >= 1
    assert any(e.event_type == 'signal.received' for e in events)


@pytest.mark.asyncio
@pytest.mark.slow
async def test_intent_scoring_creates_events(db_session_with_tenant, sample_account, tenant_id):
    """Test that intent scoring creates events"""
    actor_id = uuid.uuid4()
    
    # Create intent scored event
    await event_store.append_event(
        session=db_session_with_tenant,
        aggregate_id=sample_account.id,
        aggregate_type='account',
        event_type='intent.scored',
        event_data={
            'score': 85.5,
            'scored_at': datetime.utcnow().isoformat(),
            'method': 'time_decay'
        },
        actor_id=actor_id,
        tenant_id=tenant_id
    )
    
    # Rebuild state to verify
    state = await event_store.rebuild_state(db_session_with_tenant, sample_account.id)
    assert state.get('intent_score') == 85.5


@pytest.mark.asyncio
@pytest.mark.slow
async def test_action_lifecycle_events(db_session_with_tenant, sample_account, tenant_id):
    """Test action proposal, approval, and execution events"""
    actor_id = uuid.uuid4()
    action_id = str(uuid.uuid4())
    
    # Action proposed
    await event_store.append_event(
        session=db_session_with_tenant,
        aggregate_id=sample_account.id,
        aggregate_type='account',
        event_type='action.proposed',
        event_data={
            'id': action_id,
            'type': 'send_email',
            'risk_level': 'medium',
            'proposed_at': datetime.utcnow().isoformat(),
            'proposed_by': str(actor_id)
        },
        actor_id=actor_id,
        tenant_id=tenant_id
    )
    
    # Action approved
    await event_store.append_event(
        session=db_session_with_tenant,
        aggregate_id=sample_account.id,
        aggregate_type='account',
        event_type='action.approved',
        event_data={
            'action_id': action_id,
            'approved_at': datetime.utcnow().isoformat(),
            'approved_by': str(actor_id)
        },
        actor_id=actor_id,
        tenant_id=tenant_id
    )
    
    # Action executed
    await event_store.append_event(
        session=db_session_with_tenant,
        aggregate_id=sample_account.id,
        aggregate_type='account',
        event_type='action.executed',
        event_data={
            'action_id': action_id,
            'executed_at': datetime.utcnow().isoformat()
        },
        actor_id=actor_id,
        tenant_id=tenant_id
    )
    
    # Rebuild state
    state = await event_store.rebuild_state(db_session_with_tenant, sample_account.id)
    
    # Verify action lifecycle
    actions = state.get('actions', [])
    assert len(actions) == 1
    assert actions[0]['id'] == action_id
    assert actions[0]['status'] == 'executed'


@pytest.mark.asyncio
async def test_consent_events(db_session_with_tenant, sample_account, tenant_id):
    """Test consent grant and revoke events"""
    actor_id = uuid.uuid4()
    email = "test@example.com"
    
    # Consent granted
    await event_store.append_event(
        session=db_session_with_tenant,
        aggregate_id=sample_account.id,
        aggregate_type='account',
        event_type='consent.granted',
        event_data={
            'email': email,
            'consent_type': 'marketing',
            'granted_at': datetime.utcnow().isoformat()
        },
        actor_id=actor_id,
        tenant_id=tenant_id
    )
    
    # Consent revoked
    await event_store.append_event(
        session=db_session_with_tenant,
        aggregate_id=sample_account.id,
        aggregate_type='account',
        event_type='consent.revoked',
        event_data={
            'email': email,
            'revoked_at': datetime.utcnow().isoformat()
        },
        actor_id=actor_id,
        tenant_id=tenant_id
    )
    
    # Rebuild state
    state = await event_store.rebuild_state(db_session_with_tenant, sample_account.id)
    
    # Verify consent lifecycle
    consents = state.get('consents', [])
    assert len(consents) == 1
    assert consents[0]['email'] == email
    assert consents[0]['revoked'] is True
