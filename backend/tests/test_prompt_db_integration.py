"""Test that database prompts are used when available."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.prompt_manager import PromptManager, PromptTemplate


@pytest.mark.asyncio
async def test_generate_field_uses_db_prompt_when_available():
    """When db session is provided and prompt exists, use it."""
    mock_db = AsyncMock()
    mock_prompt = MagicMock()
    mock_prompt.content = "DB prompt: Generate meta title for {project_name}"
    mock_prompt.character_limit = 60
    mock_prompt.version = 2
    mock_prompt.name = "meta_title"
    mock_prompt.template_type = "opr"
    mock_prompt.content_variant = "standard"
    mock_prompt.is_active = True

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_prompt
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("app.services.content_generator.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            ANTHROPIC_API_KEY="test-key",
            ANTHROPIC_MODEL="claude-sonnet-4-5-20250514",
        )

        from app.services.content_generator import ContentGenerator

        generator = ContentGenerator(db=mock_db)

        # Mock the Anthropic API call
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test Title Here")]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=10)
        generator.client.messages_create = AsyncMock(return_value=mock_response)

        result = await generator.generate_field(
            field_name="meta_title",
            structured_data={
                "project_name": "Test Project",
                "developer": "Test Dev",
                "location": "Dubai",
            },
            template_type="opr",
        )

        assert result.content == "Test Title Here"
        assert result.prompt_version == "v2"
        # Verify db.execute was called (prompt lookup happened)
        mock_db.execute.assert_called()


@pytest.mark.asyncio
async def test_generate_field_falls_back_when_no_db():
    """When db session is None, fall back to hardcoded defaults."""
    with patch("app.services.content_generator.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            ANTHROPIC_API_KEY="test-key",
            ANTHROPIC_MODEL="claude-sonnet-4-5-20250514",
        )

        from app.services.content_generator import ContentGenerator

        generator = ContentGenerator(db=None)

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Fallback Title")]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=10)
        generator.client.messages_create = AsyncMock(return_value=mock_response)

        result = await generator.generate_field(
            field_name="meta_title",
            structured_data={
                "project_name": "Test Project",
                "developer": "Test Dev",
                "location": "Dubai",
            },
            template_type="opr",
        )

        assert result.content == "Fallback Title"
        assert result.prompt_version == "v1"  # Default version


@pytest.mark.asyncio
async def test_generate_all_uses_template_specific_fields():
    """generate_all() should use template-specific field set."""
    from app.services.template_fields import get_fields_for_template

    with patch("app.services.content_generator.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            ANTHROPIC_API_KEY="test-key",
            ANTHROPIC_MODEL="claude-sonnet-4-5-20250514",
        )

        from app.services.content_generator import ContentGenerator

        generator = ContentGenerator(db=None)

        # Mock the API so we don't actually call Claude
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Generated content")]
        mock_response.usage = MagicMock(input_tokens=50, output_tokens=20)
        generator.client.messages_create = AsyncMock(return_value=mock_response)

        result = await generator.generate_all(
            structured_data={
                "project_name": "Test",
                "developer": "Dev",
                "location": "Dubai",
            },
            template_type="aggregators",
        )

        aggregator_fields = get_fields_for_template("aggregators")
        # All generated fields should be from the aggregators field set
        for field_name in result.fields:
            assert field_name in aggregator_fields, (
                f"Field '{field_name}' generated but not in aggregators template"
            )
