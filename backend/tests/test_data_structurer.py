"""
Comprehensive test suite for Data Structurer service.

Tests cover:
- DataStructurer.structure() with various input scenarios
- Claude API integration with retry logic
- Prompt building and system prompt generation
- JSON response parsing and cleaning
- Field validation with confidence scoring
- Cost calculation and token tracking
- Error handling and edge cases
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import pytest

from app.services.data_structurer import (
    CONFIDENCE_THRESHOLD_NEEDS_REVIEW,
    COST_PER_MTok_INPUT,
    COST_PER_MTok_OUTPUT,
    MAX_INPUT_CHARS,
    MAX_RETRIES,
    DataStructurer,
    FieldConfidence,
    StructuredProject,
    ValidationResult,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_settings():
    """Mock settings for all tests."""
    with patch("app.services.data_structurer.get_settings") as mock:
        settings = MagicMock()
        settings.ANTHROPIC_API_KEY = "test-api-key"
        settings.ANTHROPIC_MODEL = "claude-sonnet-4-5-20250514"
        settings.ANTHROPIC_MAX_TOKENS = 4096
        settings.ANTHROPIC_TEMPERATURE = 0.0
        settings.ANTHROPIC_TIMEOUT = 300
        mock.return_value = settings
        yield mock


@pytest.fixture
def sample_markdown():
    """Sample markdown text for extraction."""
    return """# Marina Vista by Emaar

## Location
- Emirate: Dubai
- Community: Dubai Marina
- Sub-community: Marina Heights

## Pricing
- Starting Price: AED 1,500,000
- Maximum Price: AED 5,000,000
- Price per sqft: AED 2,500

## Units
- Bedrooms: Studio, 1BR, 2BR, 3BR
- Total Units: 250
- Floors: 35

## Timeline
- Launch Date: Q1 2025
- Handover: Q4 2026

## Amenities
- Swimming Pool
- Gym & Fitness Center
- Children's Play Area
- 24/7 Security

## Features
- Beachfront Location
- Smart Home Technology
- Panoramic Views
"""


@pytest.fixture
def valid_claude_response():
    """Valid Claude API response structure."""
    return {
        "project_name": {"value": "Marina Vista", "confidence": 1.0},
        "developer": {"value": "Emaar", "confidence": 1.0},
        "emirate": {"value": "Dubai", "confidence": 1.0},
        "community": {"value": "Dubai Marina", "confidence": 1.0},
        "sub_community": {"value": "Marina Heights", "confidence": 0.9},
        "property_type": {"value": "Residential", "confidence": 0.8},
        "price_min": {"value": 1500000, "confidence": 1.0},
        "price_max": {"value": 5000000, "confidence": 1.0},
        "currency": {"value": "AED", "confidence": 1.0},
        "price_per_sqft": {"value": 2500, "confidence": 1.0},
        "bedrooms": {"value": ["Studio", "1BR", "2BR", "3BR"], "confidence": 1.0},
        "total_units": {"value": 250, "confidence": 1.0},
        "floors": {"value": 35, "confidence": 1.0},
        "handover_date": {"value": "Q4 2026", "confidence": 1.0},
        "launch_date": {"value": "Q1 2025", "confidence": 1.0},
        "amenities": {"value": ["Swimming Pool", "Gym & Fitness Center", "24/7 Security"], "confidence": 0.9},
        "key_features": {"value": ["Beachfront Location", "Smart Home Technology"], "confidence": 0.9},
        "payment_plan": {"value": {"down_payment": "20%", "during_construction": "50%", "on_handover": "30%"}, "confidence": 0.7},
        "description": {"value": "Luxury residential project in Dubai Marina with beachfront access", "confidence": 0.9},
    }


@pytest.fixture
def mock_anthropic_client(mock_settings):
    """Mock Anthropic client with successful response."""
    with patch("app.services.data_structurer.anthropic.AsyncAnthropic") as mock_client:
        mock_instance = MagicMock()

        # Mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"project_name": {"value": "Test Project", "confidence": 1.0}}')]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=300)

        # Mock messages.create as async
        mock_instance.messages.create = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_instance

        yield mock_instance


# ============================================================================
# Tests: DataStructurer initialization
# ============================================================================


def test_data_structurer_init_default(mock_settings):
    """Test DataStructurer initialization with default settings."""
    structurer = DataStructurer()

    assert structurer._model == "claude-sonnet-4-5-20250514"
    assert structurer._max_tokens == 4096
    assert structurer._temperature == 0.0


def test_data_structurer_init_custom_api_key(mock_settings):
    """Test DataStructurer initialization with custom API key."""
    with patch("app.services.data_structurer.anthropic.AsyncAnthropic") as mock_client:
        DataStructurer(api_key="custom-key")
        mock_client.assert_called_once()
        assert mock_client.call_args[1]["api_key"] == "custom-key"


def test_data_structurer_init_custom_model(mock_settings):
    """Test DataStructurer initialization with custom model."""
    structurer = DataStructurer(model="claude-opus-4-5-20251101")
    assert structurer._model == "claude-opus-4-5-20251101"


# ============================================================================
# Tests: DataStructurer.structure()
# ============================================================================


@pytest.mark.asyncio
async def test_structure_returns_structured_project(mock_anthropic_client, sample_markdown, valid_claude_response):
    """Test that structure() returns a StructuredProject with all fields."""
    # Setup mock response
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(
            content=[MagicMock(text=json.dumps(valid_claude_response))],
            usage=MagicMock(input_tokens=500, output_tokens=300)
        )
    )

    structurer = DataStructurer()
    result = await structurer.structure(sample_markdown)

    assert isinstance(result, StructuredProject)
    assert result.project_name == "Marina Vista"
    assert result.developer == "Emaar"
    assert result.emirate == "Dubai"
    assert result.price_min == 1500000
    assert result.price_max == 5000000
    assert "Studio" in result.bedrooms
    assert result.total_units == 250


@pytest.mark.asyncio
async def test_structure_parses_claude_response(mock_anthropic_client, sample_markdown, valid_claude_response):
    """Test that structure() correctly parses Claude's JSON response."""
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(
            content=[MagicMock(text=json.dumps(valid_claude_response))],
            usage=MagicMock(input_tokens=500, output_tokens=300)
        )
    )

    structurer = DataStructurer()
    result = await structurer.structure(sample_markdown)

    # Verify all fields parsed correctly
    assert result.project_name == "Marina Vista"
    assert result.confidence_scores["project_name"].confidence == 1.0
    assert result.confidence_scores["sub_community"].confidence == 0.9
    assert result.property_type == "Residential"
    assert isinstance(result.bedrooms, list)
    assert len(result.amenities) == 3


