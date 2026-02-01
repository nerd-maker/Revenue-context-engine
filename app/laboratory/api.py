try:
    from fastapi import APIRouter, HTTPException, status, Request
except ImportError:
    APIRouter = HTTPException = status = Request = None
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import uuid
from app.core.config import settings
from sqlalchemy import text

router = APIRouter()

@router.post("/laboratory/experiments")
async def create_experiment(request: Request):
    data = await request.json()
    name = data.get("name")
    description = data.get("description")
    agent_config = data.get("agent_config")
    signal_filters = data.get("signal_filters")
    if not name or not agent_config:
        raise HTTPException(status_code=400, detail="Missing required fields")
    session: AsyncSession = request.state.db
    experiment_id = str(uuid.uuid4())
    # Store experiment config in laboratory.actions as event_type='experiment_config'
    await session.execute(
        """
        INSERT INTO laboratory.actions (id, event_type, actor_id, payload, created_at, compliance_tag)
        VALUES (:id, :event_type, :actor_id, :payload, :created_at, :compliance_tag)
        """,
        {
            "id": experiment_id,
            "event_type": "experiment_config",
            "actor_id": "lab_api",
            "payload": {"name": name, "description": description, "agent_config": agent_config, "signal_filters": signal_filters},
            "created_at": datetime.utcnow(),
            "compliance_tag": "lab"
        }
    )
    await session.commit()
    return {"experiment_id": experiment_id}

@router.post("/laboratory/experiments/{id}/run")
async def run_experiment(id: str, request: Request):
    session: AsyncSession = request.state.db
    # Replay last N days of production signals through lab agents
    # For demo, just copy signals from prod to lab schema
    days = int(settings.LAB_SIGNAL_REPLAY_DAYS)
    since = datetime.utcnow() - timedelta(days=days)
    # Use parameterized query to prevent SQL injection
    prod_signals = await session.execute(
        text("SELECT * FROM public.signals WHERE timestamp >= :since"), 
        {"since": since}
    )
    prod_signals = prod_signals.fetchall()
    for row in prod_signals:
        await session.execute(
            """
            INSERT INTO laboratory.signals (id, account_id, source, type, payload, confidence_score, timestamp, expires_at, consent_id, audit_id)
            VALUES (:id, :account_id, :source, :type, :payload, :confidence_score, :timestamp, :expires_at, :consent_id, :audit_id)
            ON CONFLICT (id) DO NOTHING
            """,
            dict(row)
        )
    await session.commit()
    # Simulate lab agent run (could trigger async worker)
    return {"experiment_id": id, "signals_replayed": len(prod_signals)}

@router.get("/laboratory/experiments/{id}/compare")
async def compare_experiment(id: str, request: Request):
    session: AsyncSession = request.state.db
    # Compare lab vs prod intent scores for accounts
    # Use parameterized queries to prevent SQL injection
    prod_ctx = await session.execute(
        text("SELECT account_id, intent_score FROM public.account_contexts")
    )
    lab_ctx = await session.execute(
        text("SELECT account_id, intent_score FROM laboratory.account_contexts")
    )
    prod_map = {row[0]: row[1] for row in prod_ctx.fetchall()}
    lab_map = {row[0]: row[1] for row in lab_ctx.fetchall()}
    report = []
    for acc, lab_score in lab_map.items():
        prod_score = prod_map.get(acc)
        report.append({"account_id": acc, "prod": prod_score, "lab": lab_score, "delta": (lab_score - prod_score) if prod_score is not None else None})
    return {"experiment_id": id, "comparison": report}

@router.post("/laboratory/experiments/{id}/promote")
async def promote_experiment(id: str, request: Request):
    session: AsyncSession = request.state.db
    # Validate, require approval, copy config to prod (simplified)
    # For demo, just log promotion
    await session.execute(
        """
        INSERT INTO public.audit_logs (id, event_type, actor_id, payload, created_at, compliance_tag)
        VALUES (:id, :event_type, :actor_id, :payload, :created_at, :compliance_tag)
        """,
        {
            "id": str(uuid.uuid4()),
            "event_type": "lab_promoted",
            "actor_id": "lab_api",
            "payload": {"experiment_id": id},
            "created_at": datetime.utcnow(),
            "compliance_tag": "prod"
        }
    )
    await session.commit()
    return {"experiment_id": id, "status": "promoted"}
