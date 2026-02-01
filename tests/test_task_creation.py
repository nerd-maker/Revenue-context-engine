import pytest
import asyncio
from app.services.orchestration_engine import create_task_in_salesforce

@pytest.mark.asyncio
async def test_create_task_in_salesforce():
    result = await create_task_in_salesforce("A1", "Test Account")
    assert result["status"] == "created"
    assert "task_id" in result
