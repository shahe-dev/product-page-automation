"""
Unit tests for watermark detection and removal services.

Tests both WatermarkDetector and WatermarkRemover with mocked API calls
and synthetic test images.

Run with: pytest tests/test_watermark.py -v
"""

import io
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import Optional

import cv2
import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

from app.services.watermark_detector import (
    WatermarkDetector,
    WatermarkRegion,
    DetectionResult,
)
from app.services.watermark_remover import WatermarkRemover, RemovalResult


class TestImageGenerator:
    """Helper class to generate test images."""

    @staticmethod
    def create_test_image(width: int = 800, height: int = 600,
                         color: tuple = (100, 150, 200)) -> bytes:
        """Create a simple test image with some texture."""
        # Create base image
        img = Image.new("RGB", (width, height), color)
        draw = ImageDraw.Draw(img)

        # Add some simple shapes to give it texture/edges for quality scoring
        for i in range(0, width, 50):
            draw.line([(i, 0), (i, height)], fill=(120, 160, 210), width=1)
        for i in range(0, height, 50):
            draw.line([(0, i), (width, i)], fill=(120, 160, 210), width=1)

        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()

    @staticmethod
    def create_image_with_watermark(width: int = 800, height: int = 600) -> bytes:
        """Create an image with visible text watermark."""
        img = Image.new("RGB", (width, height), (100, 150, 200))
        draw = ImageDraw.Draw(img)

        # Draw white text as watermark
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except Exception:
            font = ImageFont.load_default()

        text = "WATERMARK"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width - text_width) // 2
        y = (height - text_height) // 2
        draw.text((x, y), text, fill=(255, 255, 255), font=font)

        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()

    @staticmethod
    def create_image_array(width: int = 800, height: int = 600) -> np.ndarray:
        """Create a numpy array image for OpenCV operations."""
        img = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
        return img


