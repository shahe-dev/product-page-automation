"""
Comprehensive test suite for content generation services.

Tests cover:
- ContentGenerator: AI-powered content generation with Anthropic Claude
- ContentQAService: Brand compliance, character limits, SEO, factual accuracy
- PromptManager: Version-controlled prompts with variable substitution
- Error handling and cost tracking
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.services.content_generator import (
    COST_PER_INPUT_TOKEN,
    COST_PER_OUTPUT_TOKEN,
    MAX_RETRIES,
    RETRY_DELAY_BASE,
    RETRY_DELAY_MAX,
    ContentGenerator,
    ContentOutput,
    GeneratedField,
)
from app.services.content_qa_service import (
    ContentQAService,
    QACheckResult,
    QAReport,
)
from app.services.prompt_manager import PromptManager, PromptTemplate


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_project_data():
    """Sample structured project data for testing."""
    return {
        "project_name": "Marina Vista",
        "developer": "Emaar",
        "location": "Dubai Marina, Dubai",
        "emirate": "Dubai",
        "starting_price": 1200000,
        "bedrooms": ["1BR", "2BR", "3BR"],
        "amenities": ["Swimming Pool", "Gym", "Concierge"],
        "completion_date": "Q4 2026",
        "property_types": ["1BR", "2BR", "3BR"],
        "payment_plan": "60/40 payment plan",
        "description": "Luxury waterfront apartments in Dubai Marina",
    }


@pytest.fixture
def mock_settings():
    """Mock settings for ContentGenerator."""
    with patch("app.services.content_generator.get_settings") as mock:
        settings = MagicMock(
            ANTHROPIC_API_KEY="test-key",
            ANTHROPIC_MODEL="claude-sonnet-4-5-20250514",
            ANTHROPIC_MAX_TOKENS=4096,
            ANTHROPIC_TEMPERATURE=0.0,
            ANTHROPIC_TIMEOUT=300,
        )
        mock.return_value = settings
        yield mock


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response."""
    response = MagicMock()
    response.content = [MagicMock(text="Generated content for field")]
    response.usage = MagicMock(input_tokens=100, output_tokens=50)
    return response


@pytest.fixture
def mock_anthropic_client(mock_anthropic_response):
    """Mock Anthropic service used by content generator."""
    with patch("app.services.content_generator.anthropic_service") as mock_service:
        # Mock the messages_create method that content_generator actually calls
        mock_service.messages_create = AsyncMock(return_value=mock_anthropic_response)
        yield mock_service


@pytest.fixture
def sample_generated_field():
    """Sample GeneratedField for testing."""
    return GeneratedField(
        field_name="meta_title",
        content="Marina Vista - Luxury Apartments in Dubai Marina",
        character_count=52,
        within_limit=True,
        template_type="aggregators",
        token_usage={"input": 100, "output": 50},
        generation_cost=0.001,
        prompt_version="v1",
    )


@pytest.fixture
def sample_content_output(sample_generated_field):
    """Sample ContentOutput with multiple fields."""
    field1 = sample_generated_field
    field2 = GeneratedField(
        field_name="meta_description",
        content="Discover Marina Vista, a new development by Emaar in Dubai Marina. Starting from AED 1.2M. Expected handover Q4 2026.",
        character_count=140,
        within_limit=True,
        template_type="aggregators",
        token_usage={"input": 150, "output": 75},
        generation_cost=0.002,
        prompt_version="v1",
    )

    return ContentOutput(
        fields={"meta_title": field1, "meta_description": field2},
        template_type="aggregators",
        total_token_usage={"input": 250, "output": 125},
        total_cost=0.003,
        errors=[],
    )


# ============================================================================
# Tests: ContentGenerator - Initialization
# ============================================================================


def test_content_generator_initialization(mock_settings, mock_anthropic_client):
    """Test ContentGenerator initialization with settings and Anthropic client."""
    generator = ContentGenerator()

    assert generator.settings is not None
    assert generator.client is not None
    assert generator.prompt_manager is not None
    assert generator.brand_context is not None


def test_content_generator_field_limits_defined():
    """Test that template fields contain character limits for expected fields."""
    from app.services.template_fields import get_fields_for_template

    # ContentGenerator uses template_fields for field definitions, not a class attribute
    # Test that aggregators template has the key content fields
    aggregators_fields = get_fields_for_template("aggregators")

    # Field names updated to match current template structure
    expected_fields = [
        "meta_title",
        "meta_description",
        "url_slug",
        "hero_h1",  # Was "h1" in earlier version
    ]

    for field in expected_fields:
        assert field in aggregators_fields, f"Missing field: {field}"
        # Verify char_limit is defined (may be None for some fields)
        assert hasattr(aggregators_fields[field], "char_limit")


def test_prohibited_terms_defined():
    """Test that PROHIBITED_TERMS list is populated."""
    prohibited = ContentGenerator.PROHIBITED_TERMS

    assert len(prohibited) > 0
    assert "world-class" in prohibited
    assert "prime location" in prohibited
    assert "state-of-the-art" in prohibited
    assert "unrivaled" in prohibited
    assert "prestigious" in prohibited