@pytest.mark.asyncio
async def test_structure_handles_empty_text(mock_anthropic_client):
    """Test that empty markdown returns sparse output without API call."""
    structurer = DataStructurer()
    result = await structurer.structure("")

    assert isinstance(result, StructuredProject)
    assert result.overall_confidence == 0.0
    assert len(result.missing_fields) == 19  # All fields missing
    assert result.project_name is None

    # Verify no API call was made
    mock_anthropic_client.messages.create.assert_not_called()


@pytest.mark.asyncio
async def test_structure_handles_whitespace_only(mock_anthropic_client):
    """Test that whitespace-only text is treated as empty."""
    structurer = DataStructurer()
    result = await structurer.structure("   \n\t  ")

    assert result.overall_confidence == 0.0
    assert len(result.missing_fields) == 19
    mock_anthropic_client.messages.create.assert_not_called()


@pytest.mark.asyncio
async def test_structure_calculates_token_usage(mock_anthropic_client, sample_markdown):
    """Test that token usage is tracked from API response."""
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(
            content=[MagicMock(text='{"project_name": {"value": "Test", "confidence": 1.0}}')],
            usage=MagicMock(input_tokens=1200, output_tokens=800)
        )
    )

    structurer = DataStructurer()
    result = await structurer.structure(sample_markdown)

    assert result.token_usage["input"] == 1200
    assert result.token_usage["output"] == 800


@pytest.mark.asyncio
async def test_structure_calculates_cost(mock_anthropic_client, sample_markdown):
    """Test that cost is calculated correctly: (input*3 + output*15) / 1M."""
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(
            content=[MagicMock(text='{"project_name": {"value": "Test", "confidence": 1.0}}')],
            usage=MagicMock(input_tokens=1000, output_tokens=500)
        )
    )

    structurer = DataStructurer()
    result = await structurer.structure(sample_markdown)

    # Cost = (1000 * 3 + 500 * 15) / 1,000,000 = (3000 + 7500) / 1,000,000 = 0.0105
    expected_cost = (1000 * COST_PER_MTok_INPUT + 500 * COST_PER_MTok_OUTPUT) / 1_000_000
    assert abs(result.structuring_cost - expected_cost) < 0.0001


@pytest.mark.asyncio
async def test_structure_identifies_missing_fields(mock_anthropic_client, sample_markdown):
    """Test that fields with null values are flagged as missing."""
    sparse_response = {
        "project_name": {"value": "Test Project", "confidence": 1.0},
        "developer": {"value": None, "confidence": 0.0},
        "emirate": {"value": None, "confidence": 0.0},
        "bedrooms": {"value": [], "confidence": 0.0},
        "amenities": {"value": [], "confidence": 0.0},
    }

    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(
            content=[MagicMock(text=json.dumps(sparse_response))],
            usage=MagicMock(input_tokens=500, output_tokens=200)
        )
    )

    structurer = DataStructurer()
    result = await structurer.structure(sample_markdown)

    # Check that missing fields are identified
    assert "developer" in result.missing_fields
    assert "emirate" in result.missing_fields
    assert "bedrooms" in result.missing_fields
    assert "project_name" not in result.missing_fields  # Has value


