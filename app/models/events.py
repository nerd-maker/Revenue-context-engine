"""
Event Sourcing Models

Stores all state changes as immutable events.
Enables point-in-time reconstruction and compliance queries.
"""
from sqlalchemy import Column, String, BigInteger, DateTime, JSON, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
from datetime import datetime
import uuid


class Event(Base):
    """
    Immutable event store for all state changes.
    
    Implements event sourcing pattern with:
    - Optimistic locking via version numbers
    - Aggregate-based event streams
    - Point-in-time reconstruction capability
    """
    __tablename__ = 'events'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    aggregate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    aggregate_type = Column(String(50), nullable=False)  # 'account', 'action', 'signal'
    event_type = Column(String(100), nullable=False)     # 'account.created', 'signal.received'
    event_data = Column(JSON, nullable=False)
    version = Column(BigInteger, nullable=False)         # For optimistic locking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    actor_id = Column(UUID(as_uuid=True))
    actor_type = Column(String(50))  # 'user', 'agent', 'system'
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    __table_args__ = (
        # Composite index for aggregate event stream queries
        Index('idx_events_aggregate', 'aggregate_id', 'version'),
        
        # Index for event type filtering and time-range queries
        Index('idx_events_type_time', 'event_type', 'created_at'),
        
        # Index for tenant isolation
        Index('idx_events_tenant', 'tenant_id', 'created_at'),
        
        # Unique constraint for optimistic locking
        UniqueConstraint('aggregate_id', 'version', name='uq_event_version'),
    )
    
    def __repr__(self):
        return f"<Event {self.event_type} v{self.version} for {self.aggregate_type}:{self.aggregate_id}>"
