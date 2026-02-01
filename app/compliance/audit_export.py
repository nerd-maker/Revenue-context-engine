try:
    from fastapi import APIRouter, Request, HTTPException
except ImportError:
    APIRouter = Request = HTTPException = None
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.core import AuditLog
import uuid
import boto3
import os
from datetime import datetime, timedelta

router = APIRouter()

S3_BUCKET = os.getenv('AUDIT_LOGS_BUCKET', 'revenue-context-audit-logs')

@router.get('/audit/export')
async def export_audit_logs(request: Request):
    session: AsyncSession = request.state.db
    logs = await session.execute(select(AuditLog))
    data = [dict(row[0].__dict__) for row in logs.fetchall()]
    # Write to S3 and return signed URL
    s3 = boto3.client('s3')
    key = f"audit-exports/{uuid.uuid4()}.json"
    import json
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=json.dumps(data))
    url = s3.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': key}, ExpiresIn=3600)
    return {"url": url}
