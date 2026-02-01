"""Create prompt templates table

Revision ID: 024_create_prompt_templates
Revises: 023_create_materialized_views
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '024_create_prompt_templates'
down_revision = '023_create_materialized_views'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create prompt_templates table for versioned LLM prompts.
    """
    op.create_table(
        'prompt_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('version', sa.Integer, nullable=False),
        sa.Column('template', sa.Text, nullable=False),
        sa.Column('active', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('metadata', sa.JSON, default={}),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
    )
    
    # Unique constraint for version control
    op.create_unique_constraint(
        'uq_prompt_name_version_tenant',
        'prompt_templates',
        ['name', 'version', 'tenant_id']
    )
    
    # Index for active prompt lookup
    op.create_index(
        'idx_prompt_active',
        'prompt_templates',
        ['name', 'active', 'tenant_id']
    )


def downgrade():
    """
    Drop prompt_templates table.
    """
    op.drop_table('prompt_templates')