class TestWatermarkDetectorInit:
    """Test suite for WatermarkDetector initialization."""

    def test_init_with_default_settings(self):
        """Test detector initialization with default settings."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector()

            assert detector._client is not None
            assert detector._model == "claude-3-5-sonnet-20241022"

    def test_init_with_custom_api_key(self):
        """Test detector initialization with custom API key."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="default-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector(api_key="custom-key")

            assert detector._client is not None

    def test_init_with_custom_model(self):
        """Test detector initialization with custom model."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector(model="claude-3-opus-20240229")

            assert detector._model == "claude-3-opus-20240229"


class TestWatermarkDetectorParseResponse:
    """Test suite for WatermarkDetector response parsing."""

    def test_parse_valid_json_with_watermark(self):
        """Test parsing valid JSON response with watermark detected."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector()

        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "has_watermark": True,
            "confidence": 0.95,
            "watermarks": [
                {
                    "text": "Agency Logo",
                    "x": 100,
                    "y": 200,
                    "width": 300,
                    "height": 50,
                    "type": "logo"
                }
            ]
        })

        result = detector._parse_response(mock_response)

        assert result.has_watermark is True
        assert result.confidence == 0.95
        assert len(result.regions) == 1
        assert result.regions[0].x == 100
        assert result.regions[0].y == 200
        assert result.regions[0].width == 300
        assert result.regions[0].height == 50
        assert result.regions[0].text == "Agency Logo"
        assert result.regions[0].region_type == "logo"
        assert result.error is None

    def test_parse_valid_json_no_watermark(self):
        """Test parsing valid JSON response with no watermark."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector()

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "has_watermark": False,
            "confidence": 0.98,
            "watermarks": []
        })

        result = detector._parse_response(mock_response)

        assert result.has_watermark is False
        assert result.confidence == 0.98
        assert len(result.regions) == 0
        assert result.error is None

    def test_parse_json_with_markdown_fences(self):
        """Test parsing JSON wrapped in markdown code fences."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector()

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = """```
{
    "has_watermark": true,
    "confidence": 0.85,
    "watermarks": [
        {
            "text": "SAMPLE",
            "x": 50,
            "y": 50,
            "width": 200,
            "height": 40,
            "type": "text"
        }
    ]
}
```"""

        result = detector._parse_response(mock_response)

        assert result.has_watermark is True
        assert result.confidence == 0.85
        assert len(result.regions) == 1
        assert result.regions[0].text == "SAMPLE"

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns error result."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector()

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "This is not valid JSON"

        result = detector._parse_response(mock_response)

        assert result.has_watermark is False
        assert result.confidence == 0.0
        assert len(result.regions) == 0
        assert result.error is not None
        assert "Parse error" in result.error

    def test_parse_missing_fields(self):
        """Test parsing JSON with missing optional fields."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector()

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "has_watermark": True,
            "watermarks": [
                {
                    "x": 100,
                    "y": 100,
                    "width": 100,
                    "height": 100
                }
            ]
        })

        result = detector._parse_response(mock_response)

        assert result.has_watermark is True
        assert result.confidence == 0.0  # Default when missing
        assert len(result.regions) == 1
        assert result.regions[0].text == ""  # Default
        assert result.regions[0].region_type == "text"  # Default


class TestWatermarkDetectorDetect:
    """Test suite for WatermarkDetector.detect method."""

    @pytest.mark.asyncio
    async def test_detect_with_watermark_found(self):
        """Test detect method when watermark is found."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector()

        # Mock Anthropic client
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "has_watermark": True,
            "confidence": 0.92,
            "watermarks": [
                {
                    "text": "Agency Name",
                    "x": 50,
                    "y": 50,
                    "width": 200,
                    "height": 40,
                    "type": "text"
                }
            ]
        })

        detector._client.messages.create = Mock(return_value=mock_response)

        # Create test image
        image_bytes = TestImageGenerator.create_test_image()

        result = await detector.detect(image_bytes)

        assert result.has_watermark is True
        assert result.confidence == 0.92
        assert len(result.regions) == 1
        assert result.regions[0].text == "Agency Name"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_detect_with_no_watermark(self):
        """Test detect method when no watermark is found."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector()

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "has_watermark": False,
            "confidence": 0.95,
            "watermarks": []
        })

        detector._client.messages.create = Mock(return_value=mock_response)
        image_bytes = TestImageGenerator.create_test_image()

        result = await detector.detect(image_bytes)

        assert result.has_watermark is False
        assert result.confidence == 0.95
        assert len(result.regions) == 0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_detect_with_api_error(self):
        """Test detect method handles API errors gracefully."""
        import anthropic
        import httpx

        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector()

        # Create a mock request for APIError
        mock_request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")

        # Simulate API error
        detector._client.messages.create = Mock(
            side_effect=anthropic.APIError(
                "API connection failed",
                request=mock_request,
                body=None
            )
        )
        image_bytes = TestImageGenerator.create_test_image()

        result = await detector.detect(image_bytes)

        assert result.has_watermark is False
        assert result.confidence == 0.0
        assert result.error is not None
        assert "API error" in result.error

    @pytest.mark.asyncio
    async def test_detect_coordinate_scaling(self):
        """Test coordinate scaling from optimized to original dimensions."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector()

        # Create larger image that will be optimized
        large_image_bytes = TestImageGenerator.create_test_image(
            width=2048, height=1536
        )

        mock_response = Mock()
        mock_response.content = [Mock()]
        # Coordinates based on optimized dimensions (1024x768)
        mock_response.content[0].text = json.dumps({
            "has_watermark": True,
            "confidence": 0.90,
            "watermarks": [
                {
                    "text": "Logo",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 50,
                    "type": "logo"
                }
            ]
        })

        detector._client.messages.create = Mock(return_value=mock_response)

        result = await detector.detect(large_image_bytes)

        # Coordinates should be scaled up by 2x
        assert result.regions[0].x == 200  # 100 * 2
        assert result.regions[0].y == 200  # 100 * 2
        assert result.regions[0].width == 400  # 200 * 2
        assert result.regions[0].height == 100  # 50 * 2


