from alembic import op
import sqlalchemy as sa
import uuid

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'signals',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('idempotency_key', sa.String(500), nullable=False, unique=True),
        sa.Column('account_id', sa.String, nullable=False),
        sa.Column('source', sa.String, nullable=False),
        sa.Column('type', sa.String, nullable=False),
        sa.Column('payload', sa.JSON, nullable=False),
        sa.Column('confidence_score', sa.Float, nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('consent_id', sa.String, nullable=True),
        sa.Column('audit_id', sa.String, nullable=True),
    )
    op.create_table(
        'account_contexts',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('account_id', sa.String, nullable=False),
        sa.Column('signals', sa.JSON, nullable=False),
        sa.Column('intent_score', sa.Float, nullable=False),
        sa.Column('risk_flags', sa.JSON, nullable=False),
        sa.Column('next_best_action', sa.String, nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_table(
        'consents',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('subject_id', sa.String, nullable=False),
        sa.Column('granted_at', sa.DateTime, nullable=False),
        sa.Column('revoked_at', sa.DateTime, nullable=True),
        sa.Column('scope', sa.String, nullable=False),
        sa.Column('source', sa.String, nullable=False),
    )
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('event_type', sa.String, nullable=False),
        sa.Column('actor_id', sa.String, nullable=False),
        sa.Column('payload', sa.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('compliance_tag', sa.String, nullable=False),
    )

def downgrade():
    op.drop_table('signals')
    op.drop_table('account_contexts')
    op.drop_table('consents')
    op.drop_table('audit_logs')