# ============================================================================
# Tests: ContentGenerator - Brand Context Loading
# ============================================================================


def test_brand_context_loaded(mock_settings, mock_anthropic_client):
    """Test that brand context is loaded (or default is used)."""
    generator = ContentGenerator()

    assert isinstance(generator.brand_context, str)
    assert len(generator.brand_context) > 0
    # Should contain brand guidelines
    assert "brand" in generator.brand_context.lower() or "mpd" in generator.brand_context.lower()


def test_brand_context_fallback_when_file_missing(mock_settings, mock_anthropic_client):
    """Test that default brand context is used when file is missing."""
    with patch("app.services.content_generator.Path") as mock_path:
        # Create a mock path object that returns False for exists()
        # The code does: Path(__file__).parent.parent.parent.parent / "path"
        mock_path_instance = MagicMock()
        mock_path_instance.parent.parent.parent.parent.__truediv__.return_value.exists.return_value = False
        mock_path.return_value = mock_path_instance
        generator = ContentGenerator()

        # Should use default context from _get_default_brand_context()
        assert "real estate content writer" in generator.brand_context.lower()
        assert "prohibited terms" in generator.brand_context.lower()


def test_system_message_includes_brand_context(mock_settings, mock_anthropic_client):
    """Test that system message includes brand context."""
    generator = ContentGenerator()
    system_message = generator._build_system_message("aggregators")

    assert generator.brand_context in system_message
    assert "aggregators" in system_message.lower()


# ============================================================================
# Tests: ContentGenerator - generate_field
# ============================================================================


@pytest.mark.asyncio
async def test_generate_field_success(mock_settings, mock_anthropic_client, sample_project_data):
    """Test successful field generation."""
    generator = ContentGenerator()

    result = await generator.generate_field(
        field_name="meta_title",
        structured_data=sample_project_data,
        template_type="aggregators",
        content_variant="standard",
    )

    assert isinstance(result, GeneratedField)
    assert result.field_name == "meta_title"
    assert result.content == "Generated content for field"
    assert result.character_count == len("Generated content for field")
    assert result.template_type == "aggregators"
    assert result.token_usage == {"input": 100, "output": 50}
    assert result.generation_cost > 0


@pytest.mark.asyncio
async def test_generate_field_respects_character_limit(mock_settings, mock_anthropic_client, sample_project_data):
    """Test that generate_field checks character limit and sets within_limit flag."""
    # Mock response with content that exceeds meta_title limit (60 chars)
    long_content = "A" * 100
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=long_content)]
    mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)
    mock_anthropic_client.messages_create = AsyncMock(return_value=mock_response)

    generator = ContentGenerator()
    result = await generator.generate_field(
        field_name="meta_title",
        structured_data=sample_project_data,
        template_type="aggregators",
    )

    assert result.character_count == 100
    assert result.within_limit is False  # Exceeds 60 char limit


@pytest.mark.asyncio
async def test_generate_field_within_character_limit(mock_settings, mock_anthropic_client, sample_project_data):
    """Test that content within limit has within_limit=True."""
    short_content = "Marina Vista Dubai Marina"
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=short_content)]
    mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)
    mock_anthropic_client.messages_create = AsyncMock(return_value=mock_response)

    generator = ContentGenerator()
    result = await generator.generate_field(
        field_name="meta_title",
        structured_data=sample_project_data,
        template_type="aggregators",
    )

    assert result.character_count == len(short_content)
    assert result.within_limit is True  # Within 60 char limit


@pytest.mark.asyncio
async def test_generate_field_handles_api_error(mock_settings, mock_anthropic_client, sample_project_data):
    """Test graceful error handling when API fails."""
    # Make the mock raise a generic exception that will be retried then wrapped
    mock_anthropic_client.messages_create = AsyncMock(
        side_effect=Exception("API request failed")
    )

    generator = ContentGenerator()

    # The ContentGenerator wraps exceptions in ValueError after MAX_RETRIES
    with pytest.raises(ValueError, match="Content generation failed"):
        await generator.generate_field(
            field_name="meta_title",
            structured_data=sample_project_data,
            template_type="aggregators",
        )


@pytest.mark.asyncio
async def test_generate_field_invalid_field_name(mock_settings, mock_anthropic_client, sample_project_data):
    """Test that invalid field name raises ValueError."""
    generator = ContentGenerator()

    with pytest.raises(ValueError, match="Unknown field"):
        await generator.generate_field(
            field_name="invalid_field",
            structured_data=sample_project_data,
            template_type="aggregators",
        )


# ============================================================================
# Tests: ContentGenerator - generate_all
# ============================================================================


