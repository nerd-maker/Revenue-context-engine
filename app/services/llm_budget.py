"""
LLM Budget Manager

Controls LLM API spending with daily budget caps.
Tracks costs in Redis for fast access.
"""
from app.core.redis_client import redis_cache
from datetime import date
import logging

logger = logging.getLogger("llm_budget")


class BudgetExceededError(Exception):
    """Raised when daily LLM budget is exceeded"""
    pass


class LLMBudgetManager:
    """
    Manages LLM API budget with Redis-backed tracking.
    
    Features:
    - Daily budget caps per tenant
    - Real-time spend tracking
    - 90% warning threshold
    - Token-based cost calculation
    """
    
    def __init__(self, daily_budget: float = 100.0):
        """
        Initialize budget manager.
        
        Args:
            daily_budget: Maximum daily spend in USD
        """
        self.daily_budget = daily_budget
    
    async def check_budget(self, tenant_id: str = None) -> bool:
        """
        Check if budget available.
        
        Args:
            tenant_id: Tenant ID (None for global budget)
            
        Returns:
            True if budget available, False otherwise
        """
        await redis_cache.connect()
        key = self._get_key(tenant_id)
        current_spend = float(await redis_cache.redis.get(key) or 0)
        return current_spend < self.daily_budget
    
    async def record_cost(self, cost: float, tenant_id: str = None):
        """
        Record LLM API cost.
        
        Args:
            cost: Cost in USD
            tenant_id: Tenant ID (None for global budget)
        """
        await redis_cache.connect()
        key = self._get_key(tenant_id)
        new_spend = await redis_cache.redis.incrbyfloat(key, cost)
        await redis_cache.redis.expire(key, 86400 * 2)  # 2-day retention
        
        logger.info(f"LLM cost recorded: ${cost:.4f}, total today: ${new_spend:.2f}")
        
        # Alert if approaching limit
        if new_spend > self.daily_budget * 0.9:
            logger.warning(
                f"LLM budget at {(new_spend/self.daily_budget)*100:.0f}%: "
                f"${new_spend:.2f} / ${self.daily_budget:.2f}"
            )
    
    async def get_remaining_budget(self, tenant_id: str = None) -> float:
        """
        Get remaining daily budget.
        
        Args:
            tenant_id: Tenant ID (None for global budget)
            
        Returns:
            Remaining budget in USD
        """
        await redis_cache.connect()
        key = self._get_key(tenant_id)
        current_spend = float(await redis_cache.redis.get(key) or 0)
        return max(0, self.daily_budget - current_spend)
    
    async def get_current_spend(self, tenant_id: str = None) -> float:
        """
        Get current daily spend.
        
        Args:
            tenant_id: Tenant ID (None for global budget)
            
        Returns:
            Current spend in USD
        """
        await redis_cache.connect()
        key = self._get_key(tenant_id)
        return float(await redis_cache.redis.get(key) or 0)
    
    def _get_key(self, tenant_id: str = None) -> str:
        """
        Generate Redis key for budget tracking.
        
        Args:
            tenant_id: Tenant ID (None for global budget)
            
        Returns:
            Redis key string
        """
        if tenant_id:
            return f"llm:spend:{tenant_id}:{date.today()}"
        return f"llm:spend:global:{date.today()}"
    
    def calculate_cost(self, tokens: int, model: str = 'gpt-4') -> float:
        """
        Calculate API cost from token count.
        
        Args:
            tokens: Total token count (prompt + completion)
            model: Model name ('gpt-4', 'gpt-3.5-turbo')
            
        Returns:
            Cost in USD
        """
        # Pricing (as of 2026, update as needed)
        pricing = {
            'gpt-4': 0.03 / 1000,          # $0.03 per 1K tokens
            'gpt-4-turbo': 0.01 / 1000,    # $0.01 per 1K tokens
            'gpt-3.5-turbo': 0.002 / 1000,  # $0.002 per 1K tokens
        }
        
        cost_per_token = pricing.get(model, 0.03 / 1000)
        return tokens * cost_per_token


# Global budget manager instance
llm_budget = LLMBudgetManager(daily_budget=100.0)
