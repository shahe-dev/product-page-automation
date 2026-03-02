"""
Unit tests for Floor Plan Extractor Service

Tests the FloorPlanExtractor service including:
- Vision OCR extraction with mocked Claude API
- JSON parsing (valid and malformed)
- Text extraction fallback
- Data merging (vision + text)
- Deduplication at 95% threshold
- Per-field source tracking
- Error handling

Run with: pytest tests/test_floor_plan.py -v
"""

import base64
import io
import json
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Optional

import pytest
from PIL import Image

from app.services.floor_plan_extractor import (
    FloorPlanExtractor,
    FloorPlanData,
    FloorPlanExtractionResult,
)
from app.utils.pdf_helpers import ExtractedImage, ImageMetadata
from app.services.deduplication_service import (
    DeduplicationResult,
    FLOOR_PLAN_SIMILARITY_THRESHOLD,
)


def create_test_image(width: int = 800, height: int = 600,
                      color: tuple = (255, 255, 255)) -> bytes:
    """Create a test image with PIL."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_distinct_image(pattern_id: int, width: int = 800, height: int = 600) -> bytes:
    """Create a visually distinct image with unique patterns."""
    img = Image.new("RGB", (width, height), (255, 255, 255))
    pixels = img.load()

    # Create different patterns based on pattern_id
    for y in range(height):
        for x in range(width):
            if pattern_id == 1:
                # Diagonal stripes
                if (x + y) % 40 < 20:
                    pixels[x, y] = (200, 50, 50)
            elif pattern_id == 2:
                # Checkerboard
                if (x // 50 + y // 50) % 2 == 0:
                    pixels[x, y] = (50, 200, 50)
            elif pattern_id == 3:
                # Horizontal lines
                if y % 30 < 15:
                    pixels[x, y] = (50, 50, 200)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_extracted_image(page_num: int = 1,
                          image_bytes: Optional[bytes] = None) -> ExtractedImage:
    """Create an ExtractedImage with metadata."""
    if image_bytes is None:
        image_bytes = create_test_image()

    metadata = ImageMetadata(
        page_number=page_num,
        source="embedded",
        width=800,
        height=600,
        format="png",
    )

    return ExtractedImage(
        image_bytes=image_bytes,
        metadata=metadata,
    )


class TestFloorPlanExtractor:
    """Test suite for FloorPlanExtractor initialization."""

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_init_with_defaults(self, mock_anthropic, mock_settings):
        """Test FloorPlanExtractor initialization with default settings."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-api-key"
        mock_settings_obj.ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()

        mock_anthropic.assert_called_once_with(api_key="test-api-key")
        assert extractor._model == "claude-3-5-sonnet-20241022"

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_init_with_custom_values(self, mock_anthropic, mock_settings):
        """Test FloorPlanExtractor initialization with custom API key and model."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "default-key"
        mock_settings_obj.ANTHROPIC_MODEL = "default-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor(
            api_key="custom-key",
            model="claude-opus-4-5-20251101"
        )

        mock_anthropic.assert_called_once_with(api_key="custom-key")
        assert extractor._model == "claude-opus-4-5-20251101"


class TestExtractFloorPlans:
    """Test suite for extract_floor_plans method."""

    @pytest.mark.asyncio
    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    async def test_extract_empty_input(self, mock_anthropic, mock_settings):
        """Test extract_floor_plans with empty input list."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()
        result = await extractor.extract_floor_plans([])

        assert result.total_input == 0
        assert result.total_extracted == 0
        assert result.total_duplicates == 0
        assert len(result.floor_plans) == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    async def test_extract_single_floor_plan(self, mock_anthropic, mock_settings):
        """Test extract_floor_plans with single valid floor plan."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        # Mock Claude API response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "unit_type": "2BR",
            "bedrooms": 2,
            "bathrooms": 2.0,
            "total_sqft": 1250.0,
            "balcony_sqft": 150.0,
            "builtup_sqft": 1100.0,
            "room_dimensions": {"living": "4.2m x 3.8m", "bedroom1": "3.5m x 3.2m"},
            "features": ["maid_room", "walk_in_closet"],
            "confidence": 0.92
        })

        mock_client = Mock()
        mock_client.messages.create = Mock(return_value=mock_response)
        mock_anthropic.return_value = mock_client

        extractor = FloorPlanExtractor()
        images = [create_extracted_image(page_num=1)]
        result = await extractor.extract_floor_plans(images)

        assert result.total_input == 1
        assert result.total_extracted == 1
        assert result.total_duplicates == 0
        assert len(result.floor_plans) == 1
        assert len(result.errors) == 0

        fp = result.floor_plans[0]
        assert fp.unit_type == "2BR"
        assert fp.unit_type_source == "floor_plan_image"
        assert fp.bedrooms == 2
        assert fp.bedrooms_source == "floor_plan_image"
        assert fp.bathrooms == 2.0
        assert fp.bathrooms_source == "floor_plan_image"
        assert fp.total_sqft == 1250.0
        assert fp.total_sqft_source == "floor_plan_image"
        assert fp.balcony_sqft == 150.0
        assert fp.balcony_sqft_source == "floor_plan_image"
        assert fp.builtup_sqft == 1100.0
        assert fp.builtup_sqft_source == "floor_plan_image"
        assert fp.room_dimensions == {"living": "4.2m x 3.8m", "bedroom1": "3.5m x 3.2m"}
        assert fp.dimensions_source == "floor_plan_image"
        assert fp.features == ["maid_room", "walk_in_closet"]
        assert fp.features_source == "floor_plan_image"
        assert fp.confidence == 0.92

    @pytest.mark.asyncio
    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    async def test_extract_with_deduplication(self, mock_anthropic, mock_settings):
        """Test that duplicate floor plans are detected at 95% threshold."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        # Mock Claude API response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "unit_type": "1BR",
            "bedrooms": 1,
            "bathrooms": 1.0,
            "total_sqft": 800.0,
            "confidence": 0.85
        })

        mock_client = Mock()
        mock_client.messages.create = Mock(return_value=mock_response)
        mock_anthropic.return_value = mock_client

        extractor = FloorPlanExtractor()

        # Create identical images (should be duplicates)
        img_bytes = create_test_image(color=(100, 150, 200))
        images = [
            create_extracted_image(page_num=1, image_bytes=img_bytes),
            create_extracted_image(page_num=2, image_bytes=img_bytes),
            create_extracted_image(page_num=3, image_bytes=img_bytes),
        ]

        result = await extractor.extract_floor_plans(images)

        assert result.total_input == 3
        assert result.total_extracted == 1  # Only first one extracted
        assert result.total_duplicates == 2  # Two duplicates skipped
        assert len(result.floor_plans) == 1

    @pytest.mark.asyncio
    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    async def test_extract_with_page_text_fallback(self, mock_anthropic, mock_settings):
        """Test extract_floor_plans with page_text_map fallback for missing data."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        # Mock Claude API response with missing unit_type
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "unit_type": None,  # Missing in image
            "bedrooms": 2,
            "bathrooms": 2.0,
            "total_sqft": 1250.0,
            "confidence": 0.88
        })

        mock_client = Mock()
        mock_client.messages.create = Mock(return_value=mock_response)
        mock_anthropic.return_value = mock_client

        extractor = FloorPlanExtractor()
        images = [create_extracted_image(page_num=5)]

        # Provide text map with unit type info
        page_text_map = {
            4: "Previous page content",
            5: "Floor plan for 2BR apartment with balcony",
            6: "Next page content"
        }

        result = await extractor.extract_floor_plans(images, page_text_map)

        assert result.total_input == 1
        assert result.total_extracted == 1
        assert len(result.floor_plans) == 1

        fp = result.floor_plans[0]
        assert fp.unit_type == "2BR"  # From text fallback
        assert fp.unit_type_source == "text_fallback"
        assert fp.bedrooms == 2  # From image
        assert fp.bedrooms_source == "floor_plan_image"

    @pytest.mark.asyncio
    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    async def test_extract_with_api_error(self, mock_anthropic, mock_settings):
        """Test extract_floor_plans handles API errors gracefully."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        # Mock API error
        import anthropic
        mock_client = Mock()
        mock_request = Mock()
        mock_client.messages.create = Mock(
            side_effect=anthropic.APIError("API Error", request=mock_request, body=None)
        )
        mock_anthropic.return_value = mock_client

        extractor = FloorPlanExtractor()
        images = [create_extracted_image(page_num=1)]

        result = await extractor.extract_floor_plans(images)

        # API error is caught and returns zero-confidence result
        assert result.total_input == 1
        assert result.total_extracted == 1
        assert len(result.floor_plans) == 1
        assert result.floor_plans[0].confidence == 0.0
        assert result.floor_plans[0].unit_type is None