@pytest.mark.asyncio
async def test_generate_all_returns_content_output(mock_settings, mock_anthropic_client, sample_project_data):
    """Test that generate_all returns ContentOutput with all fields generated."""
    from app.services.template_fields import get_fields_for_template

    generator = ContentGenerator()

    with patch("app.services.content_generator.asyncio.sleep", new_callable=AsyncMock):
        result = await generator.generate_all(
            base_context=sample_project_data,
            rich_context=sample_project_data,
            template_type="aggregators",
            content_variant="standard",
        )

    assert isinstance(result, ContentOutput)
    assert result.template_type == "aggregators"
    expected_field_count = len(get_fields_for_template("aggregators"))
    assert len(result.fields) == expected_field_count
    assert all(isinstance(f, GeneratedField) for f in result.fields.values())


@pytest.mark.asyncio
async def test_generate_all_tracks_total_cost(mock_settings, mock_anthropic_client, sample_project_data):
    """Test that generate_all correctly aggregates total cost."""
    generator = ContentGenerator()

    with patch("app.services.content_generator.asyncio.sleep", new_callable=AsyncMock):
        result = await generator.generate_all(
            base_context=sample_project_data,
            rich_context=sample_project_data,
            template_type="aggregators",
        )

    # Calculate expected cost
    total_input = result.total_token_usage["input"]
    total_output = result.total_token_usage["output"]
    expected_cost = float(
        (Decimal(total_input) * COST_PER_INPUT_TOKEN) +
        (Decimal(total_output) * COST_PER_OUTPUT_TOKEN)
    )

    assert result.total_cost == pytest.approx(expected_cost, rel=1e-5)
    assert result.total_cost > 0


@pytest.mark.asyncio
async def test_generate_all_tracks_token_usage(mock_settings, mock_anthropic_client, sample_project_data):
    """Test that generate_all aggregates token usage correctly."""
    generator = ContentGenerator()

    with patch("app.services.content_generator.asyncio.sleep", new_callable=AsyncMock):
        result = await generator.generate_all(
            base_context=sample_project_data,
            rich_context=sample_project_data,
            template_type="aggregators",
        )

    assert "input" in result.total_token_usage
    assert "output" in result.total_token_usage
    assert result.total_token_usage["input"] > 0
    assert result.total_token_usage["output"] > 0

    # Sum individual field token usage
    total_input = sum(f.token_usage["input"] for f in result.fields.values())
    total_output = sum(f.token_usage["output"] for f in result.fields.values())

    assert result.total_token_usage["input"] == total_input
    assert result.total_token_usage["output"] == total_output


@pytest.mark.asyncio
async def test_generate_all_handles_partial_failure(mock_settings, mock_anthropic_client, sample_project_data):
    """Test that generate_all continues when individual field generation fails."""
    from app.services.template_fields import get_fields_for_template

    total_fields = len(get_fields_for_template("aggregators"))

    # Track call count to fail ALL retry attempts for the 3rd field.
    # generate_field retries MAX_RETRIES (3) times, so calls 3, 4, 5 must all fail.
    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count in (3, 4, 5):
            raise Exception("Simulated failure")

        response = MagicMock()
        response.content = [MagicMock(text="Generated content")]
        response.usage = MagicMock(input_tokens=100, output_tokens=50)
        return response

    mock_anthropic_client.messages_create = AsyncMock(side_effect=side_effect)

    generator = ContentGenerator()
    with patch("app.services.content_generator.asyncio.sleep", new_callable=AsyncMock):
        result = await generator.generate_all(
            base_context=sample_project_data,
            rich_context=sample_project_data,
            template_type="aggregators",
        )

    # 3rd field fails all retries -> 1 error, rest succeed
    assert len(result.fields) == total_fields - 1
    assert len(result.errors) == 1
    assert "Failed to generate" in result.errors[0]


# ============================================================================
# Tests: ContentQAService - Initialization
# ============================================================================


def test_content_qa_service_initialization():
    """Test ContentQAService initialization."""
    qa_service = ContentQAService()

    assert qa_service is not None
    assert len(qa_service.PROHIBITED_TERMS) > 0
    assert len(qa_service.CORRECT_TERMINOLOGY) > 0
    assert len(qa_service.SEO_KEYWORDS) > 0


# ============================================================================
# Tests: ContentQAService - validate_content
# ============================================================================


def test_validate_content_returns_qa_report(sample_content_output, sample_project_data):
    """Test that validate_content returns QAReport with all checks."""
    qa_service = ContentQAService()

    report = qa_service.validate_content(
        content_output=sample_content_output,
        source_data=sample_project_data,
    )

    assert isinstance(report, QAReport)
    assert isinstance(report.overall_passed, bool)
    assert isinstance(report.overall_score, float)
    assert 0 <= report.overall_score <= 100
    assert len(report.checks) == 4  # 4 check types

    # Verify all check types are present
    check_types = {check.check_type for check in report.checks}
    assert "brand_compliance" in check_types
    assert "character_limits" in check_types
    assert "seo_score" in check_types
    assert "factual_accuracy" in check_types