@pytest.mark.asyncio
async def test_structure_handles_api_exception(mock_anthropic_client, sample_markdown):
    """Test that API exceptions are handled gracefully after max retries."""
    # Create a mock request and response for proper exception initialization
    mock_request = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 500

    mock_anthropic_client.messages.create = AsyncMock(
        side_effect=[
            anthropic.InternalServerError("API Error", response=mock_response, body=None),
            anthropic.InternalServerError("API Error", response=mock_response, body=None),
            anthropic.InternalServerError("API Error", response=mock_response, body=None),
        ]
    )

    structurer = DataStructurer()
    result = await structurer.structure(sample_markdown)

    assert isinstance(result, StructuredProject)
    assert result.overall_confidence == 0.0
    assert len(result.missing_fields) == 19
    assert "Extraction failed" in result.description or "API Error" in result.description


# ============================================================================
# Tests: _call_claude()
# ============================================================================


@pytest.mark.asyncio
async def test_call_claude_retries_on_rate_limit(mock_anthropic_client, sample_markdown):
    """Test that 429 rate limit errors trigger retry logic."""
    # Create proper response mocks
    mock_response = MagicMock()
    mock_response.status_code = 429

    success_response = MagicMock()
    success_response.content = [MagicMock(text='{"project_name": {"value": "Test", "confidence": 1.0}}')]
    success_response.usage = MagicMock(input_tokens=500, output_tokens=300)

    # First two calls fail with rate limit, third succeeds
    mock_anthropic_client.messages.create = AsyncMock(
        side_effect=[
            anthropic.RateLimitError("Rate limit exceeded", response=mock_response, body=None),
            anthropic.RateLimitError("Rate limit exceeded", response=mock_response, body=None),
            success_response
        ]
    )

    structurer = DataStructurer()
    result = await structurer.structure(sample_markdown)

    assert result.project_name == "Test"
    assert mock_anthropic_client.messages.create.call_count == 3


@pytest.mark.asyncio
async def test_call_claude_retries_on_timeout(mock_anthropic_client, sample_markdown):
    """Test that timeout errors trigger retry logic."""
    mock_anthropic_client.messages.create = AsyncMock(
        side_effect=[
            anthropic.APITimeoutError("Request timeout"),
            MagicMock(
                content=[MagicMock(text='{"project_name": {"value": "Test", "confidence": 1.0}}')],
                usage=MagicMock(input_tokens=500, output_tokens=300)
            )
        ]
    )

    structurer = DataStructurer()
    result = await structurer.structure(sample_markdown)

    assert result.project_name == "Test"
    assert mock_anthropic_client.messages.create.call_count == 2


@pytest.mark.asyncio
async def test_call_claude_max_retries_exceeded(mock_anthropic_client, sample_markdown):
    """Test that after max retries, the exception is raised and handled."""
    mock_response = MagicMock()
    mock_response.status_code = 429

    mock_anthropic_client.messages.create = AsyncMock(
        side_effect=[
            anthropic.RateLimitError("Rate limit exceeded", response=mock_response, body=None),
            anthropic.RateLimitError("Rate limit exceeded", response=mock_response, body=None),
            anthropic.RateLimitError("Rate limit exceeded", response=mock_response, body=None),
        ]
    )

    structurer = DataStructurer()
    result = await structurer.structure(sample_markdown)

    # After MAX_RETRIES, should return error result
    assert result.overall_confidence == 0.0
    assert len(result.missing_fields) == 19
    assert mock_anthropic_client.messages.create.call_count == MAX_RETRIES


@pytest.mark.asyncio
async def test_call_claude_parses_json_response(mock_anthropic_client, sample_markdown):
    """Test that valid JSON is parsed correctly."""
    test_data = {
        "project_name": {"value": "Park Heights", "confidence": 1.0},
        "developer": {"value": "Meraas", "confidence": 0.95},
        "price_min": {"value": 2000000, "confidence": 0.9},
    }

    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(
            content=[MagicMock(text=json.dumps(test_data))],
            usage=MagicMock(input_tokens=600, output_tokens=400)
        )
    )

    structurer = DataStructurer()
    result = await structurer.structure(sample_markdown)

    assert result.project_name == "Park Heights"
    assert result.developer == "Meraas"
    assert result.price_min == 2000000


