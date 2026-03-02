"""Tests for tiered generation context system and prompt placeholder resolution."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4

from app.services.job_manager import JobManager
from app.services.content_generator import ContentGenerator
from app.services.prompt_manager import PromptManager, PromptTemplate


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_structured():
    """Create a mock StructuredProject with all 19 fields."""
    s = MagicMock()
    s.project_name = "Marina Heights"
    s.developer = "Emaar Properties"
    s.emirate = "Dubai"
    s.community = "Dubai Marina"
    s.sub_community = "Marina Gate"
    s.property_type = "Residential"
    s.price_min = 1_500_000
    s.price_max = 3_200_000
    s.currency = "AED"
    s.price_per_sqft = 1800
    s.bedrooms = ["Studio", "1BR", "2BR", "3BR"]
    s.total_units = 450
    s.floors = 42
    s.handover_date = "Q4 2026"
    s.launch_date = "Q1 2025"
    s.amenities = ["Swimming pool", "Gym", "Kids play area"]
    s.key_features = ["Waterfront living", "Smart home technology"]
    s.payment_plan = {"down_payment": "20%", "during_construction": "50%", "on_handover": "30%"}
    s.description = "A waterfront residential development in Dubai Marina."
    return s


def _make_floor_plans():
    """Create sample floor plan data as would come from pipeline context."""
    return {
        "floor_plans": [
            {"unit_type": "1BR", "total_sqft": 750.0, "bedrooms": 1, "bathrooms": 1.0},
            {"unit_type": "2BR", "total_sqft": 1200.0, "bedrooms": 2, "bathrooms": 2.0},
            {"unit_type": "3BR", "total_sqft": 1800.0, "bedrooms": 3, "bathrooms": 3.5},
        ]
    }


def _make_manifest():
    """Create sample image manifest."""
    return {
        "entries": [
            {"category": "hero", "path": "images/hero_01.webp"},
            {"category": "hero", "path": "images/hero_02.webp"},
            {"category": "amenity", "path": "images/amenity_01.webp"},
            {"category": "floor_plan", "path": "images/fp_01.webp"},
            {"category": "floor_plan", "path": "images/fp_02.webp"},
        ]
    }


def _make_extraction_data():
    """Create sample extracted text data."""
    return {
        "pages": {
            "1": "Marina Heights by Emaar Properties. A stunning waterfront development.",
            "2": "Starting from AED 1.5M. 1, 2, and 3 bedroom apartments available.",
            "3": "World-class amenities including swimming pool, gymnasium, and kids play area.",
        }
    }


def _make_job_manager():
    """Create a JobManager with mocked dependencies."""
    repo = MagicMock()
    repo.db = MagicMock()
    queue = MagicMock()
    return JobManager(repo, queue)


# ---------------------------------------------------------------------------
# Task 1: _build_base_context tests
# ---------------------------------------------------------------------------

class TestBuildBaseContext:
    def test_complete(self):
        """All 19 structured fields + floor_plan_summary + image_metadata present."""
        jm = _make_job_manager()
        structured = _make_structured()
        fp = _make_floor_plans()
        manifest = _make_manifest()

        ctx = jm._build_base_context(structured, fp, manifest)

        # All 19 structured fields
        assert ctx["project_name"] == "Marina Heights"
        assert ctx["developer"] == "Emaar Properties"
        assert ctx["emirate"] == "Dubai"
        assert ctx["community"] == "Dubai Marina"
        assert ctx["sub_community"] == "Marina Gate"
        assert ctx["property_type"] == "Residential"
        assert ctx["price_min"] == 1_500_000
        assert ctx["price_max"] == 3_200_000
        assert ctx["currency"] == "AED"
        assert ctx["price_per_sqft"] == 1800
        assert ctx["bedrooms"] == ["Studio", "1BR", "2BR", "3BR"]
        assert ctx["total_units"] == 450
        assert ctx["floors"] == 42
        assert ctx["handover_date"] == "Q4 2026"
        assert ctx["launch_date"] == "Q1 2025"
        assert ctx["amenities"] == ["Swimming pool", "Gym", "Kids play area"]
        assert ctx["key_features"] == ["Waterfront living", "Smart home technology"]
        assert isinstance(ctx["payment_plan"], dict)
        assert ctx["description"] == "A waterfront residential development in Dubai Marina."

        # Floor plan summary
        fps = ctx["floor_plan_summary"]
        assert fps["count"] == 3
        assert sorted(fps["unit_types"]) == ["1BR", "2BR", "3BR"]
        assert "750" in fps["sqft_range"]
        assert "1,800" in fps["sqft_range"]

        # Image metadata
        img = ctx["image_metadata"]
        assert img["total_images"] == 5
        assert img["categories"]["hero"] == 2
        assert img["categories"]["floor_plan"] == 2
        assert img["categories"]["amenity"] == 1

    def test_missing_optional(self):
        """Handles None floor plans, manifest, and optional structured fields."""
        jm = _make_job_manager()
        structured = _make_structured()
        structured.sub_community = None
        structured.price_per_sqft = None
        structured.total_units = None
        structured.floors = None
        structured.launch_date = None

        ctx = jm._build_base_context(structured, None, None)

        assert ctx["sub_community"] is None
        assert ctx["price_per_sqft"] is None
        assert ctx["floor_plan_summary"]["count"] == 0
        assert ctx["image_metadata"]["total_images"] == 0


# ---------------------------------------------------------------------------
# Task 1: _build_rich_context tests
# ---------------------------------------------------------------------------

class TestBuildRichContext:
    def test_includes_text(self):
        """Rich context has all base keys + extracted_text."""
        jm = _make_job_manager()
        structured = _make_structured()
        base = jm._build_base_context(structured, None, None)
        extraction = _make_extraction_data()

        rich = jm._build_rich_context(base, extraction)

        # All base keys present
        for key in base:
            assert key in rich

        # Extracted text present and non-empty
        assert "extracted_text" in rich
        assert "Marina Heights" in rich["extracted_text"]
        assert "Starting from AED 1.5M" in rich["extracted_text"]

    def test_empty_extraction(self):
        """Rich context with empty extraction data still works."""
        jm = _make_job_manager()
        structured = _make_structured()
        base = jm._build_base_context(structured, None, None)

        rich = jm._build_rich_context(base, {})

        assert rich["extracted_text"] == ""


# ---------------------------------------------------------------------------
# Task 4: _needs_rich_context tests
# ---------------------------------------------------------------------------

class TestNeedsRichContext:
    def test_paragraph_fields(self):
        """Paragraph/description field names trigger rich context."""
        assert JobManager._needs_rich_context("about_paragraph", None) is True
        assert JobManager._needs_rich_context("location_description", None) is True
        assert JobManager._needs_rich_context("project_overview", None) is True
        # "about_the_developer" contains "about", so it correctly gets rich context
        assert JobManager._needs_rich_context("about_the_developer", None) is True

    def test_short_fields(self):
        """Short-form fields use base context."""
        assert JobManager._needs_rich_context("meta_title", 60) is False
        assert JobManager._needs_rich_context("h1_tag", 70) is False
        assert JobManager._needs_rich_context("hero_h2", 100) is False

    def test_high_char_limit(self):
        """Fields with char_limit > 300 trigger rich context."""
        assert JobManager._needs_rich_context("some_field", 500) is True
        assert JobManager._needs_rich_context("some_field", 301) is True
        assert JobManager._needs_rich_context("some_field", 300) is False
        assert JobManager._needs_rich_context("some_field", 200) is False

    def test_content_generator_has_same_logic(self):
        """ContentGenerator._needs_rich_context matches JobManager logic."""
        assert ContentGenerator._needs_rich_context("about_paragraph", None) is True
        assert ContentGenerator._needs_rich_context("meta_title", 60) is False
        assert ContentGenerator._needs_rich_context("long_field", 500) is True


# ---------------------------------------------------------------------------
# Task 2: Prompt placeholder resolution tests
# ---------------------------------------------------------------------------

class TestPromptPlaceholderResolution:
    def setup_method(self):
        self.pm = PromptManager()

    def test_price_min_resolves_to_starting_price(self):
        """format_prompt resolves price_min when starting_price is missing."""
        template = PromptTemplate(
            field_name="test",
            template_type="aggregators",
            content="Starting from {starting_price} in {location}.",
        )
        data = {"price_min": 1_500_000, "community": "Dubai Marina"}

        result = self.pm.format_prompt(template, data)

        assert "AED" in result
        assert "1.5M" in result
        assert "Dubai Marina" in result
        assert "Unknown" not in result

    def test_bedrooms_resolves_to_property_types(self):
        """format_prompt resolves bedrooms list to property_types placeholder."""
        template = PromptTemplate(
            field_name="test",
            template_type="aggregators",
            content="Available: {property_types}.",
        )
        data = {"bedrooms": ["Studio", "1BR", "2BR"]}

        result = self.pm.format_prompt(template, data)

        assert "Studio" in result
        assert "1BR" in result
        assert "Not specified" not in result

    def test_community_resolves_to_location(self):
        """format_prompt resolves community to location placeholder."""
        template = PromptTemplate(
            field_name="test",
            template_type="aggregators",
            content="Located in {location}, {emirate}.",
        )
        data = {"community": "Business Bay", "emirate": "Dubai"}

        result = self.pm.format_prompt(template, data)

        assert "Business Bay" in result
        assert "Dubai" in result

    def test_price_range_placeholder(self):
        """format_prompt builds price_range from price_min + price_max."""
        template = PromptTemplate(
            field_name="test",
            template_type="aggregators",
            content="Price range: {price_range}.",
        )
        data = {"price_min": 1_500_000, "price_max": 3_200_000}

        result = self.pm.format_prompt(template, data)

        assert "AED" in result
        assert "1.5M" in result
        assert "3.2M" in result

    def test_payment_plan_dict_formatting(self):
        """format_prompt formats dict payment_plan as readable string."""
        template = PromptTemplate(
            field_name="test",
            template_type="aggregators",
            content="Payment: {payment_plan}.",
        )
        data = {
            "payment_plan": {
                "down_payment": "20%",
                "during_construction": "50%",
                "on_handover": "30%",
            }
        }

        result = self.pm.format_prompt(template, data)

        assert "20%" in result
        assert "50%" in result
        assert "30%" in result
        assert "Available on request" not in result

    def test_floor_plan_summary_placeholders(self):
        """format_prompt resolves floor plan summary fields."""
        template = PromptTemplate(
            field_name="test",
            template_type="aggregators",
            content="{floor_plan_count} floor plans, types: {unit_types}, range: {sqft_range}.",
        )
        data = {
            "floor_plan_summary": {
                "count": 3,
                "unit_types": ["1BR", "2BR", "3BR"],
                "sqft_range": "750 - 1,800 sqft",
            }
        }

        result = self.pm.format_prompt(template, data)

        assert "3 floor plans" in result
        assert "1BR" in result
        assert "750 - 1,800 sqft" in result

    def test_backward_compatible_with_direct_keys(self):
        """Old-style data with direct starting_price/location keys still works."""
        template = PromptTemplate(
            field_name="test",
            template_type="aggregators",
            content="{project_name} at {starting_price} in {location}.",
        )
        data = {
            "project_name": "Test Project",
            "starting_price": 2_000_000,
            "location": "Downtown Dubai",
        }

        result = self.pm.format_prompt(template, data)

        assert "Test Project" in result
        assert "AED" in result
        assert "2.0M" in result
        assert "Downtown Dubai" in result
