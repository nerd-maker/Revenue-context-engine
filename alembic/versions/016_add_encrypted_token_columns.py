from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add new encrypted columns
    op.add_column('integrations', sa.Column('encrypted_access_token', sa.Text))
    op.add_column('integrations', sa.Column('encrypted_refresh_token', sa.Text))
    op.add_column('integrations', sa.Column('encryption_key_version', sa.Integer, default=1))
    # TODO: Manually migrate existing tokens (one-time script)
    # Then drop old columns
    op.drop_column('integrations', 'access_token')
    op.drop_column('integrations', 'refresh_token')

def downgrade():
    op.add_column('integrations', sa.Column('access_token', sa.String, nullable=False))
    op.add_column('integrations', sa.Column('refresh_token', sa.String, nullable=False))
    op.drop_column('integrations', 'encrypted_access_token')
    op.drop_column('integrations', 'encrypted_refresh_token')
    op.drop_column('integrations', 'encryption_key_version')