def test_overall_score_aggregated(sample_content_output, sample_project_data):
    """Test that overall score is average of all check scores."""
    qa_service = ContentQAService()

    report = qa_service.validate_content(
        content_output=sample_content_output,
        source_data=sample_project_data,
    )

    # Calculate expected average
    total_score = sum(check.score for check in report.checks)
    expected_avg = total_score / len(report.checks)

    assert report.overall_score == pytest.approx(expected_avg, rel=0.01)


# ============================================================================
# Tests: ContentQAService - check_brand_compliance
# ============================================================================


def test_brand_compliance_passes_clean_content():
    """Test that clean content without prohibited terms passes."""
    qa_service = ContentQAService()

    clean_field = GeneratedField(
        field_name="meta_title",
        content="Marina Vista by Emaar - Dubai Marina Apartments",
        character_count=50,
        within_limit=True,
        template_type="aggregators",
        token_usage={"input": 100, "output": 50},
        generation_cost=0.001,
    )

    result = qa_service.check_brand_compliance({"meta_title": clean_field})

    assert result.passed is True
    assert result.score >= 80.0
    assert len(result.issues) == 0


def test_brand_compliance_catches_prohibited_terms():
    """Test that prohibited terms like 'world-class' are flagged."""
    qa_service = ContentQAService()

    bad_field = GeneratedField(
        field_name="meta_description",
        content="Discover world-class luxury living in a prime location with state-of-the-art amenities.",
        character_count=100,
        within_limit=True,
        template_type="aggregators",
        token_usage={"input": 100, "output": 50},
        generation_cost=0.001,
    )

    result = qa_service.check_brand_compliance({"meta_description": bad_field})

    assert len(result.issues) > 0
    # Should flag at least "world-class", "prime location", and "state-of-the-art"
    assert any("world-class" in issue["issue"].lower() for issue in result.issues)


def test_brand_compliance_checks_incorrect_terminology():
    """Test that incorrect terminology (e.g., 'flat' instead of 'apartment') is caught."""
    qa_service = ContentQAService()

    bad_field = GeneratedField(
        field_name="short_description",
        content="This flat is built by a renowned builder with completion expected soon.",
        character_count=80,
        within_limit=True,
        template_type="aggregators",
        token_usage={"input": 100, "output": 50},
        generation_cost=0.001,
    )

    result = qa_service.check_brand_compliance({"short_description": bad_field})

    assert len(result.issues) > 0
    # Should suggest "apartment" and "developer"
    assert any("apartment" in issue["issue"].lower() for issue in result.issues)
    assert any("developer" in issue["issue"].lower() for issue in result.issues)


# ============================================================================
# Tests: ContentQAService - check_character_limits
# ============================================================================


def test_character_limits_pass_within_limit():
    """Test that fields within character limits pass."""
    qa_service = ContentQAService()

    valid_field = GeneratedField(
        field_name="meta_title",
        content="Marina Vista Dubai Marina",
        character_count=26,
        within_limit=True,
        template_type="aggregators",
        token_usage={"input": 100, "output": 50},
        generation_cost=0.001,
    )

    result = qa_service.check_character_limits({"meta_title": valid_field})

    assert result.passed is True
    assert result.score == 100.0
    assert len(result.issues) == 0


def test_character_limits_fail_over_limit():
    """Test that fields exceeding character limits fail."""
    qa_service = ContentQAService()

    invalid_field = GeneratedField(
        field_name="meta_title",
        content="A" * 100,  # Exceeds 60 char limit
        character_count=100,
        within_limit=False,
        template_type="aggregators",
        token_usage={"input": 100, "output": 50},
        generation_cost=0.001,
    )

    result = qa_service.check_character_limits({"meta_title": invalid_field})

    assert result.passed is False
    assert len(result.issues) == 1
    assert result.issues[0]["severity"] == "critical"
    assert "exceeds character limit" in result.issues[0]["issue"].lower()


def test_character_limits_score_calculation():
    """Test that score is calculated as percentage of fields within limits."""
    qa_service = ContentQAService()

    fields = {
        "meta_title": GeneratedField(
            field_name="meta_title",
            content="Short",
            character_count=5,
            within_limit=True,
            template_type="aggregators",
            token_usage={"input": 100, "output": 50},
            generation_cost=0.001,
        ),
        "meta_description": GeneratedField(
            field_name="meta_description",
            content="A" * 200,  # Exceeds 160 limit
            character_count=200,
            within_limit=False,
            template_type="aggregators",
            token_usage={"input": 100, "output": 50},
            generation_cost=0.001,
        ),
    }

    result = qa_service.check_character_limits(fields)

    # 1 out of 2 passed, so score should be 50%
    assert result.score == 50.0
    assert result.passed is False  # Any field exceeding limit causes failure


# ============================================================================
# Tests: ContentQAService - check_seo_score
# ============================================================================


