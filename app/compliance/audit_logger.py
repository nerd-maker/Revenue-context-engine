"""
Comprehensive Audit Logging System

Provides detailed audit logging for compliance and security monitoring.
Logs are stored in a partitioned database table and also sent to structured logging.
"""
from sqlalchemy import Column, String, DateTime, JSON, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base
import uuid
from datetime import datetime
import logging
import json

try:
    from fastapi import Request
except ImportError:
    Request = None

logger = logging.getLogger("audit")


class AuditLog(Base):
    """
    Audit log model for tracking all significant actions in the system.
    
    This table should be partitioned by timestamp for performance.
    See migration scripts for partitioning setup.
    """
    __tablename__ = 'audit_logs_v2'
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Actor information
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Action details
    action = Column(String(50), nullable=False, index=True)  # CREATE, READ, UPDATE, DELETE
    resource_type = Column(String(100), nullable=False, index=True)  # e.g., 'signal', 'account', 'user'
    resource_id = Column(String(255), nullable=False)
    
    # Change tracking
    changes = Column(JSON, nullable=True)  # {"before": {...}, "after": {...}}
    
    # Request metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)
    
    # Additional context
    extra_metadata = Column(JSON, nullable=True)  # Any additional context
    
    __table_args__ = (
        # Composite index for common queries
        Index('idx_audit_tenant_action_time', 'tenant_id', 'action', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )


async def log_audit_event(
    session: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: str,
    tenant_id: str = None,
    user_id: str = None,
    changes: dict = None,
    request: Request = None,
    extra_metadata: dict = None
):
    """
    Log an audit event to database and structured logging.
    
    Args:
        session: Database session
        action: Action type (CREATE, READ, UPDATE, DELETE)
        resource_type: Type of resource (e.g., 'signal', 'account', 'user')
        resource_id: ID of the resource
        tenant_id: Optional tenant ID
        user_id: Optional user ID
        changes: Optional dict with 'before' and 'after' states
        request: Optional FastAPI Request object (for IP and user agent)
        extra_metadata: Optional additional metadata
    
    Example Usage:
        # Log a signal creation
        await log_audit_event(
            session=db_session,
            action='CREATE',
            resource_type='signal',
            resource_id=str(signal.id),
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            request=request,
            extra_metadata={'source': 'salesforce', 'type': 'opportunity_created'}
        )
        
        # Log an account update with before/after
        await log_audit_event(
            session=db_session,
            action='UPDATE',
            resource_type='account',
            resource_id=str(account_id),
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            changes={
                'before': {'intent_score': 45.2},
                'after': {'intent_score': 78.5}
            },
            request=request
        )
        
        # Log a data deletion
        await log_audit_event(
            session=db_session,
            action='DELETE',
            resource_type='signal',
            resource_id=str(signal_id),
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            request=request,
            extra_metadata={'reason': 'gdpr_deletion_request'}
        )
    """
    # Extract IP address and user agent from request
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get('user-agent')
    
    # Create audit log entry
    audit_entry = AuditLog(
        timestamp=datetime.utcnow(),
        tenant_id=tenant_id,
        user_id=user_id,
        action=action.upper(),
        resource_type=resource_type,
        resource_id=str(resource_id),
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
        extra_metadata=extra_metadata
    )
    
    # Save to database
    session.add(audit_entry)
    await session.commit()
    
    # Also log to structured logging for real-time monitoring
    log_data = {
        'audit_id': str(audit_entry.id),
        'timestamp': audit_entry.timestamp.isoformat(),
        'tenant_id': str(tenant_id) if tenant_id else None,
        'user_id': str(user_id) if user_id else None,
        'action': action.upper(),
        'resource_type': resource_type,
        'resource_id': str(resource_id),
        'ip_address': ip_address,
        'has_changes': changes is not None,
        'extra_metadata': extra_metadata
    }
    
    logger.info(f"AUDIT: {action.upper()} {resource_type}/{resource_id}", extra=log_data)
    
    return audit_entry


async def query_audit_logs(
    session: AsyncSession,
    tenant_id: str = None,
    user_id: str = None,
    action: str = None,
    resource_type: str = None,
    resource_id: str = None,
    start_time: datetime = None,
    end_time: datetime = None,
    limit: int = 100
):
    """
    Query audit logs with filters.
    
    Args:
        session: Database session
        tenant_id: Filter by tenant ID
        user_id: Filter by user ID
        action: Filter by action type
        resource_type: Filter by resource type
        resource_id: Filter by resource ID
        start_time: Filter by start timestamp
        end_time: Filter by end timestamp
        limit: Maximum number of results (default: 100)
    
    Returns:
        List of AuditLog entries
    
    Example Usage:
        # Get all audit logs for a tenant in the last 24 hours
        from datetime import datetime, timedelta
        
        logs = await query_audit_logs(
            session=db_session,
            tenant_id=str(tenant_id),
            start_time=datetime.utcnow() - timedelta(days=1),
            limit=1000
        )
        
        # Get all DELETE actions for a specific resource
        logs = await query_audit_logs(
            session=db_session,
            action='DELETE',
            resource_type='signal',
            resource_id=str(signal_id)
        )
    """
    from sqlalchemy import select
    
    query = select(AuditLog)
    
    # Apply filters
    if tenant_id:
        query = query.where(AuditLog.tenant_id == tenant_id)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action.upper())
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.where(AuditLog.resource_id == str(resource_id))
    if start_time:
        query = query.where(AuditLog.timestamp >= start_time)
    if end_time:
        query = query.where(AuditLog.timestamp <= end_time)
    
    # Order by timestamp descending (most recent first)
    query = query.order_by(AuditLog.timestamp.desc())
    
    # Apply limit
    query = query.limit(limit)
    
    result = await session.execute(query)
    return result.scalars().all()


