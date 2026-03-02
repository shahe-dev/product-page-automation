"""Tests for GenerationRunRepository."""
import pytest
import uuid
from unittest.mock import AsyncMock
from app.repositories.generation_run_repository import GenerationRunRepository
from app.models.enums import TemplateType


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def repo(mock_db):
    return GenerationRunRepository(mock_db)


@pytest.mark.asyncio
async def test_create_generation_run(repo, mock_db):
    """Repository creates GenerationRun record."""
    project_id = uuid.uuid4()

    result = await repo.create(
        project_id=project_id,
        template_type=TemplateType.OPR
    )

    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()


def test_repository_has_expected_methods():
    """Repository class has all expected methods."""
    assert hasattr(GenerationRunRepository, "create")
    assert hasattr(GenerationRunRepository, "get_by_id")
    assert hasattr(GenerationRunRepository, "get_by_project_and_template")
    assert hasattr(GenerationRunRepository, "list_by_project")
    assert hasattr(GenerationRunRepository, "mark_completed")
    assert hasattr(GenerationRunRepository, "mark_failed")
