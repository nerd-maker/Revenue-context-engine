try:
    from fastapi import APIRouter, HTTPException, status, Request
except ImportError:
    APIRouter = HTTPException = status = Request = None
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.core import AuditLog
from datetime import datetime
from typing import List

router = APIRouter()

@router.get("/actions/pending", response_model=List[dict])
async def list_pending_actions(request: Request, risk_level: str = None, account: str = None, date_from: str = None, date_to: str = None):
    session: AsyncSession = request.state.db
    query = select(AuditLog).where(AuditLog.event_type == "send_email", AuditLog.compliance_tag == "proposed")
    # Filtering logic (risk_level, account, date range)
    # For MVP, filter in Python after fetch
    result = await session.execute(query)
    actions = [row[0] for row in result.fetchall()]
    filtered = []
    for action in actions:
        payload = action.payload or {}
        if risk_level and payload.get("risk_level") != risk_level:
            continue
        if account and payload.get("account_id") != account:
            continue
        if date_from or date_to:
            ts = action.created_at
            if date_from and ts < datetime.fromisoformat(date_from):
                continue
            if date_to and ts > datetime.fromisoformat(date_to):
                continue
        filtered.append({
            "id": action.id,
            "account_id": payload.get("account_id"),
            "account_name": payload.get("account_name"),
            "signals": payload.get("signals"),
            "intent_score": payload.get("intent_score"),
            "email": payload.get("email"),
            "reasoning": payload.get("reasoning"),
            "created_at": action.created_at,
            "risk_level": payload.get("risk_level", "medium"),
            "status": action.compliance_tag
        })
    return filtered

@router.post("/actions/{id}/approve")
async def approve_action(id: str, request: Request):
    session: AsyncSession = request.state.db
    result = await session.execute(select(AuditLog).where(AuditLog.id == id))
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    # For MVP, assume user is authorized
    action.compliance_tag = "approved"
    action.payload["approved_by"] = "user1"
    action.payload["approved_at"] = datetime.utcnow().isoformat()
    await session.commit()
    # Publish actions.approved event (mocked)
    return {"status": "approved", "id": id}

@router.post("/actions/{id}/reject")
async def reject_action(id: str, request: Request):
    data = await request.json()
    reason = data.get("reason", "No reason provided")
    session: AsyncSession = request.state.db
    result = await session.execute(select(AuditLog).where(AuditLog.id == id))
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    action.compliance_tag = "rejected"
    action.payload["rejection_reason"] = reason
    await session.commit()
    return {"status": "rejected", "id": id, "reason": reason}