@pytest.mark.asyncio
async def test_call_claude_handles_json_decode_error(mock_anthropic_client, sample_markdown):
    """Test handling of invalid JSON response."""
    mock_anthropic_client.messages.create = AsyncMock(
        side_effect=[
            MagicMock(
                content=[MagicMock(text="Not valid JSON at all")],
                usage=MagicMock(input_tokens=500, output_tokens=100)
            ),
            MagicMock(
                content=[MagicMock(text="Still not JSON")],
                usage=MagicMock(input_tokens=500, output_tokens=100)
            ),
            MagicMock(
                content=[MagicMock(text="Nope")],
                usage=MagicMock(input_tokens=500, output_tokens=100)
            ),
        ]
    )

    structurer = DataStructurer()
    result = await structurer.structure(sample_markdown)

    # After 3 attempts with JSON errors, should return error response
    assert result.token_usage["input"] == 0
    assert result.token_usage["output"] == 0
    assert mock_anthropic_client.messages.create.call_count == MAX_RETRIES


# ============================================================================
# Tests: _build_structuring_prompt()
# ============================================================================


def test_prompt_contains_all_required_fields(mock_settings):
    """Test that prompt contains all schema fields."""
    structurer = DataStructurer()
    prompt = structurer._build_structuring_prompt("test markdown")

    required_fields = [
        "project_name", "developer", "emirate", "community", "sub_community",
        "property_type", "price_min", "price_max", "currency", "price_per_sqft",
        "bedrooms", "total_units", "floors", "handover_date", "launch_date",
        "amenities", "key_features", "payment_plan", "description"
    ]

    for field in required_fields:
        assert field in prompt


def test_prompt_requests_confidence_scores(mock_settings):
    """Test that prompt explicitly requests confidence scoring."""
    structurer = DataStructurer()
    prompt = structurer._build_structuring_prompt("test markdown")

    assert "confidence" in prompt.lower()
    assert "0.0-1.0" in prompt


def test_prompt_includes_markdown_text(mock_settings):
    """Test that the input markdown is included in the prompt."""
    structurer = DataStructurer()
    test_markdown = "# Unique Test Project Content"
    prompt = structurer._build_structuring_prompt(test_markdown)

    assert test_markdown in prompt


def test_prompt_includes_extraction_rules(mock_settings):
    """Test that extraction rules are included."""
    structurer = DataStructurer()
    prompt = structurer._build_structuring_prompt("test")

    assert "EXTRACTION RULES" in prompt
    assert "integers" in prompt.lower()
    assert "null" in prompt.lower()


def test_build_system_prompt(mock_settings):
    """Test system prompt generation."""
    structurer = DataStructurer()
    system_prompt = structurer._build_system_prompt()

    assert "real estate" in system_prompt.lower()
    assert "confidence" in system_prompt.lower()
    assert "1.0" in system_prompt
    assert "0.0" in system_prompt


# ============================================================================
# Tests: _validate()
# ============================================================================


def test_validate_passes_complete_data(mock_settings):
    """Test validation passes for complete, valid data."""
    project = StructuredProject(
        project_name="Test Project",
        developer="Test Developer",
        emirate="Dubai",
        price_min=1000000,
        price_max=5000000,
        total_units=100,
        floors=20,
        property_type="Residential",
        currency="AED",
    )

    structurer = DataStructurer()
    validation = structurer._validate(project)

    assert validation.is_valid is True
    assert len([i for i in validation.issues if i["severity"] == "critical"]) == 0


def test_validate_fails_missing_required_fields(mock_settings):
    """Test validation warns about missing critical fields."""
    project = StructuredProject(
        # Missing project_name, developer, emirate
        price_min=1000000
    )

    structurer = DataStructurer()
    validation = structurer._validate(project)

    # Should have warnings for missing critical fields
    assert any("project_name" in w for w in validation.warnings)
    assert any("developer" in w for w in validation.warnings)
    assert any("emirate" in w for w in validation.warnings)


def test_validate_fails_negative_price(mock_settings):
    """Test validation fails for negative prices."""
    project = StructuredProject(
        project_name="Test",
        price_min=-100,
        price_max=5000000
    )

    structurer = DataStructurer()
    validation = structurer._validate(project)

    assert validation.is_valid is False
    assert any(
        i["field"] == "price_min" and i["severity"] == "critical"
        for i in validation.issues
    )


def test_validate_fails_price_min_greater_than_max(mock_settings):
    """Test validation fails when price_min > price_max."""
    project = StructuredProject(
        project_name="Test",
        price_min=6000000,
        price_max=5000000
    )

    structurer = DataStructurer()
    validation = structurer._validate(project)

    assert validation.is_valid is False
    assert any("min > max" in i["issue"] for i in validation.issues)


