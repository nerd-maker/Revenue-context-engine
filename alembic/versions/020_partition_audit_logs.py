"""Partition audit_logs table by month

Revision ID: 020_partition_audit_logs
Revises: 019_complete_laboratory_schema
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from dateutil.relativedelta import relativedelta


# revision identifiers, used by Alembic.
revision = '020_partition_audit_logs'
down_revision = '019_complete_laboratory_schema'
branch_labels = None
depends_on = None


def upgrade():
    """
    Convert audit_logs table to partitioned table by month.
    Creates partitions for -3 to +3 months from current date.
    """
    # Rename existing table
    op.execute("ALTER TABLE audit_logs RENAME TO audit_logs_old")
    
    # Create partitioned table
    op.execute("""
        CREATE TABLE audit_logs (
            id VARCHAR(36) PRIMARY KEY,
            event_type VARCHAR(100) NOT NULL,
            actor_id VARCHAR(255),
            actor_type VARCHAR(50),
            resource_type VARCHAR(50),
            resource_id VARCHAR(36),
            action VARCHAR(100),
            payload JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            compliance_tag VARCHAR(50),
            tenant_id VARCHAR(36)
        ) PARTITION BY RANGE (created_at);
    """)
    
    # Create partitions for last 3 months + next 3 months
    current_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    for i in range(-3, 4):  # -3 to +3 months
        start_date = current_date + relativedelta(months=i)
        end_date = start_date + relativedelta(months=1)
        partition_name = f"audit_logs_{start_date.strftime('%Y_%m')}"
        
        op.execute(f"""
            CREATE TABLE {partition_name} PARTITION OF audit_logs
                FOR VALUES FROM ('{start_date.isoformat()}') TO ('{end_date.isoformat()}');
        """)
    
    # Copy data from old table
    op.execute("INSERT INTO audit_logs SELECT * FROM audit_logs_old")
    
    # Create indexes on partitioned table
    op.execute("""
        CREATE INDEX idx_audit_logs_resource 
        ON audit_logs (resource_type, resource_id, created_at DESC);
    """)
    
    op.execute("""
        CREATE INDEX idx_audit_logs_actor 
        ON audit_logs (actor_id, created_at DESC);
    """)
    
    op.execute("""
        CREATE INDEX idx_audit_logs_tenant 
        ON audit_logs (tenant_id, created_at DESC);
    """)
    
    op.execute("""
        CREATE INDEX idx_audit_metadata_gin 
        ON audit_logs USING GIN (payload jsonb_path_ops);
    """)
    
    # Drop old table
    op.execute("DROP TABLE audit_logs_old CASCADE")


def downgrade():
    """
    Revert to non-partitioned audit_logs table.
    """
    # Create backup of partitioned data
    op.execute("CREATE TABLE audit_logs_backup AS SELECT * FROM audit_logs")
    
    # Drop partitioned table
    op.execute("DROP TABLE audit_logs CASCADE")
    
    # Rename backup to original name
    op.execute("ALTER TABLE audit_logs_backup RENAME TO audit_logs")
    
    # Recreate original indexes
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])
