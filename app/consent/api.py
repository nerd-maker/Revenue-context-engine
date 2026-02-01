try:
    from fastapi import APIRouter, HTTPException, status, Request
except ImportError:
    APIRouter = HTTPException = status = Request = None
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.core import Consent
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/consent")
async def create_consent(request: Request):
    data = await request.json()
    email = data.get("email")
    consent_type = data.get("consent_type")
    if not email or not consent_type or consent_type not in ["marketing", "transactional"]:
        raise HTTPException(status_code=400, detail="Invalid input")
    session: AsyncSession = request.state.db
    consent = Consent(
        id=str(uuid.uuid4()),
        subject_id=email,
        granted_at=datetime.utcnow(),
        revoked_at=None,
        scope=consent_type,
        source="api"
    )
    session.add(consent)
    await session.commit()
    return {"status": "granted", "email": email, "consent_type": consent_type}

@router.get("/consent/{email}")
async def get_consent(email: str, request: Request):
    session: AsyncSession = request.state.db
    result = await session.execute(select(Consent).where(Consent.subject_id == email, Consent.revoked_at == None))
    consent = result.scalar_one_or_none()
    if not consent:
        return {"status": "revoked", "email": email}
    return {"status": "granted", "email": email, "consent_type": consent.scope}

@router.delete("/consent/{email}")
async def revoke_consent(email: str, request: Request):
    session: AsyncSession = request.state.db
    result = await session.execute(select(Consent).where(Consent.subject_id == email, Consent.revoked_at == None))
    consent = result.scalar_one_or_none()
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    consent.revoked_at = datetime.utcnow()
    await session.commit()
    # Publish consent.revoked event (future)
    return {"status": "revoked", "email": email}
