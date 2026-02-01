try:
    import httpx
except ImportError:
    httpx = None
from app.models.integration import Integration
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid
import os
from sqlalchemy import text

async def create_salesforce_task(session: AsyncSession, tenant_id: str, account_external_id: str, subject: str, description: str):
    # Lookup integration for tenant using parameterized query
    # Parameterized queries prevent SQL injection by properly escaping user input
    result = await session.execute(
        text("SELECT * FROM integrations WHERE tenant_id = :tenant_id AND provider = 'salesforce'"),
        {"tenant_id": tenant_id}
    )
    integration = result.first()
    if not integration:
        raise Exception('Salesforce integration not found for tenant')
    access_token = integration[0].access_token
    instance_url = integration[0].instance_url
    # Map internal account_external_id to Salesforce AccountId
    # (Assume mapping is stored in integration.metadata or tenant config)
    account_id = account_external_id  # TODO: lookup mapping
    url = f"{instance_url}/services/data/v58.0/sobjects/Task"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "Subject": subject,
        "Description": description,
        "WhatId": account_id,
        "Status": "Not Started"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=data)
        if resp.status_code == 401:
            # TODO: Refresh token and retry
            raise Exception('Salesforce token expired')
        if resp.status_code not in (200, 201):
            raise Exception(f'Salesforce Task creation failed: {resp.text}')
        return resp.json()
