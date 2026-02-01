"""
Pytest configuration and shared fixtures.

Provides reusable test fixtures for database sessions, tenant isolation, and mocking.
"""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.base import Base
import uuid


# Test database URL
TEST_DATABASE_URL = str(settings.DATABASE_URL).replace('/revenue_context', '/revenue_context_test')


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """Create database session for tests"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def tenant_id():
    """Generate unique tenant ID for test isolation"""
    return uuid.uuid4()


@pytest.fixture
async def db_session_with_tenant(test_engine, tenant_id):
    """Create database session with tenant context"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        # Set tenant context
        session.info['tenant_id'] = tenant_id
        yield session
        await session.rollback()


@pytest.fixture
def mock_llm_response():
    """Mock LLM API response"""
    return {
        "choices": [{
            "message": {
                "content": '{"subject": "Test Email", "body": "Test body", "reasoning": "Test reasoning", "confidence": 0.85}'
            }
        }],
        "usage": {
            "total_tokens": 250
        }
    }


@pytest.fixture
async def sample_account(db_session_with_tenant, tenant_id):
    """Create sample account for testing"""
    from app.models.core import Account
    
    account = Account(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="Test Account Inc",
        domain="testaccount.com",
        industry="SaaS"
    )
    
    db_session_with_tenant.add(account)
    await db_session_with_tenant.commit()
    await db_session_with_tenant.refresh(account)
    
    return account


@pytest.fixture
async def sample_signal(db_session_with_tenant, sample_account, tenant_id):
    """Create sample signal for testing"""
    from app.models.core import Signal
    from datetime import datetime, timedelta
    
    signal = Signal(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        account_id=sample_account.id,
        source="test",
        type="web_visit",
        payload={"page": "/pricing"},
        confidence_score=0.8,
        timestamp=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=90)
    )
    
    db_session_with_tenant.add(signal)
    await db_session_with_tenant.commit()
    await db_session_with_tenant.refresh(signal)
    
    return signal
