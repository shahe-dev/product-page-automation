"""End-to-end smoke tests for the prompt system across all 6 template types.

Verifies that ContentGenerator.generate_all() can produce every field
defined in TEMPLATE_FIELD_REGISTRY without errors, using mocked API calls.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.template_fields import TEMPLATE_FIELD_REGISTRY


SAMPLE_DATA = {
    "project_name": "Test Residences",
    "developer": "Test Properties",
    "location": "Dubai Marina",
    "emirate": "Dubai",
    "starting_price": 1500000,
    "handover_date": "Q4 2027",
    "amenities": ["Pool", "Gym", "Spa", "Kids Area", "BBQ"],
    "property_types": ["1BR", "2BR", "3BR"],
    "payment_plan": "60/40",
    "description": "A test project for validation.",
}


@pytest.mark.asyncio
@pytest.mark.parametrize("template_type", list(TEMPLATE_FIELD_REGISTRY.keys()))
async def test_all_templates_generate_without_errors(template_type):
    """Every template type should generate all its fields without errors."""
    with patch("app.services.content_generator.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            ANTHROPIC_API_KEY="test-key",
            ANTHROPIC_MODEL="claude-sonnet-4-5-20250514",
        )

        # Patch the inter-field delay to 0 so tests run fast
        with patch("app.services.content_generator.INTER_FIELD_DELAY", 0):
            from app.services.content_generator import ContentGenerator

            generator = ContentGenerator(db=None)

            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Generated test content")]
            mock_response.usage = MagicMock(input_tokens=50, output_tokens=20)
            generator.client.messages_create = AsyncMock(return_value=mock_response)

            result = await generator.generate_all(SAMPLE_DATA, template_type)

    expected_fields = set(TEMPLATE_FIELD_REGISTRY[template_type].keys())
    generated_fields = set(result.fields.keys())

    assert len(result.errors) == 0, f"Errors for {template_type}: {result.errors}"
    assert generated_fields == expected_fields, (
        f"Missing: {expected_fields - generated_fields}, "
        f"Extra: {generated_fields - expected_fields}"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("template_type", list(TEMPLATE_FIELD_REGISTRY.keys()))
async def test_all_fields_have_prompt_content(template_type):
    """Every field in every template should resolve to a non-empty prompt."""
    from app.services.prompt_manager import PromptManager

    pm = PromptManager()
    fields = TEMPLATE_FIELD_REGISTRY[template_type]

    for field_name in fields:
        prompt = await pm.get_prompt(
            field_name=field_name,
            template_type=template_type,
            db=None,
        )
        assert prompt.content, (
            f"Empty prompt content for {template_type}:{field_name}"
        )
        assert prompt.field_name == field_name
        assert prompt.template_type == template_type


@pytest.mark.asyncio
@pytest.mark.parametrize("template_type", list(TEMPLATE_FIELD_REGISTRY.keys()))
async def test_system_message_includes_template_context(template_type):
    """System message should contain brand context and template type."""
    with patch("app.services.content_generator.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            ANTHROPIC_API_KEY="test-key",
            ANTHROPIC_MODEL="claude-sonnet-4-5-20250514",
        )

        from app.services.content_generator import ContentGenerator

        generator = ContentGenerator(db=None)
        system_msg = generator._build_system_message(template_type)

    assert template_type.upper() in system_msg
    assert "TEMPLATE CONTEXT:" in system_msg
    # Brand context should be present (either from file or default)
    assert "BRAND" in system_msg.upper() or "real estate" in system_msg.lower()
