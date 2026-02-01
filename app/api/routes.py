try:
	from fastapi import APIRouter
except ImportError:
	APIRouter = None
from app.services.signal_ingestion import router as signal_router
from app.integrations.crm_webhook import router as crm_router
from app.integrations.salesforce_webhook import router as salesforce_router

api_router = APIRouter()
api_router.include_router(signal_router, prefix="/signals", tags=["signals"])
api_router.include_router(crm_router, prefix="/integrations", tags=["integrations"])
api_router.include_router(salesforce_router, prefix="/integrations", tags=["integrations"])