class TestWatermarkDetectorBatch:
    """Test suite for WatermarkDetector.detect_batch method."""

    @pytest.mark.asyncio
    async def test_detect_batch_multiple_images(self):
        """Test batch detection on multiple images."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector()

        # Create test images
        images = [
            TestImageGenerator.create_test_image(),
            TestImageGenerator.create_test_image(),
            TestImageGenerator.create_test_image(),
        ]

        # Mock responses
        responses = [
            json.dumps({"has_watermark": True, "confidence": 0.9, "watermarks": []}),
            json.dumps({"has_watermark": False, "confidence": 0.95, "watermarks": []}),
            json.dumps({"has_watermark": True, "confidence": 0.88, "watermarks": []}),
        ]

        call_count = [0]

        def mock_create(*args, **kwargs):
            response = Mock()
            response.content = [Mock()]
            response.content[0].text = responses[call_count[0]]
            call_count[0] += 1
            return response

        detector._client.messages.create = Mock(side_effect=mock_create)

        results = await detector.detect_batch(images)

        assert len(results) == 3
        assert results[0].has_watermark is True
        assert results[1].has_watermark is False
        assert results[2].has_watermark is True

    @pytest.mark.asyncio
    async def test_detect_batch_empty_list(self):
        """Test batch detection with empty list."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector()

        results = await detector.detect_batch([])

        assert len(results) == 0


class TestWatermarkDetectorHelpers:
    """Test suite for WatermarkDetector helper methods."""

    def test_detect_media_type_jpeg(self):
        """Test media type detection for JPEG images."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector()

        img = Image.new("RGB", (100, 100))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        image_bytes = buf.getvalue()

        media_type = detector._detect_media_type(image_bytes)
        assert media_type == "image/jpeg"

    def test_detect_media_type_png(self):
        """Test media type detection for PNG images."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector()

        img = Image.new("RGB", (100, 100))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        image_bytes = buf.getvalue()

        media_type = detector._detect_media_type(image_bytes)
        assert media_type == "image/png"

    def test_detect_media_type_invalid(self):
        """Test media type detection with invalid data."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector()

        media_type = detector._detect_media_type(b"invalid data")
        assert media_type == "image/jpeg"  # Default fallback

    def test_get_dimensions(self):
        """Test getting image dimensions."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector()

        image_bytes = TestImageGenerator.create_test_image(width=800, height=600)
        width, height = detector._get_dimensions(image_bytes)

        assert width == 800
        assert height == 600

    def test_get_dimensions_invalid(self):
        """Test getting dimensions from invalid image."""
        with patch("app.services.watermark_detector.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                ANTHROPIC_API_KEY="test-key",
                ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"
            )
            detector = WatermarkDetector()

        width, height = detector._get_dimensions(b"invalid data")
        assert width == 0
        assert height == 0


class TestWatermarkRemoverInit:
    """Test suite for WatermarkRemover initialization."""

    def test_init_with_default_settings(self):
        """Test remover initialization with default settings."""
        remover = WatermarkRemover()

        assert remover.inpaint_radius == 3
        assert remover.max_degradation == 0.15
        assert remover.algorithm == cv2.INPAINT_TELEA

    def test_init_with_custom_settings(self):
        """Test remover initialization with custom settings."""
        remover = WatermarkRemover(
            inpaint_radius=5,
            max_degradation=0.20,
            algorithm=cv2.INPAINT_NS
        )

        assert remover.inpaint_radius == 5
        assert remover.max_degradation == 0.20
        assert remover.algorithm == cv2.INPAINT_NS


