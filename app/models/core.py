from sqlalchemy import Column, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import Base

class Signal(Base):
    __tablename__ = 'signals'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idempotency_key = Column(String(500), nullable=False, unique=True)  # NEW: for deduplication
    account_id = Column(UUID(as_uuid=True), nullable=False)
    source = Column(String, nullable=False)
    type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    confidence_score = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    consent_id = Column(UUID(as_uuid=True), ForeignKey('consents.id'))
    audit_id = Column(UUID(as_uuid=True), ForeignKey('audit_logs.id'))

class AccountContext(Base):
    __tablename__ = 'account_contexts'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), nullable=False)
    signals = Column(JSON, nullable=False)
    intent_score = Column(Float, nullable=False)
    risk_flags = Column(JSON, nullable=False)
    next_best_action = Column(String, nullable=True)
    updated_at = Column(DateTime, nullable=False)

class Consent(Base):
    __tablename__ = 'consents'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(UUID(as_uuid=True), nullable=False)
    granted_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    scope = Column(String, nullable=False)
    source = Column(String, nullable=False)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String, nullable=False)
    actor_id = Column(UUID(as_uuid=True), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False)
    compliance_tag = Column(String, nullable=False)
