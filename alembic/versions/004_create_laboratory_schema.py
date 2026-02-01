from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS laboratory")
    op.create_table(
        'signals',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('account_id', sa.String, nullable=False),
        sa.Column('source', sa.String, nullable=False),
        sa.Column('type', sa.String, nullable=False),
        sa.Column('payload', sa.JSON, nullable=False),
        sa.Column('confidence_score', sa.Float, nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('consent_id', sa.String, nullable=True),
        sa.Column('audit_id', sa.String, nullable=True),
        schema='laboratory'
    )
    op.create_table(
        'account_contexts',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('account_id', sa.String, nullable=False),
        sa.Column('signals', sa.JSON, nullable=False),
        sa.Column('intent_score', sa.Float, nullable=False),
        sa.Column('context_quality_score', sa.Float, nullable=True),
        sa.Column('risk_flags', sa.JSON, nullable=False),
        sa.Column('next_best_action', sa.String, nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        schema='laboratory'
    )
    op.create_table(
        'actions',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('event_type', sa.String, nullable=False),
        sa.Column('actor_id', sa.String, nullable=False),
        sa.Column('payload', sa.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('compliance_tag', sa.String, nullable=False),
        schema='laboratory'
    )
    op.create_table(
        'experiment_cohorts',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('experiment_id', sa.String, nullable=False),
        sa.Column('account_id', sa.String, nullable=False),
        sa.Column('cohort', sa.String, nullable=False),
        schema='laboratory'
    )

def downgrade():
    op.drop_table('signals', schema='laboratory')
    op.drop_table('account_contexts', schema='laboratory')
    op.drop_table('actions', schema='laboratory')
    op.drop_table('experiment_cohorts', schema='laboratory')
    op.execute("DROP SCHEMA IF EXISTS laboratory CASCADE")