class TestWatermarkRemoverRemove:
    """Test suite for WatermarkRemover.remove method."""

    @pytest.mark.asyncio
    async def test_remove_no_watermark(self):
        """Test removal when no watermark is detected."""
        remover = WatermarkRemover()
        image_bytes = TestImageGenerator.create_test_image()

        detection = DetectionResult(
            has_watermark=False,
            confidence=0.95,
            regions=[]
        )

        result = await remover.remove(image_bytes, detection)

        assert result.cleaned_bytes == image_bytes
        assert result.original_bytes == image_bytes
        assert result.was_modified is False
        assert result.regions_processed == 0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_remove_with_watermark(self):
        """Test removal with detected watermark regions."""
        remover = WatermarkRemover()
        image_bytes = TestImageGenerator.create_test_image()

        regions = [
            WatermarkRegion(
                x=100,
                y=100,
                width=200,
                height=50,
                text="Logo",
                region_type="logo",
                confidence=0.9
            )
        ]

        detection = DetectionResult(
            has_watermark=True,
            confidence=0.9,
            regions=regions
        )

        result = await remover.remove(image_bytes, detection)

        # Check that processing occurred
        assert result.original_bytes == image_bytes
        assert result.regions_processed == 1
        assert result.quality_score_before > 0
        assert result.quality_score_after > 0
        assert result.quality_degradation >= 0
        assert result.error is None

        # If quality degradation is acceptable, image should be modified
        # Otherwise it falls back to original
        if result.was_modified:
            assert result.cleaned_bytes != image_bytes
            assert result.fell_back_to_original is False
        else:
            assert result.cleaned_bytes == image_bytes
            assert result.fell_back_to_original is True

    @pytest.mark.asyncio
    async def test_remove_with_quality_fallback(self):
        """Test removal falls back to original if quality degrades too much."""
        # Use very strict degradation threshold to force fallback
        remover = WatermarkRemover(max_degradation=0.0001)  # Extremely strict
        image_bytes = TestImageGenerator.create_test_image()

        # Large watermark region covering most of the image
        regions = [
            WatermarkRegion(
                x=50,
                y=50,
                width=700,
                height=500,
                text="HUGE WATERMARK",
                region_type="text",
                confidence=0.9
            )
        ]

        detection = DetectionResult(
            has_watermark=True,
            confidence=0.9,
            regions=regions
        )

        result = await remover.remove(image_bytes, detection)

        # With such a strict threshold, should fall back to original
        assert result.cleaned_bytes == image_bytes
        assert result.original_bytes == image_bytes
        assert result.was_modified is False
        assert result.fell_back_to_original is True
        assert result.regions_processed == 1
        # Quality degradation should exceed the very strict threshold
        assert result.quality_degradation > remover.max_degradation

    @pytest.mark.asyncio
    async def test_remove_with_invalid_image(self):
        """Test removal with invalid image data."""
        remover = WatermarkRemover()

        regions = [
            WatermarkRegion(x=10, y=10, width=50, height=50)
        ]

        detection = DetectionResult(
            has_watermark=True,
            confidence=0.9,
            regions=regions
        )

        result = await remover.remove(b"invalid image data", detection)

        assert result.cleaned_bytes == b"invalid image data"
        assert result.original_bytes == b"invalid image data"
        assert result.was_modified is False
        assert result.error is not None
        assert "Failed to decode image" in result.error

    @pytest.mark.asyncio
    async def test_remove_with_multiple_regions(self):
        """Test removal with multiple watermark regions."""
        remover = WatermarkRemover()
        image_bytes = TestImageGenerator.create_test_image()

        regions = [
            WatermarkRegion(x=50, y=50, width=100, height=30),
            WatermarkRegion(x=200, y=100, width=150, height=40),
            WatermarkRegion(x=400, y=200, width=120, height=35),
        ]

        detection = DetectionResult(
            has_watermark=True,
            confidence=0.92,
            regions=regions
        )

        result = await remover.remove(image_bytes, detection)

        assert result.was_modified is True
        assert result.regions_processed == 3
        assert result.error is None