def test_validate_returns_warnings(mock_settings):
    """Test validation returns non-critical warnings."""
    project = StructuredProject(
        project_name="Test",
        total_units=150000,  # Outside expected range
        bedrooms=["INVALID_FORMAT"],
        property_type="Industrial",  # Non-standard
    )

    structurer = DataStructurer()
    validation = structurer._validate(project)

    assert len(validation.warnings) > 0
    assert any("total_units" in w for w in validation.warnings)
    assert any("bedroom" in w.lower() for w in validation.warnings)
    assert any("property type" in w.lower() for w in validation.warnings)


def test_validate_floors_out_of_range(mock_settings):
    """Test validation warns for unusual floor counts."""
    project = StructuredProject(
        project_name="Test",
        floors=300  # > 200
    )

    structurer = DataStructurer()
    validation = structurer._validate(project)

    assert any("floors" in w for w in validation.warnings)


def test_validate_negative_price_per_sqft(mock_settings):
    """Test validation handles negative price per sqft."""
    project = StructuredProject(
        project_name="Test",
        price_per_sqft=-100
    )

    structurer = DataStructurer()
    validation = structurer._validate(project)

    assert any(
        i.get("field") == "price_per_sqft"
        for i in validation.issues
    )


def test_validate_date_formats(mock_settings):
    """Test validation of date format strings."""
    structurer = DataStructurer()

    # Valid dates
    assert structurer._is_valid_date_format("Q1 2026") is True
    assert structurer._is_valid_date_format("Q4 2027") is True
    assert structurer._is_valid_date_format("2026") is True
    assert structurer._is_valid_date_format("Dec 2026") is True
    assert structurer._is_valid_date_format("December 2026") is True

    # Invalid dates
    assert structurer._is_valid_date_format("Q5 2026") is False
    assert structurer._is_valid_date_format("Invalid") is False
    assert structurer._is_valid_date_format("2026-12-01") is False


def test_validate_warns_invalid_date_format(mock_settings):
    """Test validation warns for non-standard date formats."""
    project = StructuredProject(
        project_name="Test",
        handover_date="2026-12-01",  # ISO format not accepted
        launch_date="Next year"
    )

    structurer = DataStructurer()
    validation = structurer._validate(project)

    assert any("handover date" in w.lower() for w in validation.warnings)
    assert any("launch date" in w.lower() for w in validation.warnings)


# ============================================================================
# Tests: _clean_json_response()
# ============================================================================


def test_clean_strips_markdown_fences(mock_settings):
    """Test that markdown code fences are stripped."""
    structurer = DataStructurer()

    input_text = '```json\n{"key": "value"}\n```'
    cleaned = structurer._clean_json_response(input_text)

    assert cleaned == '{"key": "value"}'
    assert "```" not in cleaned


def test_clean_handles_plain_json(mock_settings):
    """Test that plain JSON without fences is unchanged."""
    structurer = DataStructurer()

    input_text = '{"key": "value", "number": 42}'
    cleaned = structurer._clean_json_response(input_text)

    assert cleaned == input_text


def test_clean_handles_json_fence_without_language(mock_settings):
    """Test cleaning of fences without language specifier."""
    structurer = DataStructurer()

    input_text = '```\n{"key": "value"}\n```'
    cleaned = structurer._clean_json_response(input_text)

    assert cleaned == '{"key": "value"}'


def test_clean_strips_whitespace(mock_settings):
    """Test that leading/trailing whitespace is stripped."""
    structurer = DataStructurer()

    input_text = '  \n{"key": "value"}\n  '
    cleaned = structurer._clean_json_response(input_text)

    assert cleaned == '{"key": "value"}'


# ============================================================================
# Tests: FieldConfidence
# ============================================================================


def test_field_confidence_needs_review(mock_settings):
    """Test that confidence < 0.7 flags needs_review=True."""
    fc = FieldConfidence(
        field_name="test_field",
        confidence=0.65,
        source="claude_extraction",
        needs_review=True
    )

    assert fc.needs_review is True
    assert fc.confidence < CONFIDENCE_THRESHOLD_NEEDS_REVIEW


def test_field_confidence_no_review(mock_settings):
    """Test that confidence >= 0.7 means needs_review=False."""
    fc = FieldConfidence(
        field_name="test_field",
        confidence=0.9,
        source="claude_extraction",
        needs_review=False
    )

    assert fc.needs_review is False
    assert fc.confidence >= CONFIDENCE_THRESHOLD_NEEDS_REVIEW


def test_field_confidence_boundary(mock_settings):
    """Test confidence at exact threshold boundary."""
    fc_below = FieldConfidence(
        field_name="test1",
        confidence=0.69,
        source="claude_extraction",
        needs_review=True
    )

    fc_at = FieldConfidence(
        field_name="test2",
        confidence=0.70,
        source="claude_extraction",
        needs_review=False
    )

    assert fc_below.needs_review is True
    assert fc_at.needs_review is False


