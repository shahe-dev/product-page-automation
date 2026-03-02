"""
Tests for Image Classifier and Deduplication Services.

Tests cover:
- DeduplicationService: perceptual hashing, similarity computation, registry management
- ImageClassifier: Claude Vision classification, category limits, deduplication
"""

import io
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from PIL import Image

from app.models.enums import ImageCategory
from app.services.deduplication_service import (
    HASH_SIZE,
    DEFAULT_SIMILARITY_THRESHOLD,
    FLOOR_PLAN_SIMILARITY_THRESHOLD,
    DeduplicationResult,
    DeduplicationService,
    compute_phash,
    compute_similarity,
    should_keep_page_render,
)
from app.services.image_classifier import (
    ImageClassifier,
    ClassificationResult,
    ClassificationOutput,
)
from app.utils.pdf_helpers import (
    ExtractedImage,
    ExtractionResult,
    ImageMetadata,
)


# Test fixtures

def create_test_image(width: int = 800, height: int = 600,
                     color: tuple = (255, 0, 0)) -> bytes:
    """Create a test image with specified dimensions and color."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_gradient_image(width: int = 800, height: int = 600, seed: int = 0) -> bytes:
    """Create a gradient image for testing similarity detection."""
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            pixels[x, y] = (
                int(255 * x / width + seed) % 256,
                int(255 * y / height + seed) % 256,
                128
            )
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_pattern_image(width: int = 800, height: int = 600,
                        pattern: str = "checkerboard") -> bytes:
    """Create a patterned image for testing."""
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            if pattern == "checkerboard":
                if (x // 50 + y // 50) % 2 == 0:
                    pixels[x, y] = (255, 255, 255)
                else:
                    pixels[x, y] = (0, 0, 0)
            elif pattern == "stripes":
                if x % 100 < 50:
                    pixels[x, y] = (255, 0, 0)
                else:
                    pixels[x, y] = (0, 0, 255)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_slightly_modified_image(original_bytes: bytes) -> bytes:
    """Create a slightly modified version of an image for duplicate testing."""
    img = Image.open(io.BytesIO(original_bytes))
    # Resize slightly
    new_size = (img.width - 10, img.height - 10)
    img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img_resized.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def red_image():
    """Fixture for a red test image."""
    return create_test_image(800, 600, (255, 0, 0))


@pytest.fixture
def blue_image():
    """Fixture for a blue test image."""
    return create_test_image(800, 600, (0, 0, 255))


@pytest.fixture
def gradient_image():
    """Fixture for a gradient test image."""
    return create_gradient_image()


@pytest.fixture
def checkerboard_image():
    """Fixture for a checkerboard pattern image."""
    return create_pattern_image(pattern="checkerboard")


@pytest.fixture
def stripes_image():
    """Fixture for a striped pattern image."""
    return create_pattern_image(pattern="stripes")


@pytest.fixture
def dedup_service():
    """Fixture providing a fresh DeduplicationService instance."""
    return DeduplicationService()


@pytest.fixture
def dedup_service_high_threshold():
    """Fixture providing DeduplicationService with floor plan threshold."""
    return DeduplicationService(threshold=FLOOR_PLAN_SIMILARITY_THRESHOLD)


# DeduplicationService Tests

class TestComputePhash:
    """Tests for compute_phash function."""

    def test_compute_phash_valid_image(self, red_image):
        """Test computing phash for valid image bytes."""
        phash = compute_phash(red_image)
        assert phash is not None
        assert len(str(phash)) > 0

    def test_compute_phash_different_images_different_hashes(
        self, gradient_image, checkerboard_image
    ):
        """Test that different images produce different hashes."""
        hash1 = compute_phash(gradient_image)
        hash2 = compute_phash(checkerboard_image)
        assert hash1 is not None
        assert hash2 is not None
        assert hash1 != hash2

    def test_compute_phash_invalid_bytes(self):
        """Test computing phash with invalid image bytes."""
        invalid_bytes = b"not an image"
        phash = compute_phash(invalid_bytes)
        assert phash is None

    def test_compute_phash_empty_bytes(self):
        """Test computing phash with empty bytes."""
        phash = compute_phash(b"")
        assert phash is None

    def test_compute_phash_identical_images_identical_hashes(self, red_image):
        """Test that identical images produce identical hashes."""
        hash1 = compute_phash(red_image)
        hash2 = compute_phash(red_image)
        assert hash1 == hash2


class TestComputeSimilarity:
    """Tests for compute_similarity function."""

    def test_compute_similarity_identical_hashes(self, red_image):
        """Test similarity of identical hashes is 1.0."""
        hash1 = compute_phash(red_image)
        hash2 = compute_phash(red_image)
        similarity = compute_similarity(hash1, hash2)
        assert similarity == 1.0

    def test_compute_similarity_different_hashes(
        self, gradient_image, checkerboard_image
    ):
        """Test similarity of very different hashes is low."""
        hash1 = compute_phash(gradient_image)
        hash2 = compute_phash(checkerboard_image)
        similarity = compute_similarity(hash1, hash2)
        # Different patterns should have different hashes
        assert 0.0 <= similarity < 1.0

    def test_compute_similarity_range(self, gradient_image, checkerboard_image):
        """Test similarity is always between 0.0 and 1.0."""
        hash1 = compute_phash(gradient_image)
        hash2 = compute_phash(checkerboard_image)
        similarity = compute_similarity(hash1, hash2)
        assert 0.0 <= similarity <= 1.0

    def test_compute_similarity_slightly_modified(self, red_image):
        """Test slightly modified images have high similarity."""
        modified_image = create_slightly_modified_image(red_image)
        hash1 = compute_phash(red_image)
        hash2 = compute_phash(modified_image)
        similarity = compute_similarity(hash1, hash2)
        # Slightly modified should still be similar
        assert similarity > 0.8


class TestDeduplicationService:
    """Tests for DeduplicationService class."""

    def test_init_default_threshold(self):
        """Test service initializes with default threshold."""
        service = DeduplicationService()
        assert service.threshold == DEFAULT_SIMILARITY_THRESHOLD

    def test_init_custom_threshold(self):
        """Test service initializes with custom threshold."""
        custom_threshold = 0.95
        service = DeduplicationService(threshold=custom_threshold)
        assert service.threshold == custom_threshold

    def test_reset_clears_registry(self, dedup_service, red_image):
        """Test reset method clears the hash registry."""
        dedup_service.register(red_image, 0)
        assert len(dedup_service._hash_registry) == 1

        dedup_service.reset()
        assert len(dedup_service._hash_registry) == 0

    def test_check_duplicate_no_prior_images(self, dedup_service, red_image):
        """Test check_duplicate with empty registry returns not duplicate."""
        result = dedup_service.check_duplicate(red_image)
        assert isinstance(result, DeduplicationResult)
        assert result.is_duplicate is False
        assert result.similarity == 0.0
        assert result.matched_index is None
        assert len(result.hash_value) > 0

    def test_check_duplicate_invalid_bytes(self, dedup_service):
        """Test check_duplicate with invalid bytes."""
        result = dedup_service.check_duplicate(b"invalid")
        assert result.is_duplicate is False
        assert result.similarity == 0.0
        assert result.hash_value == ""

    def test_register_adds_to_registry(self, dedup_service, red_image):
        """Test register adds image hash to registry."""
        hash_str = dedup_service.register(red_image, 0)
        assert hash_str is not None
        assert len(hash_str) > 0
        assert len(dedup_service._hash_registry) == 1

    def test_register_multiple_images(
        self, dedup_service, gradient_image, checkerboard_image
    ):
        """Test registering multiple images."""
        hash1 = dedup_service.register(gradient_image, 0)
        hash2 = dedup_service.register(checkerboard_image, 1)

        assert hash1 != hash2
        assert len(dedup_service._hash_registry) == 2

    def test_register_invalid_bytes(self, dedup_service):
        """Test register with invalid bytes returns None."""
        result = dedup_service.register(b"invalid", 0)
        assert result is None
        assert len(dedup_service._hash_registry) == 0

    def test_check_and_register_unique_image(self, dedup_service, red_image):
        """Test check_and_register with unique image."""
        result = dedup_service.check_and_register(red_image, 0)

        assert result.is_duplicate is False
        assert len(result.hash_value) > 0
        assert len(dedup_service._hash_registry) == 1

    def test_check_and_register_duplicate_detection(self, dedup_service, red_image):
        """Test check_and_register detects duplicates."""
        # Register first image
        result1 = dedup_service.check_and_register(red_image, 0)
        assert result1.is_duplicate is False

        # Try to register identical image
        result2 = dedup_service.check_and_register(red_image, 1)
        assert result2.is_duplicate is True
        assert result2.similarity == 1.0
        assert result2.matched_index == 0

        # Should not add duplicate to registry
        assert len(dedup_service._hash_registry) == 1

    def test_check_and_register_similar_image_above_threshold(
        self, dedup_service, red_image
    ):
        """Test similar image above threshold is detected as duplicate."""
        dedup_service.register(red_image, 0)

        # Create slightly modified version
        modified = create_slightly_modified_image(red_image)
        result = dedup_service.check_and_register(modified, 1)

        # Should detect as duplicate if similarity >= threshold
        if result.similarity >= dedup_service.threshold:
            assert result.is_duplicate is True
            assert result.matched_index == 0

    def test_high_threshold_stricter_matching(
        self, dedup_service_high_threshold, red_image
    ):
        """Test high threshold requires stricter matching."""
        dedup_service_high_threshold.register(red_image, 0)

        # Create slightly modified version
        modified = create_slightly_modified_image(red_image)
        hash1 = compute_phash(red_image)
        hash2 = compute_phash(modified)
        similarity = compute_similarity(hash1, hash2)

        # If similarity is between regular and floor plan threshold
        if (DEFAULT_SIMILARITY_THRESHOLD <= similarity <
            FLOOR_PLAN_SIMILARITY_THRESHOLD):
            result = dedup_service_high_threshold.check_duplicate(modified)
            # Should not be duplicate with high threshold
            assert result.is_duplicate is False


class TestShouldKeepPageRender:
    """Tests for should_keep_page_render function."""

    def test_skip_page_render_when_embedded_covers_content(self):
        """Verify page render is skipped when embedded image covers >70% of page area."""
        # Create a page where embedded image IS the main content
        page_size = (2480, 3508)  # A4 at 300 DPI
        embedded_size = (2200, 3200)  # Image with small margins (>70% coverage)

        # Embedded image (most of the page) - use pattern for realistic pHash
        embedded = Image.new("RGB", embedded_size, color="blue")
        from PIL import ImageDraw
        draw = ImageDraw.Draw(embedded)
        for i in range(0, embedded_size[0], 100):
            draw.line([(i, 0), (i, embedded_size[1])], fill="white", width=5)
        embedded_buf = io.BytesIO()
        embedded.save(embedded_buf, format="PNG")

        # Page render (embedded + white margins)
        page = Image.new("RGB", page_size, color="white")
        page.paste(embedded, (140, 154))  # Center the embedded image
        page_buf = io.BytesIO()
        page.save(page_buf, format="PNG")

        result = should_keep_page_render(
            page_buf.getvalue(),
            [embedded_buf.getvalue()]
        )

        assert result is False, "Page render should be skipped when embedded covers >70% of content"

    def test_keep_page_render_when_embedded_is_small_different_content(self):
        """Verify page render is kept when embedded is small and content differs."""
        # Page is much larger than embedded
        page_size = (2480, 3508)
        embedded_size = (500, 400)  # Small logo/icon - much less than 70%

        # Small embedded image with checkerboard pattern
        embedded = Image.new("RGB", embedded_size)
        pixels = embedded.load()
        for y in range(embedded_size[1]):
            for x in range(embedded_size[0]):
                if (x // 20 + y // 20) % 2 == 0:
                    pixels[x, y] = (255, 0, 0)
                else:
                    pixels[x, y] = (0, 0, 255)
        embedded_buf = io.BytesIO()
        embedded.save(embedded_buf, format="PNG")

        # Full page render with completely different content (stripes)
        page = Image.new("RGB", page_size)
        pixels = page.load()
        for y in range(page_size[1]):
            for x in range(page_size[0]):
                if (x // 100) % 2 == 0:
                    pixels[x, y] = (0, 255, 0)
                else:
                    pixels[x, y] = (255, 255, 0)
        page_buf = io.BytesIO()
        page.save(page_buf, format="PNG")

        result = should_keep_page_render(
            page_buf.getvalue(),
            [embedded_buf.getvalue()]
        )

        assert result is True, "Page render should be kept when embedded is small with different content"

    def test_should_keep_no_embedded_images(self, red_image):
        """Test page render should be kept when no embedded images."""
        result = should_keep_page_render(red_image, [])
        assert result is True

    def test_should_keep_different_embedded_images(
        self, checkerboard_image, stripes_image, gradient_image
    ):
        """Test page render kept when different from embedded."""
        embedded_list = [stripes_image, gradient_image]
        result = should_keep_page_render(checkerboard_image, embedded_list)
        assert result is True

    def test_should_discard_similar_to_embedded(self, red_image):
        """Test page render discarded when too similar to embedded."""
        # Use same image as embedded
        embedded_list = [red_image]
        result = should_keep_page_render(red_image, embedded_list)
        assert result is False

    def test_should_keep_invalid_render_bytes(self, red_image):
        """Test invalid render bytes returns True (keep by default)."""
        embedded_list = [red_image]
        result = should_keep_page_render(b"invalid", embedded_list)
        assert result is True

    def test_should_keep_when_embedded_invalid(self, red_image):
        """Test keeps page render when embedded images are invalid."""
        embedded_list = [b"invalid1", b"invalid2"]
        result = should_keep_page_render(red_image, embedded_list)
        assert result is True

    def test_should_keep_with_custom_threshold(self, gradient_image):
        """Test custom threshold affects decision."""
        modified = create_slightly_modified_image(gradient_image)
        embedded_list = [gradient_image]

        # With default threshold
        result_default = should_keep_page_render(
            modified, embedded_list, threshold=DEFAULT_SIMILARITY_THRESHOLD
        )

        # With very high threshold (0.99)
        result_high = should_keep_page_render(
            modified, embedded_list, threshold=0.99
        )

        # High threshold should be more lenient
        assert result_high is True


# ImageClassifier Tests

class TestImageClassifier:
    """Tests for ImageClassifier class."""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Mock Anthropic client."""
        with patch("app.services.image_classifier.anthropic.Anthropic") as mock:
            yield mock

    @pytest.fixture
    def classifier(self, mock_anthropic_client):
        """Fixture providing ImageClassifier with mocked API."""
        return ImageClassifier(api_key="test-key", model="test-model")

    def test_init_with_custom_params(self, mock_anthropic_client):
        """Test classifier initializes with custom parameters."""
        classifier = ImageClassifier(api_key="custom-key", model="custom-model")
        assert classifier._model == "custom-model"

    def test_parse_classification_valid_json(self, classifier):
        """Test parsing valid JSON classification response."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "category": "interior",
            "confidence": 0.95,
            "reasoning": "Modern living room with furniture",
            "alt_text": "Spacious living room with large windows"
        })

        result = classifier._parse_classification(mock_response)

        assert result.category == ImageCategory.INTERIOR
        assert result.confidence == 0.95
        assert "living room" in result.reasoning.lower()
        assert len(result.alt_text) > 0

    def test_parse_classification_with_markdown_fences(self, classifier):
        """Test parsing JSON wrapped in markdown code fences."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = """```json
{
    "category": "exterior",
    "confidence": 0.88,
    "reasoning": "Building facade",
    "alt_text": "Modern apartment building exterior"
}
```"""

        result = classifier._parse_classification(mock_response)

        assert result.category == ImageCategory.EXTERIOR
        assert result.confidence == 0.88

    def test_parse_classification_invalid_category(self, classifier):
        """Test parsing with invalid category falls back to OTHER."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "category": "invalid_category",
            "confidence": 0.5,
            "reasoning": "Unknown type",
            "alt_text": "Image"
        })

        result = classifier._parse_classification(mock_response)

        assert result.category == ImageCategory.OTHER

    def test_parse_classification_malformed_json(self, classifier):
        """Test parsing malformed JSON returns OTHER category."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Not valid JSON at all"

        result = classifier._parse_classification(mock_response)

        assert result.category == ImageCategory.OTHER
        assert result.confidence == 0.0
        assert "Parse error" in result.reasoning

    def test_parse_classification_missing_fields(self, classifier):
        """Test parsing JSON with missing fields uses defaults."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "category": "amenity"
        })

        result = classifier._parse_classification(mock_response)

        assert result.category == ImageCategory.AMENITY
        assert result.confidence == 0.0
        assert result.reasoning == ""
        assert result.alt_text == ""

    def test_should_retain_all_valid_categories(self, classifier):
        """Test should_retain returns True for all valid categories (limits disabled)."""
        # Category limits are now disabled - all valid categories are retained
        counts = {ImageCategory.INTERIOR: 100}
        result = classifier._should_retain(ImageCategory.INTERIOR, counts)
        assert result is True

        counts = {ImageCategory.LOGO: 50}
        result = classifier._should_retain(ImageCategory.LOGO, counts)
        assert result is True

        counts = {ImageCategory.FLOOR_PLAN: 200}
        result = classifier._should_retain(ImageCategory.FLOOR_PLAN, counts)
        assert result is True

    def test_should_retain_other_category(self, classifier):
        """Test should_retain always returns False for OTHER category."""
        counts = {}
        result = classifier._should_retain(ImageCategory.OTHER, counts)
        assert result is False

    def test_should_retain_zero_count(self, classifier):
        """Test should_retain with zero count for category."""
        counts = {ImageCategory.INTERIOR: 0}
        result = classifier._should_retain(ImageCategory.INTERIOR, counts)
        assert result is True

    def test_detect_media_type_png(self, classifier, red_image):
        """Test detecting PNG media type."""
        media_type = classifier._detect_media_type(red_image)
        assert media_type == "image/png"

    def test_detect_media_type_jpeg(self, classifier):
        """Test detecting JPEG media type."""
        img = Image.new("RGB", (100, 100), (255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        jpeg_bytes = buf.getvalue()

        media_type = classifier._detect_media_type(jpeg_bytes)
        assert media_type == "image/jpeg"

    def test_detect_media_type_invalid(self, classifier):
        """Test detecting media type for invalid bytes defaults to JPEG."""
        media_type = classifier._detect_media_type(b"invalid")
        assert media_type == "image/jpeg"

    def test_detect_media_type_jpg_normalized(self, classifier):
        """Test JPG is normalized to JPEG."""
        # PIL might return 'JPEG' for .jpg files
        img = Image.new("RGB", (100, 100), (255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        media_type = classifier._detect_media_type(buf.getvalue())
        assert media_type == "image/jpeg"


class TestImageClassifierIntegration:
    """Integration tests for classify_extraction method."""

    @pytest.fixture
    def mock_classify_single(self):
        """Mock _classify_single to avoid API calls."""
        with patch.object(
            ImageClassifier, "_classify_single", new_callable=AsyncMock
        ) as mock:
            yield mock

    @pytest.fixture
    def mock_logo_extraction(self):
        """Mock extract_logo_from_page to avoid API calls during logo extraction."""
        with patch.object(
            ImageClassifier, "extract_logo_from_page", new_callable=AsyncMock
        ) as mock:
            mock.return_value = None  # No logo found
            yield mock

    @pytest.fixture
    def classifier(self, mock_logo_extraction):
        """Classifier with mocked Anthropic client and logo extraction."""
        with patch("app.services.image_classifier.anthropic.Anthropic"):
            return ImageClassifier(api_key="test-key")

    @pytest.mark.asyncio
    async def test_classify_extraction_empty_input(
        self, classifier, mock_classify_single
    ):
        """Test classify_extraction with no images."""
        extraction = ExtractionResult(
            embedded=[],
            page_renders=[],
            total_pages=0
        )

        output = await classifier.classify_extraction(extraction)

        assert output.total_input == 0
        assert output.total_retained == 0
        assert output.total_duplicates == 0
        assert output.total_discarded == 0
        assert len(output.classified_images) == 0

    @pytest.mark.asyncio
    async def test_classify_extraction_embedded_only(
        self, classifier, mock_classify_single, red_image
    ):
        """Test classify_extraction with only embedded images."""
        mock_classify_single.return_value = ClassificationResult(
            category=ImageCategory.INTERIOR,
            confidence=0.9,
            alt_text="Test interior"
        )

        extracted_img = ExtractedImage(
            image_bytes=red_image,
            metadata=ImageMetadata(page_number=1, source="embedded")
        )
        extraction = ExtractionResult(
            embedded=[extracted_img],
            page_renders=[],
            total_pages=1
        )

        output = await classifier.classify_extraction(extraction)

        assert output.total_input == 1
        assert output.total_retained == 1
        assert output.total_duplicates == 0
        assert len(output.classified_images) == 1

    @pytest.mark.asyncio
    async def test_classify_extraction_dedup_for_all_categories(
        self, classifier, mock_classify_single, red_image
    ):
        """Test classify_extraction deduplicates all image categories.

        Universal perceptual deduplication at 95% threshold is now applied
        to ALL categories (not just floor plans) to catch near-identical images.
        """
        mock_classify_single.return_value = ClassificationResult(
            category=ImageCategory.EXTERIOR,
            confidence=0.9
        )

        # Create two identical images
        img1 = ExtractedImage(
            image_bytes=red_image,
            metadata=ImageMetadata(page_number=1, source="embedded")
        )
        img2 = ExtractedImage(
            image_bytes=red_image,
            metadata=ImageMetadata(page_number=2, source="embedded")
        )

        extraction = ExtractionResult(
            embedded=[img1, img2],
            page_renders=[],
            total_pages=2
        )

        output = await classifier.classify_extraction(extraction)

        # Second identical image should be deduplicated
        assert output.total_input == 2
        assert output.total_retained == 1
        assert output.total_duplicates == 1

    @pytest.mark.asyncio
    async def test_classify_extraction_deduplication_floor_plans(
        self, classifier, mock_classify_single, red_image
    ):
        """Test classify_extraction removes duplicate floor plans."""
        mock_classify_single.return_value = ClassificationResult(
            category=ImageCategory.FLOOR_PLAN,
            confidence=0.9
        )

        # Create two identical floor plan images
        img1 = ExtractedImage(
            image_bytes=red_image,
            metadata=ImageMetadata(page_number=1, source="embedded")
        )
        img2 = ExtractedImage(
            image_bytes=red_image,
            metadata=ImageMetadata(page_number=2, source="embedded")
        )

        extraction = ExtractionResult(
            embedded=[img1, img2],
            page_renders=[],
            total_pages=2
        )

        output = await classifier.classify_extraction(extraction)

        # One floor plan should be deduped
        assert output.total_input == 2
        assert output.total_retained == 1
        assert output.total_duplicates == 1

    @pytest.mark.asyncio
    async def test_classify_extraction_no_category_limits(
        self, classifier, mock_classify_single
    ):
        """Test classify_extraction retains all images (limits disabled)."""
        mock_classify_single.return_value = ClassificationResult(
            category=ImageCategory.LOGO,
            confidence=0.9
        )

        # Create many images - all should be retained (no limits)
        images = [
            ExtractedImage(
                image_bytes=create_gradient_image(800, 600, seed=i * 100),
                metadata=ImageMetadata(page_number=i+1, source="embedded")
            )
            for i in range(10)
        ]

        extraction = ExtractionResult(
            embedded=images,
            page_renders=[],
            total_pages=10
        )

        output = await classifier.classify_extraction(extraction)

        # All images should be retained (category limits disabled)
        assert output.total_retained == 10
        assert output.total_discarded == 0

    @pytest.mark.asyncio
    async def test_classify_extraction_discards_other_category(
        self, classifier, mock_classify_single, red_image
    ):
        """Test classify_extraction discards OTHER category images."""
        mock_classify_single.return_value = ClassificationResult(
            category=ImageCategory.OTHER,
            confidence=0.5
        )

        extracted_img = ExtractedImage(
            image_bytes=red_image,
            metadata=ImageMetadata(page_number=1, source="embedded")
        )
        extraction = ExtractionResult(
            embedded=[extracted_img],
            page_renders=[],
            total_pages=1
        )

        output = await classifier.classify_extraction(extraction)

        assert output.total_input == 1
        assert output.total_retained == 0
        assert output.total_discarded == 1

    @pytest.mark.asyncio
    async def test_classify_extraction_page_renders_dedup_against_embedded(
        self, classifier, mock_classify_single, red_image
    ):
        """Test page renders are deduplicated against embedded images."""
        mock_classify_single.return_value = ClassificationResult(
            category=ImageCategory.INTERIOR,
            confidence=0.9
        )

        # Same image as embedded and page render from same page
        embedded_img = ExtractedImage(
            image_bytes=red_image,
            metadata=ImageMetadata(page_number=1, source="embedded")
        )
        page_render = ExtractedImage(
            image_bytes=red_image,
            metadata=ImageMetadata(page_number=1, source="page_render")
        )

        extraction = ExtractionResult(
            embedded=[embedded_img],
            page_renders=[page_render],
            total_pages=1
        )

        output = await classifier.classify_extraction(extraction)

        # Page render should be detected as duplicate
        assert output.total_input == 2
        assert output.total_duplicates >= 1

    @pytest.mark.asyncio
    async def test_classify_extraction_mixed_categories(
        self, classifier, mock_classify_single, gradient_image,
        checkerboard_image, stripes_image
    ):
        """Test classify_extraction with multiple categories."""
        # Mock different categories for different images
        mock_classify_single.side_effect = [
            ClassificationResult(category=ImageCategory.INTERIOR, confidence=0.9),
            ClassificationResult(category=ImageCategory.EXTERIOR, confidence=0.85),
            ClassificationResult(category=ImageCategory.AMENITY, confidence=0.8),
        ]

        images = [
            ExtractedImage(
                image_bytes=gradient_image,
                metadata=ImageMetadata(page_number=1, source="embedded")
            ),
            ExtractedImage(
                image_bytes=checkerboard_image,
                metadata=ImageMetadata(page_number=2, source="embedded")
            ),
            ExtractedImage(
                image_bytes=stripes_image,
                metadata=ImageMetadata(page_number=3, source="embedded")
            ),
        ]

        extraction = ExtractionResult(
            embedded=images,
            page_renders=[],
            total_pages=3
        )

        output = await classifier.classify_extraction(extraction)

        assert output.total_input == 3
        assert output.total_retained == 3
        assert len(output.category_counts) == 3

    @pytest.mark.asyncio
    async def test_classify_extraction_resets_dedup_service(
        self, classifier, mock_classify_single, red_image
    ):
        """Test classify_extraction resets deduplication service each time."""
        mock_classify_single.return_value = ClassificationResult(
            category=ImageCategory.INTERIOR,
            confidence=0.9
        )

        extracted_img = ExtractedImage(
            image_bytes=red_image,
            metadata=ImageMetadata(page_number=1, source="embedded")
        )
        extraction = ExtractionResult(
            embedded=[extracted_img],
            page_renders=[],
            total_pages=1
        )

        # Run twice
        output1 = await classifier.classify_extraction(extraction)
        output2 = await classifier.classify_extraction(extraction)

        # Both should retain the image (no cross-extraction dedup)
        assert output1.total_retained == 1
        assert output2.total_retained == 1


class TestCategoryLimitsDisabled:
    """Tests confirming category limits are disabled."""

    def test_other_category_still_discarded(self):
        """Test OTHER category is still discarded even without limits."""
        with patch("app.services.image_classifier.anthropic.Anthropic"):
            classifier = ImageClassifier(api_key="test-key")
            counts = {}
            # OTHER should always be discarded
            assert classifier._should_retain(ImageCategory.OTHER, counts) is False

    def test_all_valid_categories_retained(self):
        """Test all non-OTHER categories are retained regardless of count."""
        with patch("app.services.image_classifier.anthropic.Anthropic"):
            classifier = ImageClassifier(api_key="test-key")
            # Even high counts should be retained
            for category in ImageCategory:
                if category != ImageCategory.OTHER:
                    counts = {category: 1000}
                    assert classifier._should_retain(category, counts) is True


class TestLogoValidation:
    """Tests for logo classification validation (false positive prevention)."""

    @pytest.fixture
    def classifier(self):
        """Classifier with mocked Anthropic client."""
        with patch("app.services.image_classifier.anthropic.Anthropic"):
            return ImageClassifier(api_key="test-key")

    def test_full_page_with_logo_not_classified_as_logo(self, classifier):
        """Verify full page renders are not misclassified as logos."""
        # Create a page-sized image (portrait aspect ratio typical of PDF pages)
        page_img = Image.new("RGB", (2480, 3508), color="white")  # A4 at 300 DPI
        # Draw a small "logo" area
        from PIL import ImageDraw
        draw = ImageDraw.Draw(page_img)
        draw.rectangle([100, 100, 300, 200], fill="blue")  # Small logo area

        buf = io.BytesIO()
        page_img.save(buf, format="PNG")

        # Initial classification says it's a logo
        initial_result = ClassificationResult(
            category=ImageCategory.LOGO,
            confidence=0.7,
            reasoning="Contains logo",
            alt_text="Logo"
        )

        result = classifier._validate_logo_classification(
            buf.getvalue(),
            initial_result
        )

        # Should reject as logo due to page-like dimensions
        assert result.category != ImageCategory.LOGO

    def test_actual_logo_image_remains_classified_as_logo(self, classifier):
        """Verify actual logo images (small, square-ish) stay as logo."""
        # Create a logo-like image (small, roughly square)
        logo_img = Image.new("RGB", (400, 200), color="blue")

        buf = io.BytesIO()
        logo_img.save(buf, format="PNG")

        initial_result = ClassificationResult(
            category=ImageCategory.LOGO,
            confidence=0.95,
            reasoning="Developer logo",
            alt_text="Company logo"
        )

        result = classifier._validate_logo_classification(
            buf.getvalue(),
            initial_result
        )

        # Should remain as logo
        assert result.category == ImageCategory.LOGO

    def test_validate_logo_preserves_non_logo_categories(self, classifier):
        """Verify non-logo classifications pass through unchanged."""
        img = Image.new("RGB", (2480, 3508), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        initial_result = ClassificationResult(
            category=ImageCategory.INTERIOR,
            confidence=0.9,
            reasoning="Living room",
            alt_text="Living room"
        )

        result = classifier._validate_logo_classification(
            buf.getvalue(),
            initial_result
        )

        # Should remain interior
        assert result.category == ImageCategory.INTERIOR

    def test_validate_logo_rejects_large_portrait_images(self, classifier):
        """Verify large portrait images are not classified as logos."""
        # Portrait orientation, large dimensions
        img = Image.new("RGB", (1500, 2500), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        initial_result = ClassificationResult(
            category=ImageCategory.LOGO,
            confidence=0.6,
            reasoning="Contains logo element",
            alt_text="Logo"
        )

        result = classifier._validate_logo_classification(
            buf.getvalue(),
            initial_result
        )

        assert result.category != ImageCategory.LOGO

    def test_validate_logo_rejects_very_large_images(self, classifier):
        """Verify very large images are not classified as logos."""
        # Landscape but very large
        img = Image.new("RGB", (3000, 2000), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        initial_result = ClassificationResult(
            category=ImageCategory.LOGO,
            confidence=0.75,
            reasoning="Logo present",
            alt_text="Logo"
        )

        result = classifier._validate_logo_classification(
            buf.getvalue(),
            initial_result
        )

        assert result.category != ImageCategory.LOGO


class TestThresholdsConfiguration:
    """Tests for threshold constants."""

    def test_hash_size_is_64(self):
        """Test HASH_SIZE constant is 64 (pHash standard)."""
        assert HASH_SIZE == 64

    def test_default_threshold_reasonable(self):
        """Test default similarity threshold is reasonable."""
        assert 0.0 < DEFAULT_SIMILARITY_THRESHOLD < 1.0
        assert DEFAULT_SIMILARITY_THRESHOLD == 0.90

    def test_floor_plan_threshold_higher(self):
        """Test floor plan threshold is higher than default."""
        assert FLOOR_PLAN_SIMILARITY_THRESHOLD > DEFAULT_SIMILARITY_THRESHOLD
        assert FLOOR_PLAN_SIMILARITY_THRESHOLD == 0.95

    def test_thresholds_in_valid_range(self):
        """Test all thresholds are in valid range [0, 1]."""
        assert 0.0 <= DEFAULT_SIMILARITY_THRESHOLD <= 1.0
        assert 0.0 <= FLOOR_PLAN_SIMILARITY_THRESHOLD <= 1.0
