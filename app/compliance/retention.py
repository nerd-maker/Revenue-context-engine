import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

async def delete_expired_signals(session: AsyncSession, retention_days: int):
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    await session.execute(
        "DELETE FROM signals WHERE timestamp < :cutoff",
        {"cutoff": cutoff}
    )
    await session.commit()
