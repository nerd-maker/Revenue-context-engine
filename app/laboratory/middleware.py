from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import contextvars

DATABASE_URL = settings.DATABASE_URL.replace('postgresql+psycopg2', 'postgresql+asyncpg')

lab_engine = create_async_engine(DATABASE_URL + "?options=-csearch_path%3Dlaboratory", echo=True, future=True)
prod_engine = create_async_engine(DATABASE_URL, echo=True, future=True)

lab_session = sessionmaker(lab_engine, expire_on_commit=False, class_=AsyncSession)
prod_session = sessionmaker(prod_engine, expire_on_commit=False, class_=AsyncSession)

session_ctx = contextvars.ContextVar("session_ctx")


class LaboratoryRoutingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        mode = settings.EXECUTION_MODE
        if mode == "laboratory":
            session = lab_session()
        else:
            session = prod_session()
        request.state.db = session
        response = await call_next(request)
        await session.close()
        return response

# Expose session factories for test isolation
async def get_laboratory_session():
    async with lab_session() as session:
        yield session

async def get_production_session():
    async with prod_session() as session:
        yield session