class TestParseVisionResponse:
    """Test suite for _parse_vision_response method."""

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_parse_valid_json(self, mock_anthropic, mock_settings):
        """Test parsing valid JSON response."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "unit_type": "Studio",
            "bedrooms": 0,
            "bathrooms": 1.0,
            "total_sqft": 500.0,
            "features": ["open_kitchen"],
            "confidence": 0.78
        })

        fp = extractor._parse_vision_response(mock_response)

        assert fp.unit_type == "Studio"
        assert fp.unit_type_source == "floor_plan_image"
        assert fp.bedrooms == 0
        assert fp.bedrooms_source == "floor_plan_image"
        assert fp.bathrooms == 1.0
        assert fp.bathrooms_source == "floor_plan_image"
        assert fp.total_sqft == 500.0
        assert fp.total_sqft_source == "floor_plan_image"
        assert fp.features == ["open_kitchen"]
        assert fp.features_source == "floor_plan_image"
        assert fp.confidence == 0.78

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_parse_json_with_markdown_fences(self, mock_anthropic, mock_settings):
        """Test parsing JSON wrapped in markdown code fences."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '```json\n{"unit_type": "3BR", "bedrooms": 3, "confidence": 0.91}\n```'

        fp = extractor._parse_vision_response(mock_response)

        assert fp.unit_type == "3BR"
        assert fp.bedrooms == 3
        assert fp.confidence == 0.91

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_parse_invalid_json(self, mock_anthropic, mock_settings):
        """Test parsing malformed JSON returns zero-confidence result."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "This is not valid JSON at all"

        fp = extractor._parse_vision_response(mock_response)

        assert fp.confidence == 0.0
        assert fp.unit_type is None
        assert fp.bedrooms is None

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_parse_partial_data(self, mock_anthropic, mock_settings):
        """Test parsing JSON with only some fields present."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "bedrooms": 1,
            "total_sqft": 650.0,
            "confidence": 0.65
        })

        fp = extractor._parse_vision_response(mock_response)

        assert fp.unit_type is None
        assert fp.unit_type_source == ""
        assert fp.bedrooms == 1
        assert fp.bedrooms_source == "floor_plan_image"
        assert fp.total_sqft == 650.0
        assert fp.total_sqft_source == "floor_plan_image"
        assert fp.bathrooms is None
        assert fp.confidence == 0.65

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_parse_with_room_dimensions(self, mock_anthropic, mock_settings):
        """Test parsing with room dimensions (only from image, never text)."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "unit_type": "2BR",
            "bedrooms": 2,
            "room_dimensions": {
                "living": "5.2m x 4.8m",
                "bedroom1": "3.8m x 3.5m",
                "bedroom2": "3.2m x 3.0m",
                "kitchen": "3.0m x 2.5m"
            },
            "confidence": 0.89
        })

        fp = extractor._parse_vision_response(mock_response)

        assert fp.room_dimensions is not None
        assert fp.dimensions_source == "floor_plan_image"
        assert len(fp.room_dimensions) == 4
        assert fp.room_dimensions["living"] == "5.2m x 4.8m"
        assert fp.room_dimensions["bedroom1"] == "3.8m x 3.5m"


class TestExtractFromText:
    """Test suite for _extract_from_text method."""

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_extract_studio_pattern(self, mock_anthropic, mock_settings):
        """Test extracting studio unit type from text."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()
        page_text_map = {
            1: "This is a studio apartment with modern finishes"
        }

        result = extractor._extract_from_text(page_text_map, 1)

        assert result.get("unit_type") == "STUDIO"

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_extract_1br_pattern(self, mock_anthropic, mock_settings):
        """Test extracting 1BR unit type from text."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()
        page_text_map = {
            5: "1BR apartment with balcony and city views"
        }

        result = extractor._extract_from_text(page_text_map, 5)

        assert result.get("unit_type") == "1BR"

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_extract_2br_pattern(self, mock_anthropic, mock_settings):
        """Test extracting 2BR unit type from text."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()
        page_text_map = {
            10: "2BR apartment with 2 bathrooms"
        }

        result = extractor._extract_from_text(page_text_map, 10)

        assert result.get("unit_type") == "2BR"

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_extract_bed_pattern(self, mock_anthropic, mock_settings):
        """Test extracting '3 bed' pattern from text."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()
        page_text_map = {
            15: "Spacious 3 bed apartment with parking"
        }

        result = extractor._extract_from_text(page_text_map, 15)

        assert result.get("unit_type") == "3BR"

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_extract_penthouse_pattern(self, mock_anthropic, mock_settings):
        """Test extracting penthouse unit type from text."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()
        page_text_map = {
            20: "Luxury penthouse with rooftop terrace"
        }

        result = extractor._extract_from_text(page_text_map, 20)

        assert result.get("unit_type") == "PENTHOUSE"

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_extract_from_adjacent_pages(self, mock_anthropic, mock_settings):
        """Test extraction considers adjacent pages (+/- 1)."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()
        page_text_map = {
            9: "Previous page mentions 2BR",
            10: "Current page with floor plan image",
            11: "Next page has additional details"
        }

        result = extractor._extract_from_text(page_text_map, 10)

        assert result.get("unit_type") == "2BR"

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_extract_no_matching_pattern(self, mock_anthropic, mock_settings):
        """Test extraction returns empty dict when no patterns match."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()
        page_text_map = {
            25: "This text has no unit type information at all"
        }

        result = extractor._extract_from_text(page_text_map, 25)

        assert result == {}

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_extract_empty_text(self, mock_anthropic, mock_settings):
        """Test extraction with empty text map."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()
        page_text_map = {}

        result = extractor._extract_from_text(page_text_map, 30)

        assert result == {}


class TestMergeData:
    """Test suite for _merge_data method."""

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_merge_with_empty_text_data(self, mock_anthropic, mock_settings):
        """Test merging when text data is empty."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()

        vision = FloorPlanData(
            unit_type="2BR",
            unit_type_source="floor_plan_image",
            bedrooms=2,
            bedrooms_source="floor_plan_image",
        )

        merged = extractor._merge_data(vision, {}, 1)

        assert merged.unit_type == "2BR"
        assert merged.unit_type_source == "floor_plan_image"

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_merge_vision_data_takes_priority(self, mock_anthropic, mock_settings):
        """Test that vision data takes priority over text data."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()

        vision = FloorPlanData(
            unit_type="2BR",
            unit_type_source="floor_plan_image",
            bedrooms=2,
            bedrooms_source="floor_plan_image",
        )

        text_data = {"unit_type": "1BR"}  # Conflicting data

        merged = extractor._merge_data(vision, text_data, 1)

        # Vision data should win
        assert merged.unit_type == "2BR"
        assert merged.unit_type_source == "floor_plan_image"

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_merge_text_fallback_for_missing_fields(self, mock_anthropic, mock_settings):
        """Test that text data is used as fallback for missing vision fields."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()

        vision = FloorPlanData(
            unit_type=None,  # Missing in vision
            bedrooms=2,
            bedrooms_source="floor_plan_image",
        )

        text_data = {"unit_type": "2BR"}

        merged = extractor._merge_data(vision, text_data, 1)

        # Text fallback should be used
        assert merged.unit_type == "2BR"
        assert merged.unit_type_source == "text_fallback"
        assert merged.bedrooms == 2
        assert merged.bedrooms_source == "floor_plan_image"

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_merge_room_dimensions_only_from_vision(self, mock_anthropic, mock_settings):
        """Test that room dimensions NEVER come from text, only vision."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()

        # Vision with dimensions
        vision_with_dims = FloorPlanData(
            unit_type="2BR",
            unit_type_source="floor_plan_image",
            room_dimensions={"living": "5m x 4m"},
            dimensions_source="floor_plan_image",
        )

        # Text data (should not affect dimensions)
        text_data = {"unit_type": "2BR"}

        merged = extractor._merge_data(vision_with_dims, text_data, 1)

        assert merged.room_dimensions == {"living": "5m x 4m"}
        assert merged.dimensions_source == "floor_plan_image"

        # Vision without dimensions
        vision_no_dims = FloorPlanData(
            unit_type="2BR",
            unit_type_source="floor_plan_image",
            room_dimensions=None,
            dimensions_source="",
        )

        merged2 = extractor._merge_data(vision_no_dims, text_data, 1)

        # Dimensions should remain None (no text fallback)
        assert merged2.room_dimensions is None
        assert merged2.dimensions_source == ""


class TestDetectMediaType:
    """Test suite for _detect_media_type method."""

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_detect_png(self, mock_anthropic, mock_settings):
        """Test media type detection for PNG images."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()

        img = Image.new("RGB", (100, 100), (255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()

        media_type = extractor._detect_media_type(img_bytes)
        assert media_type == "image/png"

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_detect_jpeg(self, mock_anthropic, mock_settings):
        """Test media type detection for JPEG images."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()

        img = Image.new("RGB", (100, 100), (255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        img_bytes = buf.getvalue()

        media_type = extractor._detect_media_type(img_bytes)
        assert media_type == "image/jpeg"

    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    def test_detect_invalid_image(self, mock_anthropic, mock_settings):
        """Test media type detection for invalid image bytes."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        extractor = FloorPlanExtractor()

        # Invalid image bytes
        invalid_bytes = b"not an image at all"

        media_type = extractor._detect_media_type(invalid_bytes)
        assert media_type == "image/png"  # Default fallback


class TestSourceTracking:
    """Test suite for per-field source tracking."""

    @pytest.mark.asyncio
    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    async def test_all_data_from_image_source(self, mock_anthropic, mock_settings):
        """Test that all extracted fields have correct source='floor_plan_image'."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        # Mock Claude API response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "unit_type": "2BR",
            "bedrooms": 2,
            "bathrooms": 2.0,
            "total_sqft": 1250.0,
            "balcony_sqft": 150.0,
            "builtup_sqft": 1100.0,
            "room_dimensions": {"living": "4.2m x 3.8m"},
            "features": ["maid_room"],
            "confidence": 0.92
        })

        mock_client = Mock()
        mock_client.messages.create = Mock(return_value=mock_response)
        mock_anthropic.return_value = mock_client

        extractor = FloorPlanExtractor()
        images = [create_extracted_image(page_num=1)]
        result = await extractor.extract_floor_plans(images)

        fp = result.floor_plans[0]

        # All sources should be "floor_plan_image"
        assert fp.unit_type_source == "floor_plan_image"
        assert fp.bedrooms_source == "floor_plan_image"
        assert fp.bathrooms_source == "floor_plan_image"
        assert fp.total_sqft_source == "floor_plan_image"
        assert fp.balcony_sqft_source == "floor_plan_image"
        assert fp.builtup_sqft_source == "floor_plan_image"
        assert fp.dimensions_source == "floor_plan_image"
        assert fp.features_source == "floor_plan_image"

    @pytest.mark.asyncio
    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    async def test_mixed_source_tracking(self, mock_anthropic, mock_settings):
        """Test per-field source tracking with mixed sources."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        # Mock Claude API response with partial data
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "unit_type": None,  # Missing - will use text fallback
            "bedrooms": 1,
            "bathrooms": 1.0,
            "confidence": 0.75
        })

        mock_client = Mock()
        mock_client.messages.create = Mock(return_value=mock_response)
        mock_anthropic.return_value = mock_client

        extractor = FloorPlanExtractor()
        images = [create_extracted_image(page_num=3)]

        page_text_map = {
            3: "1BR apartment layout"
        }

        result = await extractor.extract_floor_plans(images, page_text_map)

        fp = result.floor_plans[0]

        # Mixed sources
        assert fp.unit_type_source == "text_fallback"
        assert fp.bedrooms_source == "floor_plan_image"
        assert fp.bathrooms_source == "floor_plan_image"
        assert fp.total_sqft_source == ""  # Not provided