class TestWatermarkRemoverBatch:
    """Test suite for WatermarkRemover.remove_batch method."""

    @pytest.mark.asyncio
    async def test_remove_batch_multiple_images(self):
        """Test batch removal on multiple images."""
        remover = WatermarkRemover()

        images = [
            (TestImageGenerator.create_test_image(), DetectionResult(has_watermark=False)),
            (TestImageGenerator.create_test_image(), DetectionResult(
                has_watermark=True,
                regions=[WatermarkRegion(x=50, y=50, width=100, height=30)]
            )),
            (TestImageGenerator.create_test_image(), DetectionResult(has_watermark=False)),
        ]

        results = await remover.remove_batch(images)

        assert len(results) == 3
        assert results[0].was_modified is False
        assert results[1].was_modified is True
        assert results[2].was_modified is False

    @pytest.mark.asyncio
    async def test_remove_batch_empty_list(self):
        """Test batch removal with empty list."""
        remover = WatermarkRemover()
        results = await remover.remove_batch([])
        assert len(results) == 0


class TestWatermarkRemoverHelpers:
    """Test suite for WatermarkRemover helper methods."""

    def test_create_mask_single_region(self):
        """Test mask creation with single watermark region."""
        remover = WatermarkRemover()
        image = TestImageGenerator.create_image_array(width=800, height=600)

        regions = [
            WatermarkRegion(x=100, y=100, width=200, height=50)
        ]

        mask = remover._create_mask(image, regions)

        assert mask.shape == (600, 800)
        assert mask.dtype == np.uint8
        # Check that watermark region is white (255)
        assert np.any(mask[100:150, 100:300] == 255)
        # Check that outside region is black (0)
        assert mask[0, 0] == 0

    def test_create_mask_multiple_regions(self):
        """Test mask creation with multiple watermark regions."""
        remover = WatermarkRemover()
        image = TestImageGenerator.create_image_array(width=800, height=600)

        regions = [
            WatermarkRegion(x=50, y=50, width=100, height=30),
            WatermarkRegion(x=200, y=100, width=150, height=40),
        ]

        mask = remover._create_mask(image, regions)

        assert mask.shape == (600, 800)
        # Both regions should be marked
        assert np.any(mask[50:80, 50:150] == 255)
        assert np.any(mask[100:140, 200:350] == 255)

    def test_create_mask_out_of_bounds(self):
        """Test mask creation handles out of bounds coordinates."""
        remover = WatermarkRemover()
        image = TestImageGenerator.create_image_array(width=800, height=600)

        # Region partially outside image bounds
        regions = [
            WatermarkRegion(x=-50, y=-50, width=200, height=100),
            WatermarkRegion(x=700, y=500, width=200, height=200),
        ]

        mask = remover._create_mask(image, regions)

        assert mask.shape == (600, 800)
        # Should clip to image bounds
        assert np.any(mask[0:50, 0:150] == 255)
        assert np.any(mask[500:600, 700:800] == 255)

    def test_compute_quality_score(self):
        """Test quality score computation."""
        remover = WatermarkRemover()

        # Create sharp image with high frequency content
        sharp_image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)

        score = remover._compute_quality_score(sharp_image)

        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)

    def test_compute_quality_score_consistent(self):
        """Test quality score is consistent for same image."""
        remover = WatermarkRemover()
        image = TestImageGenerator.create_image_array()

        score1 = remover._compute_quality_score(image)
        score2 = remover._compute_quality_score(image)

        assert score1 == score2

    def test_bytes_to_cv2_valid_image(self):
        """Test conversion from bytes to cv2 array."""
        remover = WatermarkRemover()
        image_bytes = TestImageGenerator.create_test_image()

        img_array = remover._bytes_to_cv2(image_bytes)

        assert img_array is not None
        assert isinstance(img_array, np.ndarray)
        assert len(img_array.shape) == 3
        assert img_array.shape[2] == 3  # BGR channels

    def test_bytes_to_cv2_invalid_data(self):
        """Test conversion handles invalid data."""
        remover = WatermarkRemover()

        img_array = remover._bytes_to_cv2(b"invalid image data")

        assert img_array is None

    def test_cv2_to_bytes_png(self):
        """Test conversion from cv2 array to PNG bytes."""
        remover = WatermarkRemover()
        img_array = TestImageGenerator.create_image_array()

        image_bytes = remover._cv2_to_bytes(img_array, fmt="png")

        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0

    def test_cv2_to_bytes_jpg(self):
        """Test conversion from cv2 array to JPG bytes."""
        remover = WatermarkRemover()
        img_array = TestImageGenerator.create_image_array()

        image_bytes = remover._cv2_to_bytes(img_array, fmt="jpg")

        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0

    def test_bytes_cv2_roundtrip(self):
        """Test roundtrip conversion bytes -> cv2 -> bytes."""
        remover = WatermarkRemover()
        original_bytes = TestImageGenerator.create_test_image()

        # Convert to cv2 and back
        img_array = remover._bytes_to_cv2(original_bytes)
        assert img_array is not None

        converted_bytes = remover._cv2_to_bytes(img_array, fmt="png")
        assert isinstance(converted_bytes, bytes)

        # Verify we can still read the converted bytes
        img_array2 = remover._bytes_to_cv2(converted_bytes)
        assert img_array2 is not None
        assert img_array.shape == img_array2.shape