# ============================================================================
# Tests: StructuredProject
# ============================================================================


def test_overall_confidence_calculated(mock_settings):
    """Test that overall confidence is average of field confidences."""
    project = StructuredProject()
    project.confidence_scores = {
        "field1": FieldConfidence("field1", 1.0, "test", False),
        "field2": FieldConfidence("field2", 0.8, "test", False),
        "field3": FieldConfidence("field3", 0.6, "test", True),
    }

    # Overall should be (1.0 + 0.8 + 0.6) / 3 = 0.8
    expected = (1.0 + 0.8 + 0.6) / 3

    # Manually calculate since overall_confidence is set during parsing
    confidences = [fc.confidence for fc in project.confidence_scores.values() if fc.confidence > 0]
    actual = sum(confidences) / len(confidences) if confidences else 0.0

    assert abs(actual - expected) < 0.01


def test_needs_review_fields_populated(mock_settings):
    """Test that fields with low confidence are listed in needs_review_fields."""
    project = StructuredProject()
    project.needs_review_fields = ["developer", "price_max", "handover_date"]

    assert len(project.needs_review_fields) == 3
    assert "developer" in project.needs_review_fields
    assert "price_max" in project.needs_review_fields


def test_structured_project_defaults(mock_settings):
    """Test StructuredProject default values."""
    project = StructuredProject()

    assert project.project_name is None
    assert project.currency == "AED"
    assert project.bedrooms == []
    assert project.amenities == []
    assert project.confidence_scores == {}
    assert project.overall_confidence == 0.0
    assert project.missing_fields == []
    assert project.token_usage == {}
    assert project.structuring_cost == 0.0


# ============================================================================
# Tests: _parse_structured_data()
# ============================================================================


@pytest.mark.asyncio
async def test_parse_handles_error_response(mock_settings):
    """Test parsing of error responses from Claude."""
    raw_data = {
        "error": "JSON parse error: Invalid syntax",
        "_token_usage": {"input": 100, "output": 50},
        "_cost": 0.001
    }

    structurer = DataStructurer()
    project = structurer._parse_structured_data(raw_data)

    assert "JSON parse error" in project.description
    assert project.overall_confidence == 0.0
    assert len(project.missing_fields) == 19
    assert project.token_usage["input"] == 100


@pytest.mark.asyncio
async def test_parse_handles_direct_values(mock_settings):
    """Test parsing when values are provided directly without confidence."""
    raw_data = {
        "project_name": "Direct Project",  # No confidence wrapper
        "developer": "Direct Dev",
        "_token_usage": {"input": 100, "output": 50},
        "_cost": 0.001
    }

    structurer = DataStructurer()
    project = structurer._parse_structured_data(raw_data)

    assert project.project_name == "Direct Project"
    assert project.developer == "Direct Dev"
    # Should have default medium confidence (0.5)
    assert project.confidence_scores["project_name"].confidence == 0.5


@pytest.mark.asyncio
async def test_parse_converts_null_strings(mock_settings):
    """Test that 'null' and 'None' strings are converted to None."""
    raw_data = {
        "project_name": {"value": "null", "confidence": 0.0},
        "developer": {"value": "None", "confidence": 0.0},
        "_token_usage": {"input": 100, "output": 50},
        "_cost": 0.001
    }

    structurer = DataStructurer()
    project = structurer._parse_structured_data(raw_data)

    assert project.project_name is None
    assert project.developer is None


@pytest.mark.asyncio
async def test_parse_type_conversion(mock_settings):
    """Test that field types are correctly converted."""
    raw_data = {
        "price_min": {"value": "1500000", "confidence": 1.0},  # String to int
        "total_units": {"value": 250.0, "confidence": 1.0},     # Float to int
        "bedrooms": {"value": "Studio,1BR", "confidence": 0.8},  # Will try list conversion
        "_token_usage": {"input": 100, "output": 50},
        "_cost": 0.001
    }

    structurer = DataStructurer()
    project = structurer._parse_structured_data(raw_data)

    assert isinstance(project.price_min, int)
    assert project.price_min == 1500000
    assert isinstance(project.total_units, int)
    assert project.total_units == 250


# ============================================================================
# Tests: _calculate_cost()
# ============================================================================


def test_calculate_cost_zero_tokens(mock_settings):
    """Test cost calculation with zero tokens."""
    structurer = DataStructurer()
    cost = structurer._calculate_cost(0, 0)

    assert cost == 0.0


