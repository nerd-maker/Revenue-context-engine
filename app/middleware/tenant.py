try:
    from fastapi import Request
except ImportError:
    Request = None
from starlette.middleware.base import BaseHTTPMiddleware
from app.auth.jwt import get_tenant_id_from_request
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import contextvars

DATABASE_URL = settings.DATABASE_URL.replace('postgresql+psycopg2', 'postgresql+asyncpg')

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
session_factory = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            tenant_id = get_tenant_id_from_request(request)
        except Exception:
            tenant_id = '00000000-0000-0000-0000-000000000000'  # fallback for public endpoints
        # Set tenant context for RLS
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(
                text("SET LOCAL app.tenant_id = :tenant_id"),
                {"tenant_id": str(tenant_id)}
            )
        request.state.tenant_id = tenant_id
        db_session = session_factory()
        db_session.info["tenant_id"] = tenant_id
        request.state.db = db_session
        response = await call_next(request)
        await request.state.db.close()
        return response