class TestWatermarkRegion:
    """Test suite for WatermarkRegion dataclass."""

    def test_watermark_region_creation(self):
        """Test WatermarkRegion creation with all fields."""
        region = WatermarkRegion(
            x=100,
            y=200,
            width=300,
            height=50,
            text="Agency Logo",
            region_type="logo",
            confidence=0.95
        )

        assert region.x == 100
        assert region.y == 200
        assert region.width == 300
        assert region.height == 50
        assert region.text == "Agency Logo"
        assert region.region_type == "logo"
        assert region.confidence == 0.95

    def test_watermark_region_defaults(self):
        """Test WatermarkRegion defaults for optional fields."""
        region = WatermarkRegion(x=10, y=20, width=30, height=40)

        assert region.x == 10
        assert region.y == 20
        assert region.width == 30
        assert region.height == 40
        assert region.text == ""
        assert region.region_type == "text"
        assert region.confidence == 0.0


class TestDetectionResult:
    """Test suite for DetectionResult dataclass."""

    def test_detection_result_creation(self):
        """Test DetectionResult creation with all fields."""
        regions = [WatermarkRegion(x=10, y=20, width=30, height=40)]

        result = DetectionResult(
            has_watermark=True,
            confidence=0.92,
            regions=regions,
            error=None
        )

        assert result.has_watermark is True
        assert result.confidence == 0.92
        assert len(result.regions) == 1
        assert result.error is None

    def test_detection_result_defaults(self):
        """Test DetectionResult defaults."""
        result = DetectionResult()

        assert result.has_watermark is False
        assert result.confidence == 0.0
        assert result.regions == []
        assert result.error is None

    def test_detection_result_with_error(self):
        """Test DetectionResult with error message."""
        result = DetectionResult(error="API connection failed")

        assert result.has_watermark is False
        assert result.error == "API connection failed"


class TestRemovalResult:
    """Test suite for RemovalResult dataclass."""

    def test_removal_result_creation(self):
        """Test RemovalResult creation with all fields."""
        result = RemovalResult(
            cleaned_bytes=b"cleaned",
            original_bytes=b"original",
            was_modified=True,
            quality_score_before=0.85,
            quality_score_after=0.80,
            quality_degradation=0.059,
            fell_back_to_original=False,
            regions_processed=2,
            error=None
        )

        assert result.cleaned_bytes == b"cleaned"
        assert result.original_bytes == b"original"
        assert result.was_modified is True
        assert result.quality_score_before == 0.85
        assert result.quality_score_after == 0.80
        assert result.quality_degradation == 0.059
        assert result.fell_back_to_original is False
        assert result.regions_processed == 2
        assert result.error is None

    def test_removal_result_defaults(self):
        """Test RemovalResult defaults."""
        result = RemovalResult()

        assert result.cleaned_bytes == b""
        assert result.original_bytes == b""
        assert result.was_modified is False
        assert result.quality_score_before == 1.0
        assert result.quality_score_after == 1.0
        assert result.quality_degradation == 0.0
        assert result.fell_back_to_original is False
        assert result.regions_processed == 0
        assert result.error is None