class TestDeduplication:
    """Test suite for deduplication at 95% threshold."""

    @pytest.mark.asyncio
    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    async def test_deduplication_threshold(self, mock_anthropic, mock_settings):
        """Test that deduplication uses 95% threshold for floor plans."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        mock_client = Mock()
        mock_anthropic.return_value = mock_client

        extractor = FloorPlanExtractor()

        # Verify the threshold is set correctly
        assert extractor._dedup.threshold == FLOOR_PLAN_SIMILARITY_THRESHOLD
        assert FLOOR_PLAN_SIMILARITY_THRESHOLD == 0.95

    @pytest.mark.asyncio
    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    async def test_identical_images_deduplication(self, mock_anthropic, mock_settings):
        """Test that identical images are properly deduplicated."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '{"unit_type": "2BR", "confidence": 0.9}'

        mock_client = Mock()
        mock_client.messages.create = Mock(return_value=mock_response)
        mock_anthropic.return_value = mock_client

        extractor = FloorPlanExtractor()

        # Create multiple identical images
        img_bytes = create_test_image(color=(50, 100, 150))
        images = [
            create_extracted_image(page_num=i, image_bytes=img_bytes)
            for i in range(5)
        ]

        result = await extractor.extract_floor_plans(images)

        # Only first image should be extracted
        assert result.total_input == 5
        assert result.total_extracted == 1
        assert result.total_duplicates == 4

    @pytest.mark.asyncio
    @patch("app.services.floor_plan_extractor.get_settings")
    @patch("app.services.floor_plan_extractor.anthropic.Anthropic")
    async def test_different_images_no_deduplication(self, mock_anthropic, mock_settings):
        """Test that different images are not deduplicated."""
        mock_settings_obj = Mock()
        mock_settings_obj.ANTHROPIC_API_KEY = "test-key"
        mock_settings_obj.ANTHROPIC_MODEL = "test-model"
        mock_settings.return_value = mock_settings_obj

        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '{"unit_type": "2BR", "confidence": 0.9}'

        mock_client = Mock()
        mock_client.messages.create = Mock(return_value=mock_response)
        mock_anthropic.return_value = mock_client

        extractor = FloorPlanExtractor()

        # Create visually distinct images with different patterns
        images = [
            create_extracted_image(page_num=1, image_bytes=create_distinct_image(1)),
            create_extracted_image(page_num=2, image_bytes=create_distinct_image(2)),
            create_extracted_image(page_num=3, image_bytes=create_distinct_image(3)),
        ]

        result = await extractor.extract_floor_plans(images)

        # All images should be extracted (different patterns, not duplicates)
        assert result.total_input == 3
        assert result.total_extracted == 3
        assert result.total_duplicates == 0
