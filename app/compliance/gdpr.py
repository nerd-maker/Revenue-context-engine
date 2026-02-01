try:
    from fastapi import APIRouter, Request, HTTPException
except ImportError:
    APIRouter = Request = HTTPException = None
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.core import Signal, AccountContext

router = APIRouter()

@router.get('/accounts/{account_id}/export')
async def export_account(account_id: str, request: Request):
    session: AsyncSession = request.state.db
    signals = await session.execute(select(Signal).where(Signal.account_id == account_id))
    contexts = await session.execute(select(AccountContext).where(AccountContext.account_id == account_id))
    return {
        "account_id": account_id,
        "signals": [dict(row[0].__dict__) for row in signals.fetchall()],
        "contexts": [dict(row[0].__dict__) for row in contexts.fetchall()]
    }