def test_seo_score_checks_keyword_presence(sample_project_data):
    """Test that SEO check verifies project name in meta title."""
    qa_service = ContentQAService()

    good_field = GeneratedField(
        field_name="meta_title",
        content="Marina Vista - Dubai Marina Apartments",
        character_count=42,
        within_limit=True,
        template_type="aggregators",
        token_usage={"input": 100, "output": 50},
        generation_cost=0.001,
    )

    result = qa_service.check_seo_score(
        {"meta_title": good_field},
        sample_project_data,
    )

    # Should pass project name and location checks
    assert result.score > 0
    # Verify no critical issues about missing project name
    project_issues = [i for i in result.issues if "project name" in i["issue"].lower()]
    assert len(project_issues) == 0


def test_seo_score_checks_meta_lengths(sample_project_data):
    """Test that SEO check verifies meta title and description lengths."""
    qa_service = ContentQAService()

    # Meta title with optimal length (50-60 chars)
    good_title = GeneratedField(
        field_name="meta_title",
        content="Marina Vista by Emaar - Dubai Marina Real Estate",  # 50 chars
        character_count=50,
        within_limit=True,
        template_type="aggregators",
        token_usage={"input": 100, "output": 50},
        generation_cost=0.001,
    )

    # Meta description with optimal length (150-160 chars)
    good_desc = GeneratedField(
        field_name="meta_description",
        content="Discover Marina Vista, a new property development by Emaar in Dubai Marina. Modern apartments starting from AED 1.2M. Expected handover Q4 2026.",  # ~150 chars
        character_count=150,
        within_limit=True,
        template_type="aggregators",
        token_usage={"input": 100, "output": 50},
        generation_cost=0.001,
    )

    result = qa_service.check_seo_score(
        {"meta_title": good_title, "meta_description": good_desc},
        sample_project_data,
    )

    # Should pass length checks
    length_issues = [i for i in result.issues if "not optimal" in i["issue"].lower()]
    assert len(length_issues) == 0


def test_seo_score_flags_suboptimal_lengths(sample_project_data):
    """Test that suboptimal meta lengths are flagged."""
    qa_service = ContentQAService()

    # Too short meta title
    short_title = GeneratedField(
        field_name="meta_title",
        content="Marina Vista",  # Only 13 chars (optimal: 50-60)
        character_count=13,
        within_limit=True,
        template_type="aggregators",
        token_usage={"input": 100, "output": 50},
        generation_cost=0.001,
    )

    result = qa_service.check_seo_score(
        {"meta_title": short_title},
        sample_project_data,
    )

    # Should flag length issue
    length_issues = [i for i in result.issues if "not optimal" in i["issue"].lower()]
    assert len(length_issues) > 0


# ============================================================================
# Tests: ContentQAService - check_factual_accuracy
# ============================================================================


def test_factual_accuracy_matches_source(sample_project_data):
    """Test that content matching source data passes factual accuracy."""
    qa_service = ContentQAService()

    accurate_fields = {
        "meta_title": GeneratedField(
            field_name="meta_title",
            content="Marina Vista by Emaar in Dubai Marina",
            character_count=41,
            within_limit=True,
            template_type="aggregators",
            token_usage={"input": 100, "output": 50},
            generation_cost=0.001,
        ),
        "short_description": GeneratedField(
            field_name="short_description",
            content="Marina Vista is a new development by Emaar located in Dubai Marina, Dubai.",
            character_count=75,
            within_limit=True,
            template_type="aggregators",
            token_usage={"input": 100, "output": 50},
            generation_cost=0.001,
        ),
    }

    result = qa_service.check_factual_accuracy(accurate_fields, sample_project_data)

    assert result.passed is True
    assert result.score >= 75.0
    # No critical issues about missing project name or location
    critical_issues = [i for i in result.issues if i["severity"] == "critical"]
    assert len(critical_issues) == 0


def test_factual_accuracy_catches_mismatch(sample_project_data):
    """Test that wrong project name or location triggers failure."""
    qa_service = ContentQAService()

    inaccurate_field = GeneratedField(
        field_name="meta_title",
        content="Dubai Heights by Damac in Downtown Dubai",  # Wrong name, developer, location
        character_count=44,
        within_limit=True,
        template_type="aggregators",
        token_usage={"input": 100, "output": 50},
        generation_cost=0.001,
    )

    result = qa_service.check_factual_accuracy(
        {"meta_title": inaccurate_field},
        sample_project_data,
    )

    assert result.passed is False
    # Should flag missing project name and location
    critical_issues = [i for i in result.issues if i["severity"] == "critical"]
    assert len(critical_issues) > 0


def test_factual_accuracy_checks_developer_mention(sample_project_data):
    """Test that developer name is checked in content."""
    qa_service = ContentQAService()

    # Content without developer mention
    field = GeneratedField(
        field_name="short_description",
        content="Marina Vista is located in Dubai Marina with great amenities.",
        character_count=65,
        within_limit=True,
        template_type="aggregators",
        token_usage={"input": 100, "output": 50},
        generation_cost=0.001,
    )

    result = qa_service.check_factual_accuracy({"short_description": field}, sample_project_data)

    # Should have a warning about missing developer
    developer_issues = [i for i in result.issues if "developer" in i["issue"].lower()]
    assert len(developer_issues) > 0


