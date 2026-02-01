"""
Prompt Versioning Integration Tests

Tests prompt management and version control.
"""
import pytest
import uuid
from app.services.prompt_manager import prompt_manager
from app.models.prompts import PromptTemplate


@pytest.mark.asyncio
async def test_create_prompt_version(db_session_with_tenant, tenant_id):
    """Test creating new prompt version"""
    user_id = uuid.uuid4()
    
    prompt = await prompt_manager.create_new_version(
        session=db_session_with_tenant,
        prompt_name='test_prompt',
        template='Hello {name}!',
        created_by=user_id
    )
    
    assert prompt.id is not None
    assert prompt.name == 'test_prompt'
    assert prompt.version == 1
    assert prompt.active is False


@pytest.mark.asyncio
async def test_version_increment(db_session_with_tenant, tenant_id):
    """Test version auto-increment"""
    user_id = uuid.uuid4()
    
    # Create version 1
    v1 = await prompt_manager.create_new_version(
        session=db_session_with_tenant,
        prompt_name='test_prompt',
        template='Version 1',
        created_by=user_id
    )
    
    # Create version 2
    v2 = await prompt_manager.create_new_version(
        session=db_session_with_tenant,
        prompt_name='test_prompt',
        template='Version 2',
        created_by=user_id
    )
    
    assert v1.version == 1
    assert v2.version == 2


@pytest.mark.asyncio
async def test_activate_version(db_session_with_tenant, tenant_id):
    """Test version activation"""
    user_id = uuid.uuid4()
    
    # Create two versions
    v1 = await prompt_manager.create_new_version(
        session=db_session_with_tenant,
        prompt_name='test_prompt',
        template='Version 1',
        created_by=user_id
    )
    
    v2 = await prompt_manager.create_new_version(
        session=db_session_with_tenant,
        prompt_name='test_prompt',
        template='Version 2',
        created_by=user_id
    )
    
    # Activate version 1
    await prompt_manager.activate_version(db_session_with_tenant, v1.id)
    
    # Get active prompt
    active = await prompt_manager.get_active_prompt(
        db_session_with_tenant,
        'test_prompt'
    )
    
    assert active.id == v1.id
    assert active.version == 1


@pytest.mark.asyncio
async def test_list_versions(db_session_with_tenant, tenant_id):
    """Test listing all versions"""
    user_id = uuid.uuid4()
    
    # Create 3 versions
    for i in range(3):
        await prompt_manager.create_new_version(
            session=db_session_with_tenant,
            prompt_name='test_prompt',
            template=f'Version {i+1}',
            created_by=user_id
        )
    
    # List versions
    versions = await prompt_manager.list_versions(
        db_session_with_tenant,
        'test_prompt'
    )
    
    assert len(versions) == 3
    assert versions[0].version == 3  # Ordered desc
    assert versions[1].version == 2
    assert versions[2].version == 1
