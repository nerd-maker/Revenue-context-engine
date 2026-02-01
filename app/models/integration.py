from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from .base import Base

class Integration(Base):
    __tablename__ = 'integrations'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    provider = Column(String, nullable=False)  # 'salesforce', etc.
    org_id = Column(String, nullable=False)
    encrypted_access_token = Column(String, nullable=False)
    encrypted_refresh_token = Column(String, nullable=False)
    encryption_key_version = Column(sa.Integer, default=1)
    instance_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_metadata = Column(JSON, nullable=True)