# ============================================================================
# Tests: PromptManager - Initialization
# ============================================================================


def test_prompt_manager_initialization():
    """Test PromptManager initialization with default prompts."""
    pm = PromptManager()

    assert pm is not None
    assert pm.default_prompts is not None
    assert len(pm.default_prompts) > 0


def test_default_prompts_cover_all_fields():
    """Test that default prompts include generic fallbacks and template-specific overrides."""
    pm = PromptManager()

    # Generic prompts (available as fallback for any template)
    generic_fields = ["meta_title", "meta_description", "h1", "url_slug", "image_alt"]
    for field in generic_fields:
        assert field in pm.default_prompts, f"Missing generic prompt: {field}"
        assert "content" in pm.default_prompts[field]
        assert "version" in pm.default_prompts[field]

    # Template-specific prompts use "template_type:field_name" keys
    template_types = ["aggregators", "opr", "mpp", "adop", "adre", "commercial"]
    for ttype in template_types:
        scoped_keys = [k for k in pm.default_prompts if k.startswith(f"{ttype}:")]
        assert len(scoped_keys) > 0, f"No template-specific prompts for {ttype}"
        for key in scoped_keys:
            assert "content" in pm.default_prompts[key]
            assert "version" in pm.default_prompts[key]


# ============================================================================
# Tests: PromptManager - get_prompt
# ============================================================================


@pytest.mark.asyncio
async def test_get_prompt_returns_template():
    """Test that get_prompt returns PromptTemplate for valid field."""
    pm = PromptManager()

    template = await pm.get_prompt(
        field_name="meta_title",
        template_type="aggregators",
        variant="standard",
    )

    assert isinstance(template, PromptTemplate)
    assert template.field_name == "meta_title"
    assert template.template_type == "aggregators"
    assert template.content is not None
    assert len(template.content) > 0
    assert template.version >= 1


@pytest.mark.asyncio
async def test_get_prompt_with_template_type():
    """Test that template-specific prompts work."""
    pm = PromptManager()

    template1 = await pm.get_prompt("meta_title", template_type="aggregators")
    template2 = await pm.get_prompt("meta_title", template_type="opr")

    # Both should be valid templates
    assert isinstance(template1, PromptTemplate)
    assert isinstance(template2, PromptTemplate)
    assert template1.template_type == "aggregators"
    assert template2.template_type == "opr"


@pytest.mark.asyncio
async def test_get_prompt_fallback_to_default():
    """Test that unknown field returns generic prompt."""
    pm = PromptManager()

    template = await pm.get_prompt(
        field_name="unknown_field",
        template_type="aggregators",
    )

    assert isinstance(template, PromptTemplate)
    assert template.field_name == "unknown_field"
    assert "unknown_field" in template.content


# ============================================================================
# Tests: PromptManager - format_prompt
# ============================================================================


def test_format_prompt_substitutes_variables(sample_project_data):
    """Test that format_prompt replaces placeholders with actual data."""
    pm = PromptManager()

    template = PromptTemplate(
        field_name="test",
        template_type="aggregators",
        content="Project: {project_name}, Developer: {developer}, Location: {location}",
    )

    formatted = pm.format_prompt(template, sample_project_data)

    assert "Marina Vista" in formatted
    assert "Emaar" in formatted
    assert "Dubai Marina, Dubai" in formatted
    # Placeholders should be replaced
    assert "{project_name}" not in formatted
    assert "{developer}" not in formatted
    assert "{location}" not in formatted


def test_format_prompt_handles_missing_data():
    """Test that missing data keys are replaced with defaults."""
    pm = PromptManager()

    template = PromptTemplate(
        field_name="test",
        template_type="aggregators",
        content="Project: {project_name}, Price: {starting_price}",
    )

    # Empty data
    formatted = pm.format_prompt(template, {})

    assert "Unknown Project" in formatted  # Default for missing project_name
    assert "Price on request" in formatted  # Default for missing price


def test_format_prompt_with_list_fields(sample_project_data):
    """Test that list fields (amenities, property_types) are formatted correctly."""
    pm = PromptManager()

    template = PromptTemplate(
        field_name="test",
        template_type="aggregators",
        content="Amenities: {amenities}, Types: {property_types}",
    )

    formatted = pm.format_prompt(template, sample_project_data)

    # Should format list as comma-separated
    assert "Swimming Pool" in formatted
    assert "Gym" in formatted
    assert "1BR" in formatted


def test_format_prompt_price_formatting():
    """Test that prices are formatted correctly."""
    pm = PromptManager()

    template = PromptTemplate(
        field_name="test",
        template_type="aggregators",
        content="Price: {starting_price}",
    )

    # Test with different price ranges
    test_cases = [
        (1200000, "AED 1.2M"),
        (500000, "AED 500K"),
        (2500000, "AED 2.5M"),
    ]

    for price, expected_format in test_cases:
        formatted = pm.format_prompt(template, {"starting_price": price})
        assert expected_format in formatted