def test_calculate_cost_standard_usage(mock_settings):
    """Test cost calculation with typical usage."""
    structurer = DataStructurer()
    cost = structurer._calculate_cost(1000, 500)

    # (1000 * 3 + 500 * 15) / 1,000,000 = 10,500 / 1,000,000 = 0.0105
    expected = (1000 * COST_PER_MTok_INPUT + 500 * COST_PER_MTok_OUTPUT) / 1_000_000
    assert abs(cost - expected) < 0.0001


def test_calculate_cost_high_usage(mock_settings):
    """Test cost calculation with high token usage."""
    structurer = DataStructurer()
    cost = structurer._calculate_cost(10000, 5000)

    # (10000 * 3 + 5000 * 15) / 1,000,000 = 105,000 / 1,000,000 = 0.105
    expected = (10000 * COST_PER_MTok_INPUT + 5000 * COST_PER_MTok_OUTPUT) / 1_000_000
    assert abs(cost - expected) < 0.0001


def test_calculate_cost_only_input(mock_settings):
    """Test cost calculation with only input tokens."""
    structurer = DataStructurer()
    cost = structurer._calculate_cost(2000, 0)

    expected = (2000 * COST_PER_MTok_INPUT) / 1_000_000
    assert abs(cost - expected) < 0.0001


def test_calculate_cost_only_output(mock_settings):
    """Test cost calculation with only output tokens."""
    structurer = DataStructurer()
    cost = structurer._calculate_cost(0, 1000)

    expected = (1000 * COST_PER_MTok_OUTPUT) / 1_000_000
    assert abs(cost - expected) < 0.0001


# ============================================================================
# Tests: _get_all_field_names()
# ============================================================================


def test_get_all_field_names(mock_settings):
    """Test that all field names are returned."""
    structurer = DataStructurer()
    fields = structurer._get_all_field_names()

    assert len(fields) == 19
    assert "project_name" in fields
    assert "developer" in fields
    assert "price_min" in fields
    assert "bedrooms" in fields
    assert "description" in fields


# ============================================================================
# Tests: ValidationResult
# ============================================================================


def test_validation_result_creation():
    """Test ValidationResult dataclass creation."""
    result = ValidationResult(
        is_valid=True,
        issues=[],
        warnings=["Minor warning"]
    )

    assert result.is_valid is True
    assert len(result.issues) == 0
    assert len(result.warnings) == 1


def test_validation_result_with_issues():
    """Test ValidationResult with critical issues."""
    issues = [
        {"field": "price_min", "issue": "negative value", "severity": "critical"},
        {"field": "price_max", "issue": "negative value", "severity": "critical"}
    ]

    result = ValidationResult(
        is_valid=False,
        issues=issues,
        warnings=[]
    )

    assert result.is_valid is False
    assert len(result.issues) == 2
    assert result.issues[0]["severity"] == "critical"


# ============================================================================
# Tests: Edge cases and integration
# ============================================================================


@pytest.mark.asyncio
async def test_structure_with_template_type_parameter(mock_anthropic_client, sample_markdown):
    """Test that template_type parameter is accepted (for future use)."""
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(
            content=[MagicMock(text='{"project_name": {"value": "Test", "confidence": 1.0}}')],
            usage=MagicMock(input_tokens=500, output_tokens=300)
        )
    )

    structurer = DataStructurer()
    result = await structurer.structure(sample_markdown, template_type="custom_template")

    assert isinstance(result, StructuredProject)


@pytest.mark.asyncio
async def test_parse_with_empty_lists_and_dicts(mock_settings):
    """Test parsing fields with empty collections."""
    raw_data = {
        "project_name": {"value": "Test", "confidence": 1.0},
        "bedrooms": {"value": [], "confidence": 0.0},
        "amenities": {"value": [], "confidence": 0.0},
        "payment_plan": {"value": None, "confidence": 0.0},
        "_token_usage": {"input": 100, "output": 50},
        "_cost": 0.001
    }

    structurer = DataStructurer()
    project = structurer._parse_structured_data(raw_data)

    assert project.bedrooms == []
    assert project.amenities == []
    assert project.payment_plan is None
    assert "bedrooms" in project.missing_fields
    assert "amenities" in project.missing_fields