# Partitioning setup SQL (run in migration)
PARTITION_SETUP_SQL = """
-- Create partitioned audit logs table
-- This should be run in an Alembic migration

-- 1. Create parent partitioned table
CREATE TABLE IF NOT EXISTS audit_logs_v2 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL,
    tenant_id UUID,
    user_id UUID,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255) NOT NULL,
    changes JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    extra_metadata JSONB
) PARTITION BY RANGE (timestamp);

-- 2. Create indexes on parent table
CREATE INDEX IF NOT EXISTS idx_audit_tenant_action_time 
    ON audit_logs_v2 (tenant_id, action, timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_resource 
    ON audit_logs_v2 (resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
    ON audit_logs_v2 (timestamp);

-- 3. Create monthly partitions (example for 2026)
CREATE TABLE IF NOT EXISTS audit_logs_2026_01 
    PARTITION OF audit_logs_v2
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE IF NOT EXISTS audit_logs_2026_02 
    PARTITION OF audit_logs_v2
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- Add more partitions as needed...

-- 4. Create function to automatically create future partitions
CREATE OR REPLACE FUNCTION create_audit_log_partition()
RETURNS void AS $$
DECLARE
    partition_date DATE;
    partition_name TEXT;
    start_date TEXT;
    end_date TEXT;
BEGIN
    -- Create partition for next month
    partition_date := DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month');
    partition_name := 'audit_logs_' || TO_CHAR(partition_date, 'YYYY_MM');
    start_date := TO_CHAR(partition_date, 'YYYY-MM-DD');
    end_date := TO_CHAR(partition_date + INTERVAL '1 month', 'YYYY-MM-DD');
    
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_logs_v2 FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );
END;
$$ LANGUAGE plpgsql;

-- 5. Schedule automatic partition creation (requires pg_cron extension)
-- SELECT cron.schedule('create-audit-partitions', '0 0 1 * *', 'SELECT create_audit_log_partition()');
"""
