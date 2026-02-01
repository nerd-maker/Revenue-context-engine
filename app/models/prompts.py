"""
Prompt Template Models

Version-controlled LLM prompts stored in database.
Enables prompt governance, A/B testing, and audit trails.
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Text, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
from datetime import datetime
import uuid


class PromptTemplate(Base):
    """
    Versioned LLM prompt templates.
    
    Features:
    - Version control for prompts
    - A/B testing support via metadata
    - Audit trail of prompt changes
    - Tenant isolation
    """
    __tablename__ = 'prompt_templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)  # 'email_generation', 'intent_scoring'
    version = Column(Integer, nullable=False)
    template = Column(Text, nullable=False)
    active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    metadata = Column(JSON, default={})  # For A/B test tracking, performance metrics
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    __table_args__ = (
        # Ensure unique version per prompt per tenant
        UniqueConstraint('name', 'version', 'tenant_id', name='uq_prompt_name_version_tenant'),
        
        # Index for active prompt lookup (most common query)
        Index('idx_prompt_active', 'name', 'active', 'tenant_id')
    )
    
    def __repr__(self):
        return f"<PromptTemplate {self.name} v{self.version} {'[ACTIVE]' if self.active else ''}>"