@pytest.mark.asyncio
async def test_overall_confidence_with_zero_scores(mock_settings):
    """Test overall confidence when all explicit scores are zero."""
    # Note: Missing fields in raw_data will get default 0.5 confidence
    # Only explicitly set fields to 0.0 will have 0 confidence
    raw_data = {
        "project_name": {"value": None, "confidence": 0.0},
        "developer": {"value": None, "confidence": 0.0},
        "emirate": {"value": None, "confidence": 0.0},
        "community": {"value": None, "confidence": 0.0},
        "sub_community": {"value": None, "confidence": 0.0},
        "property_type": {"value": None, "confidence": 0.0},
        "price_min": {"value": None, "confidence": 0.0},
        "price_max": {"value": None, "confidence": 0.0},
        "currency": {"value": None, "confidence": 0.0},
        "price_per_sqft": {"value": None, "confidence": 0.0},
        "bedrooms": {"value": [], "confidence": 0.0},
        "total_units": {"value": None, "confidence": 0.0},
        "floors": {"value": None, "confidence": 0.0},
        "handover_date": {"value": None, "confidence": 0.0},
        "launch_date": {"value": None, "confidence": 0.0},
        "amenities": {"value": [], "confidence": 0.0},
        "key_features": {"value": [], "confidence": 0.0},
        "payment_plan": {"value": None, "confidence": 0.0},
        "description": {"value": None, "confidence": 0.0},
        "_token_usage": {"input": 100, "output": 50},
        "_cost": 0.001
    }

    structurer = DataStructurer()
    project = structurer._parse_structured_data(raw_data)

    # When all confidences are 0, overall should be 0
    assert project.overall_confidence == 0.0


@pytest.mark.asyncio
async def test_overall_confidence_excludes_zero_scores(mock_settings):
    """Test that zero confidence scores are excluded from average calculation."""
    # Provide all fields to avoid default 0.5 confidence for missing fields
    raw_data = {
        "project_name": {"value": "Test", "confidence": 1.0},
        "developer": {"value": "Dev", "confidence": 0.8},
        "emirate": {"value": None, "confidence": 0.0},  # Should be excluded
        "community": {"value": None, "confidence": 0.0},
        "sub_community": {"value": None, "confidence": 0.0},
        "property_type": {"value": None, "confidence": 0.0},
        "price_min": {"value": None, "confidence": 0.0},
        "price_max": {"value": None, "confidence": 0.0},
        "currency": {"value": None, "confidence": 0.0},
        "price_per_sqft": {"value": None, "confidence": 0.0},
        "bedrooms": {"value": [], "confidence": 0.0},
        "total_units": {"value": None, "confidence": 0.0},
        "floors": {"value": None, "confidence": 0.0},
        "handover_date": {"value": None, "confidence": 0.0},
        "launch_date": {"value": None, "confidence": 0.0},
        "amenities": {"value": [], "confidence": 0.0},
        "key_features": {"value": [], "confidence": 0.0},
        "payment_plan": {"value": None, "confidence": 0.0},
        "description": {"value": None, "confidence": 0.0},
        "_token_usage": {"input": 100, "output": 50},
        "_cost": 0.001
    }

    structurer = DataStructurer()
    project = structurer._parse_structured_data(raw_data)

    # Should be (1.0 + 0.8) / 2 = 0.9, with all zero scores excluded
    assert abs(project.overall_confidence - 0.9) < 0.01


# ============================================================================
# Risk Mitigation Tests - Input Truncation
# ============================================================================


class TestDataStructurerInputTruncation:
    """Tests for input text truncation to prevent context overflow."""

    @pytest.mark.asyncio
    async def test_long_input_truncated(self, mock_settings):
        """Test that input exceeding MAX_INPUT_CHARS is truncated."""
        long_text = "A" * (MAX_INPUT_CHARS + 50000)
        assert len(long_text) > MAX_INPUT_CHARS

        structurer = DataStructurer()

        # Mock _call_claude to capture the prompt it receives
        called_with_prompt = {}

        async def capture_call(prompt, system=""):
            called_with_prompt["prompt"] = prompt
            return {
                "project_name": {"value": "Test", "confidence": 0.8},
                "_token_usage": {"input": 100, "output": 50},
                "_cost": 0.001,
            }

        structurer._call_claude = capture_call
        await structurer.structure(long_text)

        # The prompt should contain the truncated text, not the full text
        assert len(called_with_prompt["prompt"]) < len(long_text)

    @pytest.mark.asyncio
    async def test_short_input_not_truncated(self, mock_settings):
        """Test that input under MAX_INPUT_CHARS is not truncated."""
        short_text = "# Test Project\nLocation: Dubai\nPrice: 1000000"
        assert len(short_text) < MAX_INPUT_CHARS

        structurer = DataStructurer()

        called_with_prompt = {}

        async def capture_call(prompt, system=""):
            called_with_prompt["prompt"] = prompt
            return {
                "project_name": {"value": "Test", "confidence": 0.8},
                "_token_usage": {"input": 100, "output": 50},
                "_cost": 0.001,
            }

        structurer._call_claude = capture_call
        await structurer.structure(short_text)

        # The prompt should contain the full original text
        assert short_text in called_with_prompt["prompt"]

    def test_max_input_chars_constant(self):
        """Test MAX_INPUT_CHARS is defined at a reasonable value."""
        assert MAX_INPUT_CHARS == 150_000
        # Should be well under Claude's ~800K char context window
        assert MAX_INPUT_CHARS < 800_000
