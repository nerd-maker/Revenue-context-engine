from alembic import op
import sqlalchemy as sa

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'integrations',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('tenant_id', sa.String, nullable=False),
        sa.Column('provider', sa.String, nullable=False),
        sa.Column('org_id', sa.String, nullable=False),
        sa.Column('access_token', sa.String, nullable=False),
        sa.Column('refresh_token', sa.String, nullable=False),
        sa.Column('instance_url', sa.String, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('metadata', sa.JSON, nullable=True),
    )
    op.create_index('ix_integrations_tenant_id', 'integrations', ['tenant_id'])

def downgrade():
    op.drop_index('ix_integrations_tenant_id', table_name='integrations')
    op.drop_table('integrations')
