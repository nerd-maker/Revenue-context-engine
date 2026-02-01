"""
Event Store Service

Implements event sourcing pattern for immutable audit trail.
Supports point-in-time state reconstruction and event replay.
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.events import Event
from datetime import datetime
from uuid import UUID
import logging

logger = logging.getLogger("event_store")


class EventStore:
    """
    Event Sourcing implementation.
    Stores all state changes as immutable events.
    """
    
    async def append_event(
        self,
        session: AsyncSession,
        aggregate_id: UUID,
        aggregate_type: str,
        event_type: str,
        event_data: dict,
        actor_id: UUID,
        actor_type: str = 'system',
        tenant_id: UUID = None
    ) -> Event:
        """
        Append event to event store.
        Implements optimistic locking with version numbers.
        
        Args:
            session: Database session
            aggregate_id: ID of the aggregate (account, action, etc.)
            aggregate_type: Type of aggregate ('account', 'action', 'signal')
            event_type: Event type ('account.created', 'signal.received')
            event_data: Event payload
            actor_id: ID of actor causing the event
            actor_type: Type of actor ('user', 'agent', 'system')
            tenant_id: Tenant ID for multi-tenancy
            
        Returns:
            Created Event instance
        """
        # Get current version for optimistic locking
        result = await session.execute(
            select(func.max(Event.version))
            .where(Event.aggregate_id == aggregate_id)
        )
        current_version = result.scalar() or 0
        
        # Get tenant_id from session if not provided
        if tenant_id is None:
            tenant_id = session.info.get('tenant_id')
        
        # Create new event
        event = Event(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            event_type=event_type,
            event_data=event_data,
            version=current_version + 1,
            actor_id=actor_id,
            actor_type=actor_type,
            tenant_id=tenant_id,
            created_at=datetime.utcnow()
        )
        
        session.add(event)
        await session.commit()
        await session.refresh(event)  # CRITICAL: Refresh to prevent detached instance errors
        
        logger.info(
            f"Appended event: {event_type} for {aggregate_type}:{aggregate_id} "
            f"(v{event.version})"
        )
        return event
    
    async def get_events(
        self,
        session: AsyncSession,
        aggregate_id: UUID,
        from_version: int = 0,
        up_to_timestamp: datetime = None
    ) -> list[Event]:
        """
        Get events for an aggregate.
        
        Args:
            session: Database session
            aggregate_id: Aggregate ID
            from_version: Start from this version (exclusive)
            up_to_timestamp: Get events up to this timestamp (inclusive)
            
        Returns:
            List of events ordered by version
        """
        query = (
            select(Event)
            .where(Event.aggregate_id == aggregate_id)
            .where(Event.version > from_version)
            .order_by(Event.version)
        )
        
        if up_to_timestamp:
            query = query.where(Event.created_at <= up_to_timestamp)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def rebuild_state(
        self,
        session: AsyncSession,
        aggregate_id: UUID,
        up_to_timestamp: datetime = None
    ) -> dict:
        """
        Rebuild aggregate state from events.
        Used for compliance queries: "What was the state at 2026-01-15?"
        
        Args:
            session: Database session
            aggregate_id: Aggregate ID
            up_to_timestamp: Reconstruct state up to this timestamp
            
        Returns:
            Reconstructed state dictionary
        """
        events = await self.get_events(
            session,
            aggregate_id,
            up_to_timestamp=up_to_timestamp
        )
        
        state = {}
        for event in events:
            state = self._apply_event(state, event)
        
        logger.info(f"Rebuilt state for {aggregate_id}: {len(events)} events")
        return state
    
    def _apply_event(self, state: dict, event: Event) -> dict:
        """
        Apply event to state.
        Implements domain logic for state transitions.
        
        Args:
            state: Current state
            event: Event to apply
            
        Returns:
            Updated state
        """
        event_type = event.event_type
        data = event.event_data
        
        if event_type == 'account.created':
            state.update({
                'id': str(event.aggregate_id),
                'name': data.get('name'),
                'domain': data.get('domain'),
                'industry': data.get('industry'),
                'created_at': data.get('created_at'),
            })
        
        elif event_type == 'signal.received':
            state.setdefault('signals', []).append({
                'id': data.get('id'),
                'type': data.get('type'),
                'source': data.get('source'),
                'timestamp': data.get('timestamp'),
                'confidence_score': data.get('confidence_score'),
            })
        
        elif event_type == 'intent.scored':
            state['intent_score'] = data.get('score')
            state['intent_scored_at'] = data.get('scored_at')
            state['intent_calculation_method'] = data.get('method', 'time_decay')
        
        elif event_type == 'action.proposed':
            state.setdefault('actions', []).append({
                'id': data.get('id'),
                'type': data.get('type'),
                'status': 'proposed',
                'risk_level': data.get('risk_level'),
                'proposed_at': data.get('proposed_at'),
                'proposed_by': data.get('proposed_by'),
            })
        
        elif event_type == 'action.approved':
            # Update action status
            for action in state.get('actions', []):
                if action['id'] == data.get('action_id'):
                    action['status'] = 'approved'
                    action['approved_at'] = data.get('approved_at')
                    action['approved_by'] = data.get('approved_by')
        
        elif event_type == 'action.rejected':
            # Update action status
            for action in state.get('actions', []):
                if action['id'] == data.get('action_id'):
                    action['status'] = 'rejected'
                    action['rejected_at'] = data.get('rejected_at')
                    action['rejected_by'] = data.get('rejected_by')
                    action['rejection_reason'] = data.get('reason')
        
        elif event_type == 'action.executed':
            # Update action status
            for action in state.get('actions', []):
                if action['id'] == data.get('action_id'):
                    action['status'] = 'executed'
                    action['executed_at'] = data.get('executed_at')
        
        elif event_type == 'consent.granted':
            state.setdefault('consents', []).append({
                'email': data.get('email'),
                'type': data.get('consent_type'),
                'granted_at': data.get('granted_at'),
                'revoked': False
            })
        
        elif event_type == 'consent.revoked':
            # Mark consent as revoked
            for consent in state.get('consents', []):
                if consent['email'] == data.get('email'):
                    consent['revoked'] = True
                    consent['revoked_at'] = data.get('revoked_at')
        
        elif event_type == 'context.enriched':
            state.setdefault('enrichments', []).append({
                'provider': data.get('provider'),
                'enriched_at': data.get('enriched_at'),
                'fields_added': data.get('fields_added', []),
                'cost': data.get('cost'),
            })
        
        return state


# Global event store instance
event_store = EventStore()


# Usage example:
# await event_store.append_event(
#     session=session,
#     aggregate_id=account_id,
#     aggregate_type='account',
#     event_type='signal.received',
#     event_data={'id': str(signal.id), 'type': signal.type, ...},
#     actor_id=user_id,
#     actor_type='system'
# )
