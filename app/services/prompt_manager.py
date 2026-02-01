"""
Prompt Manager Service

Manages versioned LLM prompts with activation control.
"""
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.prompts import PromptTemplate
from uuid import UUID
import logging

logger = logging.getLogger("prompt_manager")


class PromptManager:
    """
    Service for managing versioned LLM prompts.
    """
    
    async def get_active_prompt(
        self,
        session: AsyncSession,
        prompt_name: str
    ) -> PromptTemplate:
        """
        Get active prompt template.
        
        Args:
            session: Database session
            prompt_name: Name of prompt ('email_generation', etc.)
            
        Returns:
            Active PromptTemplate instance
            
        Raises:
            NoResultFound: If no active prompt exists
        """
        tenant_id = session.info.get('tenant_id')
        
        result = await session.execute(
            select(PromptTemplate)
            .where(PromptTemplate.name == prompt_name)
            .where(PromptTemplate.tenant_id == tenant_id)
            .where(PromptTemplate.active == True)
            .order_by(PromptTemplate.version.desc())
            .limit(1)
        )
        
        prompt = result.scalar_one()
        logger.debug(f"Retrieved active prompt: {prompt_name} v{prompt.version}")
        return prompt
    
    async def create_new_version(
        self,
        session: AsyncSession,
        prompt_name: str,
        template: str,
        created_by: UUID,
        metadata: dict = None
    ) -> PromptTemplate:
        """
        Create new prompt version.
        
        Args:
            session: Database session
            prompt_name: Name of prompt
            template: Prompt template string
            created_by: User ID creating the version
            metadata: Optional metadata (A/B test config, etc.)
            
        Returns:
            Created PromptTemplate instance (inactive by default)
        """
        tenant_id = session.info.get('tenant_id')
        
        # Get current max version
        result = await session.execute(
            select(func.max(PromptTemplate.version))
            .where(PromptTemplate.name == prompt_name)
            .where(PromptTemplate.tenant_id == tenant_id)
        )
        current_version = result.scalar() or 0
        
        # Create new version
        prompt = PromptTemplate(
            name=prompt_name,
            version=current_version + 1,
            template=template,
            active=False,  # Not active by default
            created_by=created_by,
            metadata=metadata or {},
            tenant_id=tenant_id
        )
        
        session.add(prompt)
        await session.commit()
        await session.refresh(prompt)
        
        logger.info(f"Created prompt version: {prompt_name} v{prompt.version}")
        return prompt
    
    async def activate_version(
        self,
        session: AsyncSession,
        prompt_id: UUID
    ):
        """
        Activate specific prompt version (deactivates others).
        
        Args:
            session: Database session
            prompt_id: ID of prompt to activate
        """
        # Get prompt
        result = await session.execute(
            select(PromptTemplate).where(PromptTemplate.id == prompt_id)
        )
        prompt = result.scalar_one()
        
        # Deactivate all versions of this prompt
        await session.execute(
            update(PromptTemplate)
            .where(PromptTemplate.name == prompt.name)
            .where(PromptTemplate.tenant_id == prompt.tenant_id)
            .values(active=False)
        )
        
        # Activate this version
        prompt.active = True
        await session.commit()
        
        logger.info(f"Activated prompt: {prompt.name} v{prompt.version}")
    
    async def list_versions(
        self,
        session: AsyncSession,
        prompt_name: str
    ) -> list[PromptTemplate]:
        """
        List all versions of a prompt.
        
        Args:
            session: Database session
            prompt_name: Name of prompt
            
        Returns:
            List of PromptTemplate instances ordered by version desc
        """
        tenant_id = session.info.get('tenant_id')
        
        result = await session.execute(
            select(PromptTemplate)
            .where(PromptTemplate.name == prompt_name)
            .where(PromptTemplate.tenant_id == tenant_id)
            .order_by(PromptTemplate.version.desc())
        )
        
        return list(result.scalars().all())


# Global prompt manager instance
prompt_manager = PromptManager()
