"""Create event store table

Revision ID: 022_create_event_store
Revises: 021_add_performance_indexes
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '022_create_event_store'
down_revision = '021_add_performance_indexes'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create events table for event sourcing.
    Stores all state changes as immutable events.
    """
    op.create_table(
        'events',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('aggregate_id', UUID(as_uuid=True), nullable=False),
        sa.Column('aggregate_type', sa.String(50), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_data', sa.JSON, nullable=False),
        sa.Column('version', sa.BigInteger, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('actor_id', UUID(as_uuid=True)),
        sa.Column('actor_type', sa.String(50)),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
    )
    
    # Composite index for aggregate event stream queries
    op.create_index(
        'idx_events_aggregate',
        'events',
        ['aggregate_id', 'version']
    )
    
    # Index for event type filtering and time-range queries
    op.create_index(
        'idx_events_type_time',
        'events',
        ['event_type', 'created_at']
    )
    
    # Index for tenant isolation
    op.create_index(
        'idx_events_tenant',
        'events',
        ['tenant_id', 'created_at']
    )
    
    # Unique constraint for optimistic locking
    op.create_unique_constraint(
        'uq_event_version',
        'events',
        ['aggregate_id', 'version']
    )


def downgrade():
    """
    Drop events table.
    """
    op.drop_table('events')
