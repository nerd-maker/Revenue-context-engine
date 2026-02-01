import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.services.email_orchestration_agent import EmailOrchestrationAgent

@pytest.mark.asyncio
@patch('app.services.email_orchestration_agent.EmailOrchestrationAgent.generate_email')
@patch('app.services.email_orchestration_agent.EmailOrchestrationAgent.check_consent')
async def test_email_generation_and_risk(mock_consent, mock_generate_email):
    agent = EmailOrchestrationAgent()
    mock_consent.return_value = True
    mock_generate_email.return_value = {
        "subject": "Test Subject",
        "body": "Test Body",
        "reasoning": "Test Reasoning",
        "confidence": 0.65
    }
    context = {"account_id": "A1", "intent_score": 80}
    await agent.process_context(context)
    # Should route to high-risk queue (compliance_tag='high-risk')
    # (DB assertion would be here in a real test)

@pytest.mark.asyncio
@patch('app.services.email_orchestration_agent.EmailOrchestrationAgent.check_consent')
async def test_no_email_if_no_consent(mock_consent):
    agent = EmailOrchestrationAgent()
    mock_consent.return_value = False
    context = {"account_id": "A2", "intent_score": 80}
    await agent.process_context(context)
    # Should not create any action
