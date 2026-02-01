

import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from sqlalchemy import text
from app.models.core import Signal
from app.security.encryption import encryptor
from app.core.database import AsyncSessionLocal

@pytest.mark.asyncio
async def test_sqlalchemy_orm_prevents_injection():
    malicious_id = "foo'; DROP TABLE signals; --"
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1
        result = await session.execute(Signal.__table__.select().where(Signal.account_id == malicious_id))
        assert result.fetchall() == []

def test_token_encryption_roundtrip():
    token = "super-secret-token"
    encrypted = encryptor.encrypt(token)
    decrypted = encryptor.decrypt(encrypted)
    assert decrypted == token
