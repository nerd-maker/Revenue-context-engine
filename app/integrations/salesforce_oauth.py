try:
    from fastapi import APIRouter, Request, HTTPException
except ImportError:
    APIRouter = Request = HTTPException = None
from app.models.integration import Integration
from app.security.encryption import encryptor
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid
try:
    import httpx
except ImportError:
    httpx = None
from app.integrations.circuit_breaker import call_salesforce_api, CircuitBreakerError
import os

router = APIRouter()

SALESFORCE_CLIENT_ID = os.getenv('SALESFORCE_CLIENT_ID')
SALESFORCE_CLIENT_SECRET = os.getenv('SALESFORCE_CLIENT_SECRET')
SALESFORCE_REDIRECT_URI = os.getenv('SALESFORCE_REDIRECT_URI')

@router.get('/integrations/salesforce/authorize')
async def salesforce_authorize(request: Request):
    tenant_id = request.query_params.get('tenant_id')
    if not tenant_id:
        raise HTTPException(status_code=400, detail='Missing tenant_id')
    url = (
        f"https://login.salesforce.com/services/oauth2/authorize?response_type=code"
        f"&client_id={SALESFORCE_CLIENT_ID}"
        f"&redirect_uri={SALESFORCE_REDIRECT_URI}"
        f"&state={tenant_id}"
    )
    return {"auth_url": url}

@router.get('/integrations/salesforce/callback')
async def salesforce_callback(request: Request):
    code = request.query_params.get('code')
    state = request.query_params.get('state')  # tenant_id
    if not code or not state:
        raise HTTPException(status_code=400, detail='Missing code or state')
    try:
        data = await call_salesforce_api(
            url='https://login.salesforce.com/services/oauth2/token',
            method='POST',
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': SALESFORCE_CLIENT_ID,
                'client_secret': SALESFORCE_CLIENT_SECRET,
                'redirect_uri': SALESFORCE_REDIRECT_URI,
            }
        )
    except CircuitBreakerError:
        import logging
        logger = logging.getLogger("salesforce_oauth")
        logger.error("Salesforce API circuit breaker OPEN")
        raise HTTPException(
            status_code=503,
            detail="Salesforce API temporarily unavailable. Please try again in 60 seconds."
        )
    except httpx.HTTPStatusError as e:
        import logging
        logger = logging.getLogger("salesforce_oauth")
        logger.error(f"Salesforce OAuth error: {e}")
        raise HTTPException(status_code=400, detail='Salesforce OAuth failed')
    # Store tokens (should be encrypted in production)
    session: AsyncSession = request.state.db
    integration = Integration(
        id=str(uuid.uuid4()),
        tenant_id=state,
        provider='salesforce',
        org_id=data['id'],
        encrypted_access_token=encryptor.encrypt(data['access_token']),
        encrypted_refresh_token=encryptor.encrypt(data['refresh_token']),
        encryption_key_version=1,
        instance_url=data['instance_url'],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        metadata={}
    )
    session.add(integration)
    await session.commit()
    return {"status": "connected", "org_id": data['id']}