# ============================================================================
# Tests: PromptManager - Helper Methods
# ============================================================================


def test_format_list_helper():
    """Test _format_list helper method."""
    pm = PromptManager()

    # Empty list
    assert pm._format_list([]) == "Not specified"

    # Short list
    assert pm._format_list(["A", "B", "C"]) == "A, B, C"

    # Long list (shows first 3 + count)
    long_list = ["A", "B", "C", "D", "E", "F"]
    result = pm._format_list(long_list)
    assert "A, B, C" in result
    assert "3 more" in result


def test_format_price_helper():
    """Test _format_price helper method."""
    pm = PromptManager()

    # None
    assert pm._format_price(None) == "Price on request"

    # Large numbers
    assert pm._format_price(1500000) == "AED 1.5M"
    assert pm._format_price(2000000) == "AED 2.0M"

    # Thousands
    assert pm._format_price(500000) == "AED 500K"
    assert pm._format_price(750000) == "AED 750K"

    # Small numbers
    assert pm._format_price(999) == "AED 999"


# ============================================================================
# Tests: Edge Cases and Error Handling
# ============================================================================


def test_generated_field_dataclass():
    """Test GeneratedField dataclass initialization."""
    field = GeneratedField(
        field_name="test",
        content="test content",
        character_count=12,
        within_limit=True,
        template_type="aggregators",
        token_usage={"input": 10, "output": 5},
        generation_cost=0.0001,
    )

    assert field.field_name == "test"
    assert field.content == "test content"
    assert field.prompt_version is None  # Optional field


def test_content_output_dataclass():
    """Test ContentOutput dataclass initialization."""
    output = ContentOutput(
        fields={},
        template_type="aggregators",
        total_token_usage={"input": 100, "output": 50},
        total_cost=0.01,
    )

    assert output.fields == {}
    assert output.errors == []  # Default factory


def test_qa_check_result_add_issue():
    """Test QACheckResult.add_issue method."""
    result = QACheckResult(
        check_type="test",
        passed=True,
        score=100.0,
    )

    result.add_issue(field="test_field", issue="test issue", severity="warning")

    assert len(result.issues) == 1
    assert result.issues[0]["field"] == "test_field"
    assert result.issues[0]["issue"] == "test issue"
    assert result.issues[0]["severity"] == "warning"


def test_qa_report_get_check():
    """Test QAReport.get_check method."""
    check1 = QACheckResult(check_type="brand_compliance", passed=True, score=100.0)
    check2 = QACheckResult(check_type="seo_score", passed=False, score=60.0)

    report = QAReport(
        overall_passed=False,
        overall_score=80.0,
        checks=[check1, check2],
        critical_issues=0,
        warnings=2,
    )

    brand_check = report.get_check("brand_compliance")
    assert brand_check is not None
    assert brand_check.check_type == "brand_compliance"

    missing_check = report.get_check("nonexistent")
    assert missing_check is None


# ============================================================================
# Tests: Cost Calculation
# ============================================================================


def test_cost_per_token_constants():
    """Test that cost constants are defined correctly."""
    assert COST_PER_INPUT_TOKEN == Decimal("0.000003")
    assert COST_PER_OUTPUT_TOKEN == Decimal("0.000015")


def test_generation_cost_calculation():
    """Test that generation cost is calculated correctly."""
    input_tokens = 1000
    output_tokens = 500

    expected_cost = float(
        (Decimal(input_tokens) * COST_PER_INPUT_TOKEN) +
        (Decimal(output_tokens) * COST_PER_OUTPUT_TOKEN)
    )

    # Should be $0.003 + $0.0075 = $0.0105
    assert expected_cost == pytest.approx(0.0105, rel=1e-5)


# ============================================================================
# Risk Mitigation Tests - Rate Limits, Retries, Character Enforcement
# ============================================================================


