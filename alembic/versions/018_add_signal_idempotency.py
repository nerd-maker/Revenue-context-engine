"""
Alembic migration for signal idempotency (P1 reliability)
Adds idempotency_key column, backfills, and enforces uniqueness.
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add column
    op.add_column('signals', sa.Column('idempotency_key', sa.String(500), nullable=True))

    # Backfill existing data (generate keys from existing signals)
    op.execute("""
        UPDATE signals 
        SET idempotency_key = source || ':' || (payload->>'id') || ':' || timestamp::text
        WHERE idempotency_key IS NULL;
    """)

    # Make non-nullable
    op.alter_column('signals', 'idempotency_key', nullable=False)

    # Add unique constraint
    op.create_unique_constraint('uq_signal_idempotency', 'signals', ['idempotency_key'])
    op.create_index('idx_signal_idempotency', 'signals', ['idempotency_key'])

def downgrade():
    op.drop_constraint('uq_signal_idempotency', 'signals')
    op.drop_index('idx_signal_idempotency')
    op.drop_column('signals', 'idempotency_key')
