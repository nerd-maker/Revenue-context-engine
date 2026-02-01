
import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app.models.core import Signal
from sqlalchemy import select, text
import uuid
from datetime import datetime, timedelta
from app.core.database import AsyncSessionLocal

@pytest.mark.asyncio
async def test_tenant_isolation_enforced():
    """CRITICAL: Verify tenant A cannot see tenant B data"""
    tenant_a_id = uuid.uuid4()
    tenant_b_id = uuid.uuid4()

    # Create signal for tenant A
    async with get_session_with_tenant(tenant_a_id) as session:
        signal = Signal(
            id=uuid.uuid4(),
            tenant_id=tenant_a_id,
            account_id=uuid.uuid4(),
            source="test",
            type="web_visit",
            payload={},
            confidence_score=1.0,
            timestamp=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        session.add(signal)
        await session.commit()
        signal_id = signal.id

    # Try to read as tenant B
    async with get_session_with_tenant(tenant_b_id) as session:
        result = await session.execute(select(Signal))
        signals = result.scalars().all()
        assert len(signals) == 0, "RLS FAILED: Tenant B can see Tenant A data!"

    # Verify tenant A can still see own data
    async with get_session_with_tenant(tenant_a_id) as session:
        result = await session.execute(select(Signal).where(Signal.id == signal_id))
        signal = result.scalar_one()
        assert signal.tenant_id == tenant_a_id

from contextlib import asynccontextmanager

@asynccontextmanager
async def get_session_with_tenant(tenant_id: uuid.UUID):
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("SET LOCAL app.tenant_id = :tenant_id"),
            {"tenant_id": str(tenant_id)}
        )
        session.info["tenant_id"] = tenant_id
        yield session