class TestContentGeneratorRetryLogic:
    """Tests for retry and rate limit handling in ContentGenerator."""

    @pytest.mark.asyncio
    async def test_rate_limit_retry_succeeds(self, mock_settings):
        """Test that rate limit errors trigger retry and eventually succeed."""
        import anthropic as anthropic_mod

        with patch("app.services.content_generator.anthropic_service") as mock_service:
            # First call: rate limit. Second call: success.
            rate_limit_error = anthropic_mod.RateLimitError(
                message="Rate limit exceeded",
                response=MagicMock(status_code=429),
                body=None,
            )
            success_response = MagicMock()
            success_response.content = [MagicMock(text="Short title here")]
            success_response.usage = MagicMock(input_tokens=100, output_tokens=20)

            mock_service.messages_create = AsyncMock(
                side_effect=[rate_limit_error, success_response]
            )

            with patch("app.services.content_generator.asyncio.sleep", new_callable=AsyncMock):
                gen = ContentGenerator()
                result = await gen.generate_field(
                    field_name="meta_title",
                    structured_data={"project_name": "Test"},
                    template_type="aggregators",
                )

            assert result.field_name == "meta_title"
            assert result.content == "Short title here"
            assert mock_service.messages_create.call_count == 2

    @pytest.mark.asyncio
    async def test_timeout_retry_succeeds(self, mock_settings):
        """Test that timeout errors trigger retry and eventually succeed."""
        import anthropic as anthropic_mod

        with patch("app.services.content_generator.anthropic_service") as mock_service:
            timeout_error = anthropic_mod.APITimeoutError(request=MagicMock())
            success_response = MagicMock()
            success_response.content = [MagicMock(text="Valid content")]
            success_response.usage = MagicMock(input_tokens=100, output_tokens=20)

            mock_service.messages_create = AsyncMock(
                side_effect=[timeout_error, success_response]
            )

            with patch("app.services.content_generator.asyncio.sleep", new_callable=AsyncMock):
                gen = ContentGenerator()
                result = await gen.generate_field(
                    field_name="meta_title",
                    structured_data={"project_name": "Test"},
                    template_type="aggregators",
                )

            assert result.content == "Valid content"
            assert mock_service.messages_create.call_count == 2

    @pytest.mark.asyncio
    async def test_all_retries_exhausted_raises(self, mock_settings):
        """Test that ValueError is raised after all retries are exhausted."""
        import anthropic as anthropic_mod

        with patch("app.services.content_generator.anthropic_service") as mock_service:
            rate_limit_error = anthropic_mod.RateLimitError(
                message="Rate limit exceeded",
                response=MagicMock(status_code=429),
                body=None,
            )
            mock_service.messages_create = AsyncMock(side_effect=rate_limit_error)

            with patch("app.services.content_generator.asyncio.sleep", new_callable=AsyncMock):
                gen = ContentGenerator()
                with pytest.raises(ValueError, match="after 3 attempts"):
                    await gen.generate_field(
                        field_name="meta_title",
                        structured_data={"project_name": "Test"},
                        template_type="aggregators",
                    )

            assert mock_service.messages_create.call_count == MAX_RETRIES

    @pytest.mark.asyncio
    async def test_over_limit_triggers_retry_with_stricter_prompt(self, mock_settings):
        """Test that over-limit content triggers retry with character enforcement."""
        with patch("app.services.content_generator.anthropic_service") as mock_service:
            # First response: too long (meta_title limit is 60)
            long_response = MagicMock()
            long_response.content = [MagicMock(text="A" * 80)]
            long_response.usage = MagicMock(input_tokens=100, output_tokens=30)

            # Second response: within limit
            short_response = MagicMock()
            short_response.content = [MagicMock(text="Marina Vista Dubai Apartments")]
            short_response.usage = MagicMock(input_tokens=120, output_tokens=15)

            mock_service.messages_create = AsyncMock(
                side_effect=[long_response, short_response]
            )

            with patch("app.services.content_generator.asyncio.sleep", new_callable=AsyncMock):
                gen = ContentGenerator()
                result = await gen.generate_field(
                    field_name="meta_title",
                    structured_data={"project_name": "Marina Vista"},
                    template_type="aggregators",
                    character_limit=60,
                )

            assert result.within_limit is True
            assert result.character_count <= 60
            assert mock_service.messages_create.call_count == 2

            # Verify second call included stricter prompt
            second_call_args = mock_service.messages_create.call_args_list[1]
            second_message = second_call_args[1]["messages"][0]["content"]
            assert "CRITICAL" in second_message
            assert "60 characters or fewer" in second_message

    @pytest.mark.asyncio
    async def test_inter_field_delay_applied(self, mock_settings):
        """Test that inter-field delay is applied between sequential generations."""
        from app.services.template_fields import get_fields_for_template

        total_fields = len(get_fields_for_template("aggregators"))

        with patch("app.services.content_generator.anthropic_service") as mock_service:
            success_response = MagicMock()
            success_response.content = [MagicMock(text="Short text")]
            success_response.usage = MagicMock(input_tokens=100, output_tokens=20)
            mock_service.messages_create = AsyncMock(return_value=success_response)

            with patch("app.services.content_generator.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                gen = ContentGenerator()
                ctx = {"project_name": "Test"}
                await gen.generate_all(
                    base_context=ctx,
                    rich_context=ctx,
                    template_type="aggregators",
                )

            # No inter-field delay -- removed (rate limiting handled by
            # centralized Anthropic client with exponential backoff).
            # Only retry sleeps (1.0s) should appear.
            inter_field_calls = [
                call for call in mock_sleep.call_args_list
                if call[0] == (0.5,)
            ]
            assert len(inter_field_calls) == 0

    def test_retry_constants_defined(self):
        """Test that retry constants have reasonable values."""
        assert MAX_RETRIES == 3
        assert RETRY_DELAY_BASE == 1.0
        assert RETRY_DELAY_MAX == 15.0
