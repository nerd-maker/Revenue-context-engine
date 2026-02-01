"""Add performance indexes for query optimization

Revision ID: 021_add_performance_indexes
Revises: 020_partition_audit_logs
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '021_add_performance_indexes'
down_revision = '020_partition_audit_logs'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add composite and specialized indexes for common query patterns.
    Includes GIN indexes for JSONB columns.
    """
    # === SIGNALS TABLE INDEXES ===
    
    # Composite index for account + timestamp (context calculation queries)
    op.create_index(
        'idx_signals_account_timestamp',
        'signals',
        ['account_id', sa.text('timestamp DESC'), 'expires_at']
    )
    
    # Composite index for tenant + account (multi-tenant queries)
    op.create_index(
        'idx_signals_tenant_account',
        'signals',
        ['tenant_id', 'account_id', sa.text('timestamp DESC')]
    )
    
    # Composite index for type + timestamp (analytics queries)
    op.create_index(
        'idx_signals_type_timestamp',
        'signals',
        ['type', sa.text('timestamp DESC')]
    )
    
    # GIN index for JSONB payload queries
    op.execute("""
        CREATE INDEX idx_signals_payload_gin 
        ON signals USING GIN (payload jsonb_path_ops);
    """)
    
    # === ACTIONS TABLE INDEXES ===
    
    # Partial index for pending approval queue
    op.execute("""
        CREATE INDEX idx_actions_pending_approval 
        ON actions (status, risk_level, proposed_at DESC)
        WHERE status = 'proposed';
    """)
    
    # === ACCOUNT CONTEXTS TABLE INDEXES ===
    
    # Composite index for intent score leaderboard queries
    op.create_index(
        'idx_account_contexts_intent',
        'account_contexts',
        ['tenant_id', sa.text('intent_score DESC'), sa.text('last_signal_at DESC')]
    )
    
    # GIN index for signals JSONB array
    op.execute("""
        CREATE INDEX idx_account_contexts_signals_gin
        ON account_contexts USING GIN (signals jsonb_path_ops);
    """)
    
    # === CONSENTS TABLE INDEXES ===
    
    # Composite index for email lookup
    op.create_index(
        'idx_consents_email_status',
        'consents',
        ['subject_id', 'status', 'revoked_at']
    )


def downgrade():
    """
    Remove all performance indexes.
    """
    # Signals indexes
    op.drop_index('idx_signals_account_timestamp', table_name='signals')
    op.drop_index('idx_signals_tenant_account', table_name='signals')
    op.drop_index('idx_signals_type_timestamp', table_name='signals')
    op.drop_index('idx_signals_payload_gin', table_name='signals')
    
    # Actions indexes
    op.drop_index('idx_actions_pending_approval', table_name='actions')
    
    # Account contexts indexes
    op.drop_index('idx_account_contexts_intent', table_name='account_contexts')
    op.drop_index('idx_account_contexts_signals_gin', table_name='account_contexts')
    
    # Consents indexes
    op.drop_index('idx_consents_email_status', table_name='consents')
