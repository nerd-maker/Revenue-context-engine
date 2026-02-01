from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

def create_db_engine(pool_size: int = 20):
    """
    Create async database engine with production-ready pooling.
    Pool sizing for multi-worker deployment:
    - Base pool: 20 connections (supports 8 workers with 2-3 connections each)
    - Max overflow: 30 (burst capacity for spikes)
    - Timeout: 30s (wait for connection)
    - Statement timeout: 60s (prevent runaway queries)
    
    Total capacity: 20 + 30 = 50 connections per instance
    With 8 workers: ~6 connections per worker max
    """
    database_url = settings.DATABASE_URL.replace('postgresql+psycopg2', 'postgresql+asyncpg')
    return create_async_engine(
        database_url,
        echo=(settings.ENV == 'development'),
        pool_size=pool_size,
        max_overflow=30,  # Increased from 20
        pool_timeout=30,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=3600,  # Recycle connections every hour
        connect_args={
            "server_settings": {
                "application_name": f"revenue_context_{settings.ENV}",
                "statement_timeout": "60000",  # 60s query timeout
            },
            "command_timeout": 60,
        }
    )

engine = create_db_engine()
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db():
    """Dependency for FastAPI routes"""
    async with AsyncSessionLocal() as session:
        yield session
