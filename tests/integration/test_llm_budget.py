"""
LLM Budget Control Integration Tests

Tests budget enforcement and cost tracking.
"""
import pytest
import uuid
from app.services.llm_budget import llm_budget, BudgetExceededError


@pytest.mark.asyncio
async def test_budget_check():
    """Test budget availability check"""
    tenant_id = str(uuid.uuid4())
    
    # Should have budget initially
    has_budget = await llm_budget.check_budget(tenant_id)
    assert has_budget is True


@pytest.mark.asyncio
async def test_record_cost():
    """Test cost recording"""
    tenant_id = str(uuid.uuid4())
    
    # Record cost
    await llm_budget.record_cost(10.50, tenant_id)
    
    # Check spend
    spend = await llm_budget.get_current_spend(tenant_id)
    assert spend == 10.50
    
    # Check remaining
    remaining = await llm_budget.get_remaining_budget(tenant_id)
    assert remaining == llm_budget.daily_budget - 10.50


@pytest.mark.asyncio
async def test_budget_exceeded():
    """Test budget enforcement"""
    tenant_id = str(uuid.uuid4())
    
    # Exhaust budget
    await llm_budget.record_cost(llm_budget.daily_budget + 1, tenant_id)
    
    # Should fail budget check
    has_budget = await llm_budget.check_budget(tenant_id)
    assert has_budget is False


@pytest.mark.asyncio
async def test_calculate_cost():
    """Test token-based cost calculation"""
    # GPT-4: $0.03 per 1K tokens
    cost_gpt4 = llm_budget.calculate_cost(1000, 'gpt-4')
    assert cost_gpt4 == 0.03
    
    # GPT-3.5: $0.002 per 1K tokens
    cost_gpt35 = llm_budget.calculate_cost(1000, 'gpt-3.5-turbo')
    assert cost_gpt35 == 0.002
    
    # 500 tokens
    cost_500 = llm_budget.calculate_cost(500, 'gpt-4')
    assert cost_500 == 0.015


@pytest.mark.asyncio
async def test_remaining_budget():
    """Test remaining budget calculation"""
    tenant_id = str(uuid.uuid4())
    
    # Initial remaining should be full budget
    remaining = await llm_budget.get_remaining_budget(tenant_id)
    assert remaining == llm_budget.daily_budget
    
    # After spending, remaining should decrease
    await llm_budget.record_cost(25.0, tenant_id)
    remaining = await llm_budget.get_remaining_budget(tenant_id)
    assert remaining == llm_budget.daily_budget - 25.0
