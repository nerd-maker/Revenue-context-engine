import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def assign_cohort(account_id, experiment_id, percent=5):
    h = int(hashlib.sha256(f"{account_id}-{experiment_id}".encode()).hexdigest(), 16)
    cohort = 'experiment' if (h % 100) < percent else 'control'
    return cohort

async def store_cohort(session: AsyncSession, experiment_id, account_id, cohort):
    await session.execute(
        """
        INSERT INTO laboratory.experiment_cohorts (id, experiment_id, account_id, cohort)
        VALUES (:id, :experiment_id, :account_id, :cohort)
        ON CONFLICT (experiment_id, account_id) DO NOTHING
        """,
        {
            "id": f"{experiment_id}-{account_id}",
            "experiment_id": experiment_id,
            "account_id": account_id,
            "cohort": cohort
        }
    )
    await session.commit()
