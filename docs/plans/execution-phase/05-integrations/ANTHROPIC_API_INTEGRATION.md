# Anthropic Claude API Integration

## Overview

PDP Automation v.3 uses a **hybrid approach** for document processing:
- **pymupdf4llm** - Cost-free text extraction from PDFs (90% cost savings vs vision-based extraction)
- **Claude Sonnet 4.5** - Vision tasks (image classification, watermark detection, floor plan analysis) and content generation

This guide covers the Claude Sonnet 4.5 integration patterns, best practices, and optimization strategies.

**Model Used:**
- **Claude Sonnet 4.5** (`claude-sonnet-4-5-20250929`) - Multimodal (vision + text), optimized for complex agents, coding, and document analysis

**Use Cases:**
1. Image classification (interior, exterior, amenity, floor_plan, etc.)
2. Watermark detection and analysis
3. Floor plan data extraction (vision-based OCR)
4. SEO-optimized content generation
5. Quality assurance validation
6. Fallback vision extraction when pymupdf4llm fails

## Hybrid Processing Architecture

```
PDF Input
    |
    +---> [pymupdf4llm] ---> Text Extraction (FREE)
    |         |
    |         +---> Project data, descriptions, amenities, payment plans
    |         +---> Floor plan surrounding text (for cross-referencing)
    |
    +---> [PyMuPDF fitz] ---> Dual Image Extraction (FREE)
              |
              +---> Embedded XObjects (doc.extract_image)
              +---> Page Renders at 300 DPI (page.get_pixmap)
              |
              +---> [LLM Image Optimizer]
              |         |
              |         +---> Tier 1: Original/Archive (full quality)
              |         +---> Tier 2: LLM-Optimized (task-specific dims)
              |
              +---> [Claude Sonnet 4.5 Vision] (uses Tier 2 images)
                        |
                        +---> Image Classification
                        +---> Watermark Detection
                        +---> Floor Plan OCR + Text Cross-Reference
                        +---> Alt-text Generation
```

### Why Hybrid?

| Task | Method | Cost |
|------|--------|------|
| Text extraction | pymupdf4llm | FREE |
| Image extraction | PyMuPDF (fitz) | FREE |
| Image classification | Claude Sonnet 4.5 Vision | ~$0.003/image |
| Watermark detection | Claude Sonnet 4.5 Vision | ~$0.003/image |
| Floor plan OCR | Claude Sonnet 4.5 Vision | ~$0.01/floor plan |
| Content generation | Claude Sonnet 4.5 | ~$0.02/project |
| **Total per project** | Hybrid | **~$0.15-0.30** |

Compare to vision-only: ~$1.50-3.00 per project (10x more expensive)

## Prerequisites

1. **Anthropic API Account** with Claude access
2. **API Key** stored in GCP Secret Manager
3. **Python 3.11+** with required libraries
4. **Sufficient API quota** (contact Anthropic for production tier)

### API Key Setup

```bash
# Store in GCP Secret Manager
echo -n "sk-ant-your-anthropic-api-key" | gcloud secrets create anthropic-api-key \
  --data-file=- \
  --replication-policy="automatic" \
  --project=YOUR-GCP-PROJECT-ID

# Grant access to service account
gcloud secrets add-iam-policy-binding anthropic-api-key \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=YOUR-GCP-PROJECT-ID

# Verify access
gcloud secrets versions access latest --secret=anthropic-api-key
```

## Installation and Configuration

### Python Dependencies

```bash
# Anthropic SDK
pip install anthropic>=0.40.0

# PDF text extraction (FREE - no API costs)
pip install pymupdf4llm>=0.2.9
pip install pymupdf>=1.26.6

# Image processing
pip install pillow>=10.0.0
pip install pdf2image>=1.16.0
```

### Backend Configuration

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Anthropic Configuration
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5-20250929"
    ANTHROPIC_MAX_TOKENS: int = 4096
    ANTHROPIC_TEMPERATURE: float = 0.7
    ANTHROPIC_TIMEOUT: int = 120

    # Rate limiting
    ANTHROPIC_MAX_RETRIES: int = 3
    ANTHROPIC_RETRY_DELAY: int = 60

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### Initialize Anthropic Client

```python
# backend/app/services/anthropic_client.py
import anthropic
from anthropic import AsyncAnthropic, RateLimitError, APIError, APITimeoutError
from app.core.config import settings
from app.core.logging import logger
import asyncio
from typing import Optional, List, Dict, Any

class AnthropicService:
    """Service for interacting with Anthropic Claude API"""

    def __init__(self):
        self.client = AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            timeout=settings.ANTHROPIC_TIMEOUT,
            max_retries=settings.ANTHROPIC_MAX_RETRIES
        )
        self.model = settings.ANTHROPIC_MODEL

    async def _call_with_retry(
        self,
        func,
        *args,
        max_retries: int = 3,
        **kwargs
    ) -> Any:
        """Call Anthropic API with exponential backoff retry logic"""
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except RateLimitError as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = (2 ** attempt) * settings.ANTHROPIC_RETRY_DELAY
                logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                await asyncio.sleep(wait_time)
            except APITimeoutError as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Request timeout, retrying {attempt + 1}/{max_retries}")
                await asyncio.sleep(10)
            except APIError as e:
                logger.error(f"Anthropic API error: {e}")
                raise

    async def close(self):
        """Close the client connection"""
        await self.client.close()

# Singleton instance
anthropic_service = AnthropicService()
```

## Text Extraction with pymupdf4llm (FREE)

Primary method for extracting text content from PDFs - no API costs.

```python
# backend/app/services/pdf_text_extraction.py
import pymupdf4llm
import fitz  # PyMuPDF
from typing import Dict, Any, List
from app.core.logging import logger

def extract_text_from_pdf(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Extract structured text from PDF using pymupdf4llm.

    This is FREE - no API calls required.

    Args:
        pdf_bytes: PDF file as bytes

    Returns:
        Dict with markdown text and metadata
    """
    try:
        # Open PDF from bytes
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        # Extract as markdown (preserves structure)
        markdown_text = pymupdf4llm.to_markdown(doc)

        # Extract metadata
        metadata = {
            "page_count": len(doc),
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "creation_date": doc.metadata.get("creationDate", "")
        }

        doc.close()

        logger.info(f"Extracted {len(markdown_text)} chars from {metadata['page_count']} pages (FREE)")

        return {
            "text": markdown_text,
            "metadata": metadata,
            "extraction_method": "pymupdf4llm",
            "cost": 0.0
        }

    except Exception as e:
        logger.error(f"pymupdf4llm extraction failed: {e}")
        raise

def extract_all_images_from_pdf(pdf_bytes: bytes) -> Dict[str, List]:
    """
    Comprehensive triple-extraction strategy for ALL image types.

    This is FREE - no API calls required.

    Why triple extraction?
    - PyMuPDF's extract_image() only gets embedded raster XObjects
    - It MISSES: vector graphics, CAD exports, composited renders, logos
    - Page rendering captures ALL visual content including vectors
    - pymupdf4llm extracts per-page text for context and cross-referencing

    Args:
        pdf_bytes: PDF file as bytes

    Returns:
        Dict with:
            - "embedded": List of embedded raster images
            - "page_renders": List of full page renders (captures vectors)
            - "metadata": Extraction statistics
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    embedded_images = []
    page_renders = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        # ========================================
        # EXTRACTION 1: Embedded raster images
        # ========================================
        image_list = page.get_images()
        for img_index, img in enumerate(image_list):
            xref = img[0]
            try:
                base_image = doc.extract_image(xref)

                # Skip tiny images (likely decorative)
                if base_image["width"] < 500 or base_image["height"] < 500:
                    continue

                embedded_images.append({
                    "bytes": base_image["image"],
                    "source": "embedded",
                    "page": page_num + 1,
                    "index": img_index,
                    "format": base_image["ext"],
                    "width": base_image["width"],
                    "height": base_image["height"],
                    "xref": xref
                })
            except Exception as e:
                logger.warning(f"Failed to extract embedded image {xref}: {e}")

        # ========================================
        # EXTRACTION 2: Full page render (captures vectors)
        # ========================================
        # Render at 300 DPI for ALL pages - consistent quality
        # Vector content (logos, amenities, maps) needs same quality as floor plans
        dpi = 300
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_bytes = pix.tobytes("png")

        page_renders.append({
            "bytes": img_bytes,
            "source": "page_render",
            "page": page_num + 1,
            "width": pix.width,
            "height": pix.height,
            "dpi": dpi,
            "has_embedded_images": len(image_list) > 0
        })

    doc.close()

    logger.info(f"Triple extraction: {len(embedded_images)} embedded, {len(page_renders)} page renders (FREE)")

    return {
        "embedded": embedded_images,
        "page_renders": page_renders,
        "page_text_map": {},  # Per-page text extraction via pymupdf4llm
        "metadata": {
            "total_embedded": len(embedded_images),
            "total_pages": len(page_renders),
            "extraction_method": "triple"
        }
    }

def parse_project_data_from_text(markdown_text: str) -> Dict[str, Any]:
    """
    Parse structured project data from extracted markdown text.

    This uses pattern matching - no API calls required.

    Args:
        markdown_text: Markdown text from pymupdf4llm

    Returns:
        Dict with parsed project fields
    """
    import re

    data = {}

    # Extract project name (usually in H1 or first prominent text)
    h1_match = re.search(r'^#\s+(.+)$', markdown_text, re.MULTILINE)
    if h1_match:
        data["project_name"] = h1_match.group(1).strip()

    # Extract prices (AED patterns)
    price_pattern = r'(?:AED|Dhs?\.?)\s*([\d,]+(?:\.\d{2})?)'
    prices = re.findall(price_pattern, markdown_text, re.IGNORECASE)
    if prices:
        # Clean and find minimum price
        clean_prices = [int(p.replace(',', '').split('.')[0]) for p in prices]
        data["starting_price"] = f"AED {min(clean_prices):,}"

    # Extract bedroom configurations
    bedroom_pattern = r'(\d)\s*(?:BR|Bed(?:room)?s?|B/R)'
    bedrooms = set(re.findall(bedroom_pattern, markdown_text, re.IGNORECASE))
    if bedrooms:
        data["bedrooms"] = ", ".join(sorted(bedrooms)) + " BR"

    # Extract completion date
    completion_pattern = r'(?:completion|handover|ready)\s*(?:date)?[:\s]*(?:Q[1-4]\s*)?(\d{4})'
    completion = re.search(completion_pattern, markdown_text, re.IGNORECASE)
    if completion:
        data["completion_date"] = completion.group(1)

    # Extract area ranges
    area_pattern = r'(\d{3,5})\s*(?:sq\.?\s*ft|sqft|square\s*feet)'
    areas = re.findall(area_pattern, markdown_text, re.IGNORECASE)
    if areas:
        areas = [int(a) for a in areas]
        data["area_range"] = f"{min(areas):,} - {max(areas):,} sq ft"

    logger.info(f"Parsed {len(data)} fields from text (FREE)")

    return data
```

## LLM Image Optimizer

Creates optimized image variants for Claude Sonnet 4.5 processing to reduce token consumption.

```python
# backend/app/services/llm_image_optimizer.py
from PIL import Image
import io
from typing import Tuple, Dict, Any

class LLMImageOptimizer:
    """
    Creates optimized image variants for Claude Sonnet 4.5 processing.

    Goals:
    - Reduce token consumption (images consume tokens based on size)
    - Maintain sufficient quality for vision tasks
    - Do NOT degrade task accuracy (classification, OCR, detection)

    Key Principle:
    - Original images (Tier 1) preserved for final output
    - Optimized variants (Tier 2) used ONLY for Claude processing
    """

    # Anthropic recommended max dimension for optimal processing
    MAX_DIMENSION = 1568

    # Task-specific settings (balance quality vs. tokens)
    TASK_SETTINGS = {
        "classification": {
            "max_dimension": 1024,    # Classification works at lower res
            "quality": 80,
            "format": "JPEG"
        },
        "watermark_detection": {
            "max_dimension": 1280,    # Need detail for bounding boxes
            "quality": 85,
            "format": "JPEG"
        },
        "floor_plan_ocr": {
            "max_dimension": 1568,    # Maximum for text legibility
            "quality": None,          # Lossless
            "format": "PNG"
        },
        "alt_text_generation": {
            "max_dimension": 1024,
            "quality": 80,
            "format": "JPEG"
        }
    }

    def optimize_for_llm(
        self,
        image_bytes: bytes,
        task: str
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Create LLM-optimized variant of image.

        Args:
            image_bytes: Original image bytes (full quality)
            task: Vision task type

        Returns:
            Tuple of (optimized_bytes, metadata)
        """
        settings = self.TASK_SETTINGS.get(task, self.TASK_SETTINGS["classification"])

        img = Image.open(io.BytesIO(image_bytes))
        original_size = len(image_bytes)

        # Resize if exceeds max dimension (maintain aspect ratio)
        if max(img.size) > settings["max_dimension"]:
            img.thumbnail(
                (settings["max_dimension"], settings["max_dimension"]),
                Image.Resampling.LANCZOS
            )

        # Convert to RGB if necessary (for JPEG)
        if settings["format"] == "JPEG" and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Save with task-appropriate quality
        output = io.BytesIO()
        if settings["format"] == "PNG":
            img.save(output, format="PNG", optimize=True)
        else:
            img.save(output, format="JPEG", quality=settings["quality"], optimize=True)

        optimized_bytes = output.getvalue()

        metadata = {
            "original_size": original_size,
            "optimized_size": len(optimized_bytes),
            "reduction_percent": round((1 - len(optimized_bytes) / original_size) * 100, 1),
            "dimensions": img.size,
            "task": task,
            "format": settings["format"]
        }

        return optimized_bytes, metadata

# Singleton instance
llm_optimizer = LLMImageOptimizer()
```

**Token Savings Estimate:**

| Task | Original (2450x1400) | Optimized | Token Reduction |
|------|----------------------|-----------|-----------------|
| Classification | ~1200 tokens | ~400 tokens | ~67% |
| Watermark detection | ~1200 tokens | ~600 tokens | ~50% |
| Floor plan OCR | ~1200 tokens | ~900 tokens | ~25% |

## Image Quality Validation

Validate image quality before sending to Claude vision tasks.

```python
# backend/app/services/image_quality_validator.py
from PIL import Image, ImageEnhance
import io
from typing import Optional
from dataclasses import dataclass
from app.core.logging import logger

@dataclass
class ValidationResult:
    is_valid: bool
    width: int
    height: int
    warnings: list
    enhanced_bytes: Optional[bytes]
    recommendation: str

def validate_image_quality(
    image_bytes: bytes,
    task: str,
    auto_enhance: bool = False
) -> ValidationResult:
    """
    Validate image quality before sending to Claude.

    Thresholds by task:
    - classification: min 800x600px, any format
    - watermark_detection: min 1024x768px, prefer uncompressed
    - floor_plan_ocr: min 1200x900px, prefer PNG or high-quality JPEG

    Args:
        image_bytes: Raw image bytes
        task: Vision task type
        auto_enhance: If True, attempt enhancement when below threshold

    Returns:
        ValidationResult with is_valid, enhanced_bytes (if applicable), warnings
    """
    img = Image.open(io.BytesIO(image_bytes))
    width, height = img.size

    thresholds = {
        "classification": {"min_width": 800, "min_height": 600},
        "watermark_detection": {"min_width": 1024, "min_height": 768},
        "floor_plan_ocr": {"min_width": 1200, "min_height": 900}
    }

    threshold = thresholds.get(task, thresholds["classification"])
    is_valid = width >= threshold["min_width"] and height >= threshold["min_height"]

    warnings = []
    enhanced_bytes = None

    if not is_valid:
        warnings.append(f"Image below threshold: {width}x{height} < {threshold['min_width']}x{threshold['min_height']}")

        if auto_enhance:
            try:
                enhanced_bytes = _enhance_image(img, threshold)
                warnings.append("Auto-enhancement applied (experimental)")
            except Exception as e:
                warnings.append(f"Auto-enhancement failed: {e}")

    if warnings:
        logger.warning(f"Quality validation for {task}: {warnings}")

    return ValidationResult(
        is_valid=is_valid,
        width=width,
        height=height,
        warnings=warnings,
        enhanced_bytes=enhanced_bytes,
        recommendation="review" if not is_valid else "proceed"
    )

def _enhance_image(img: Image.Image, threshold: dict) -> bytes:
    """
    EXPERIMENTAL: Enhance low-quality image using Pillow.
    Uses LANCZOS resampling for upscaling.
    Note: This cannot recover lost detail, only interpolate.
    """
    scale_w = threshold["min_width"] / img.width
    scale_h = threshold["min_height"] / img.height
    scale = max(scale_w, scale_h, 1.0)

    if scale > 1.0:
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Sharpen slightly to reduce blur from upscaling
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.2)

    output = io.BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()
```

**Usage in Pipeline:**
```python
# Default: warn only, no auto-enhance
result = validate_image_quality(image_bytes, "floor_plan_ocr")
if result.warnings:
    logger.warning(f"Quality issues: {result.warnings}")

# Optional: enable auto-enhance for failed validations
result = validate_image_quality(
    image_bytes,
    "floor_plan_ocr",
    auto_enhance=True  # Experimental fallback
)
if result.enhanced_bytes:
    image_bytes = result.enhanced_bytes
```

## Image Classification with Claude Vision

Classify extracted images - uses Claude API (costs apply).

```python
# backend/app/services/image_classification.py
import base64
from typing import List, Literal
from app.services.anthropic_client import anthropic_service
from app.core.logging import logger

ImageCategory = Literal[
    "interior",
    "exterior",
    "amenity",
    "floor_plan",
    "logo",
    "location_map",
    "master_plan",
    "other"
]

async def classify_image(original_bytes: bytes) -> ImageCategory:
    """
    Classify a single image using Claude Sonnet 4.5 vision.

    Uses LLM-optimized image (Tier 2) to reduce token consumption.

    Args:
        original_bytes: Original image file as bytes (Tier 1)

    Returns:
        Image category
    """
    from app.services.llm_image_optimizer import llm_optimizer

    # Create LLM-optimized version (smaller = fewer tokens)
    optimized_bytes, meta = llm_optimizer.optimize_for_llm(original_bytes, "classification")
    logger.info(f"Classification image optimized: {meta['reduction_percent']}% size reduction")

    # Encode optimized image to base64
    base64_image = base64.standard_b64encode(optimized_bytes).decode('utf-8')

    # Use format from optimizer
    media_type = f"image/{meta['format'].lower()}"

    classification_prompt = """
    Classify this real estate marketing image into ONE of these categories:

    - interior: Indoor photos of rooms, living spaces, kitchens, bathrooms
    - exterior: Building exterior, facade, entrance
    - amenity: Shared facilities like pool, gym, playground, gardens
    - floor_plan: Architectural floor plans or unit layouts
    - logo: Company or project logo
    - location_map: Maps showing location or nearby landmarks
    - master_plan: Site plan or master development layout
    - other: Anything else

    Respond with ONLY the category name, nothing else.
    """

    try:
        response = await anthropic_service._call_with_retry(
            anthropic_service.client.messages.create,
            model=anthropic_service.model,
            max_tokens=50,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_image
                            }
                        },
                        {"type": "text", "text": classification_prompt}
                    ]
                }
            ]
        )

        category = response.content[0].text.strip().lower()
        logger.info(f"Image classified as: {category}")

        return category if category in ImageCategory.__args__ else "other"

    except Exception as e:
        logger.error(f"Image classification failed: {e}")
        return "other"

async def classify_images_batch(images: List[bytes]) -> List[ImageCategory]:
    """
    Classify multiple images efficiently.

    Args:
        images: List of image bytes

    Returns:
        List of categories
    """
    import asyncio

    # Process in batches to avoid rate limits
    batch_size = 5
    results = []

    for i in range(0, len(images), batch_size):
        batch = images[i:i + batch_size]

        # Classify batch concurrently
        tasks = [classify_image(img) for img in batch]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)

        # Small delay between batches
        if i + batch_size < len(images):
            await asyncio.sleep(1)

    return results
```

## Watermark Detection with Claude Vision

Detect and identify watermarks in images.

```python
# backend/app/services/watermark_detection.py
import base64
import json
from typing import Dict, Any
from app.services.anthropic_client import anthropic_service
from app.core.logging import logger

async def detect_watermark(original_bytes: bytes) -> Dict[str, Any]:
    """
    Detect if image contains watermark and extract details.

    Uses LLM-optimized image (Tier 2) to reduce token consumption.

    Args:
        original_bytes: Original image file as bytes (Tier 1)

    Returns:
        Dict with has_watermark, watermark_text, confidence
    """
    from app.services.llm_image_optimizer import llm_optimizer

    # Create LLM-optimized version (need detail for bounding boxes)
    optimized_bytes, meta = llm_optimizer.optimize_for_llm(original_bytes, "watermark_detection")
    logger.info(f"Watermark detection image optimized: {meta['reduction_percent']}% size reduction")

    base64_image = base64.standard_b64encode(optimized_bytes).decode('utf-8')
    media_type = f"image/{meta['format'].lower()}"

    detection_prompt = """
    Analyze this image for watermarks. A watermark is text, logo, or pattern overlaid on the image.

    Respond in JSON format:
    {
        "has_watermark": true/false,
        "watermark_text": "exact text of watermark if readable, or null",
        "watermark_location": "top-left/top-right/bottom-left/bottom-right/center/multiple/null",
        "confidence": "high/medium/low"
    }

    Return ONLY valid JSON without code blocks.
    """

    try:
        response = await anthropic_service._call_with_retry(
            anthropic_service.client.messages.create,
            model=anthropic_service.model,
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_image
                            }
                        },
                        {"type": "text", "text": detection_prompt}
                    ]
                }
            ]
        )

        result_text = response.content[0].text.strip()
        result_text = _clean_json_response(result_text)
        result = json.loads(result_text)
        logger.info(f"Watermark detection: {result}")

        return result

    except Exception as e:
        logger.error(f"Watermark detection failed: {e}")
        return {
            "has_watermark": False,
            "watermark_text": None,
            "watermark_location": None,
            "confidence": "low"
        }

def _clean_json_response(text: str) -> str:
    """Clean JSON response from Claude (remove code blocks if present)"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        # Remove 'json' language identifier if present
        if lines and lines[0].strip().lower() == "json":
            lines = lines[1:]
        text = "\n".join(lines)
    return text.strip()
```

## Floor Plan Data Extraction with Claude Vision

Extract unit data from floor plan images using OCR, with cross-referencing to surrounding PDF text.

**Key Principle: Floor Plan Image is Source of Truth**

| Priority | Source | When to Use |
|----------|--------|-------------|
| 1 (PRIMARY) | Floor plan image | Always - if data is visible in the floor plan |
| 2 (FALLBACK) | Verified surrounding text | Only if floor plan lacks data AND text is verified to refer to THIS floor plan |
| 3 (REJECT) | Unverified text | NEVER - risks associating wrong data with floor plan |

```python
# backend/app/services/floor_plan_extraction.py
import base64
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from app.services.anthropic_client import anthropic_service
from app.services.llm_image_optimizer import llm_optimizer
from app.core.logging import logger

@dataclass
class FloorPlanData:
    unit_type: Optional[str] = None
    unit_type_source: str = "none"
    unit_type_confidence: float = 0.0

    bedrooms: Optional[int] = None
    bedrooms_source: str = "none"

    bathrooms: Optional[float] = None
    bathrooms_source: str = "none"

    area_sqft: Optional[float] = None
    area_source: str = "none"

    room_dimensions: Dict[str, str] = field(default_factory=dict)
    dimensions_source: str = "none"

    features: List[str] = field(default_factory=list)


async def extract_floor_plan_data_comprehensive(
    floor_plan_image: bytes,
    pdf_text: str,
    page_number: int
) -> FloorPlanData:
    """
    Extract floor plan data from BOTH image OCR AND surrounding PDF text.

    Floor plan image is SOURCE OF TRUTH. Text is VERIFIED FALLBACK only.

    Args:
        floor_plan_image: Floor plan image bytes
        pdf_text: Full markdown text from pymupdf4llm
        page_number: Page where floor plan was found

    Returns:
        Merged FloorPlanData with confidence scores per field
    """

    # ========================================
    # SOURCE 1: Vision OCR from floor plan image (PRIMARY)
    # ========================================
    optimized_image, meta = llm_optimizer.optimize_for_llm(floor_plan_image, "floor_plan_ocr")
    logger.info(f"Floor plan optimized: {meta['reduction_percent']}% size reduction")

    vision_prompt = """
    Extract all visible data from this floor plan image:
    - Unit type (e.g., "1BR", "2BR", "Studio")
    - Bedroom count
    - Bathroom count (support .5 for half-bath)
    - Total area (if shown)
    - Room dimensions (if shown)
    - Features visible in the layout

    Return JSON. For fields not visible in the image, use null.
    {
        "unit_type": "string or null",
        "bedrooms": "number or null",
        "bathrooms": "number or null",
        "total_area": "string or null",
        "room_dimensions": {"room_name": "dimensions"} or null,
        "features": ["list"] or []
    }
    """

    vision_result = await _claude_vision_extract(optimized_image, vision_prompt)

    # ========================================
    # SOURCE 2: Text extraction from surrounding pages (FALLBACK)
    # ========================================
    context_pages = _extract_page_context(pdf_text, page_number, window=2)

    text_prompt = f"""
    Extract floor plan unit data from this PDF text. Look for:
    - Unit types and their specifications
    - Bedroom/bathroom counts
    - Area measurements (sqft, sqm)
    - Features and amenities per unit type

    Text context (pages {page_number-1} to {page_number+1}):
    {context_pages}

    Return JSON array of all unit types found with their specifications.
    Include page number where each was found.
    """

    text_result = await _claude_text_extract(text_prompt)

    # ========================================
    # MERGE: Image is source of truth, text is verified fallback
    # ========================================
    merged_data = _merge_floor_plan_sources(vision_result, text_result, page_number)

    return merged_data


async def _claude_vision_extract(image_bytes: bytes, prompt: str) -> Dict[str, Any]:
    """Extract data from floor plan image using Claude vision."""
    base64_image = base64.standard_b64encode(image_bytes).decode('utf-8')

    # Use PNG for floor plans (lossless for text clarity)
    media_type = "image/png"

    try:
        response = await anthropic_service._call_with_retry(
            anthropic_service.client.messages.create,
            model=anthropic_service.model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_image
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        )

        result_text = response.content[0].text.strip()
        result_text = _clean_json_response(result_text)
        return json.loads(result_text)

    except Exception as e:
        logger.error(f"Vision extraction failed: {e}")
        return {}


async def _claude_text_extract(prompt: str) -> List[Dict[str, Any]]:
    """Extract floor plan data from surrounding text."""
    try:
        response = await anthropic_service._call_with_retry(
            anthropic_service.client.messages.create,
            model=anthropic_service.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()
        result_text = _clean_json_response(result_text)
        result = json.loads(result_text)
        return result if isinstance(result, list) else [result]

    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return []


def _extract_page_context(pdf_text: str, page_number: int, window: int = 2) -> str:
    """Extract text from pages surrounding the floor plan."""
    # Split by page markers (pymupdf4llm uses --- or page breaks)
    pages = pdf_text.split("---")

    start = max(0, page_number - window - 1)
    end = min(len(pages), page_number + window)

    return "\n".join(pages[start:end])


def _merge_floor_plan_sources(
    vision_data: Dict,
    text_data: List[Dict],
    floor_plan_page: int
) -> FloorPlanData:
    """
    Merge floor plan data with FLOOR PLAN IMAGE as source of truth.

    Priority (CRITICAL):
    1. FLOOR PLAN IMAGE is the source of truth
       - If vision OCR extracts data from the floor plan, USE IT
    2. Text is FALLBACK ONLY
       - Only used when floor plan image lacks the data
       - MUST be verified to refer to THIS specific floor plan
    3. Never associate unverified text data with a floor plan
    """
    merged = FloorPlanData()

    # ========================================
    # SOURCE OF TRUTH: Floor plan image (vision)
    # ========================================

    # Unit type: from floor plan if present
    if vision_data.get("unit_type"):
        merged.unit_type = vision_data["unit_type"]
        merged.unit_type_source = "floor_plan_image"
        merged.unit_type_confidence = 0.90
    else:
        # FALLBACK: Try text, but MUST verify it refers to this floor plan
        text_unit = _find_verified_text_data(text_data, floor_plan_page, "unit_type")
        if text_unit:
            merged.unit_type = text_unit["value"]
            merged.unit_type_source = "text_fallback"
            merged.unit_type_confidence = text_unit["confidence"]

    # Area: from floor plan if present
    if vision_data.get("total_area"):
        merged.area_sqft = _parse_area(vision_data["total_area"])
        merged.area_source = "floor_plan_image"
    else:
        text_area = _find_verified_text_data(text_data, floor_plan_page, "area_sqft")
        if text_area:
            merged.area_sqft = text_area["value"]
            merged.area_source = "text_fallback"

    # Bedroom/bathroom count: from floor plan if present
    if vision_data.get("bedrooms") is not None:
        merged.bedrooms = vision_data["bedrooms"]
        merged.bedrooms_source = "floor_plan_image"
    else:
        text_beds = _find_verified_text_data(text_data, floor_plan_page, "bedrooms")
        if text_beds:
            merged.bedrooms = text_beds["value"]
            merged.bedrooms_source = "text_fallback"

    if vision_data.get("bathrooms") is not None:
        merged.bathrooms = vision_data["bathrooms"]
        merged.bathrooms_source = "floor_plan_image"

    # Room dimensions: floor plan only (never in text)
    if vision_data.get("room_dimensions"):
        merged.room_dimensions = vision_data["room_dimensions"]
        merged.dimensions_source = "floor_plan_image"

    # Features: floor plan primary
    vision_features = set(vision_data.get("features", []))
    merged.features = list(vision_features)

    logger.info(f"Floor plan merged: unit_type={merged.unit_type} (source: {merged.unit_type_source})")

    return merged


def _find_verified_text_data(
    text_data: List[Dict],
    floor_plan_page: int,
    field: str
) -> Optional[Dict]:
    """
    Find text data that is VERIFIED to refer to the specific floor plan.

    Verification criteria:
    1. Text is on the same page as floor plan OR immediately adjacent
    2. Text contains explicit reference to the unit type visible in floor plan
    3. Text appears in a context that clearly associates it with the floor plan

    Returns:
        {"value": ..., "confidence": 0.0-1.0} or None if not verified
    """
    for entry in text_data:
        # Check page proximity
        entry_page = entry.get("page", 0)
        if abs(entry_page - floor_plan_page) > 1:
            continue  # Too far from floor plan page

        # If we found data on the same or adjacent page, use it with moderate confidence
        if field in entry and entry[field] is not None:
            return {
                "value": entry[field],
                "confidence": 0.7 if entry_page == floor_plan_page else 0.5
            }

    return None  # No verified text data found


def _parse_area(area_str: str) -> Optional[float]:
    """Parse area string to float (sqft)."""
    import re
    if not area_str:
        return None

    # Extract number from strings like "850 sqft" or "79 sqm"
    match = re.search(r'([\d,]+(?:\.\d+)?)', area_str)
    if match:
        value = float(match.group(1).replace(',', ''))
        # Convert sqm to sqft if needed
        if 'sqm' in area_str.lower() or 'm2' in area_str.lower():
            value = value * 10.764
        return value
    return None


def _clean_json_response(text: str) -> str:
    """Clean JSON response from Claude (remove code blocks if present)"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        if lines and lines[0].strip().lower() == "json":
            lines = lines[1:]
        text = "\n".join(lines)
    return text.strip()
```

**Verification Requirements for Text Fallback:**
- Text must be on same page or immediately adjacent (within 1 page)
- Text must contain explicit reference matching floor plan (e.g., unit type label)
- If verification fails, leave field empty rather than risk wrong data

## SEO Content Generation with Claude

Generate SEO-optimized content from extracted data with brand context enforcement.

```python
# backend/app/services/content_generation.py
import json
from typing import Dict, Any
from app.services.anthropic_client import anthropic_service
from app.core.logging import logger

# Load brand context once at module level
def _load_brand_context() -> str:
    """Load brand context for prepending to content prompts"""
    context_path = "reference/company/brand-guidelines/brand-context-prompt.md"
    try:
        with open(context_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("Brand context file not found, using default")
        return "Generate professional real estate content."

BRAND_CONTEXT = _load_brand_context()

async def generate_seo_content(
    project_data: Dict[str, Any],
    content_type: str = "full"
) -> Dict[str, str]:
    """
    Generate SEO-optimized content from project data.

    Brand context is automatically prepended to enforce:
    - Advisor voice (not salesperson tone)
    - Terminology standards (apartment not flat, specific amenity descriptors)
    - Language prohibitions (no "world-class", "prime location", etc.)
    - Content structure rules (lead with differentiator)

    Args:
        project_data: Extracted project information
        content_type: Type of content to generate (full, meta, overview)

    Returns:
        Dict with generated content fields
    """

    generation_prompt = f"""
    Project Details:
    {json.dumps(project_data, indent=2)}

    Generate the following content:

    1. meta_title: 50-60 characters, include project name and location
    2. meta_description: 150-160 characters, compelling with price and key features
    3. h1: Main heading, 40-60 characters
    4. overview: 2-3 paragraphs, 150-200 words, highlight unique features
    5. amenities_description: 1 paragraph describing key amenities
    6. location_description: 1 paragraph about location advantages
    7. investment_highlights: 3-4 bullet points on investment benefits

    SEO Requirements:
    - Include keywords: "{project_data.get('project_name', '')}", "{project_data.get('location', '')}", "Dubai property", "real estate"
    - Natural language, not keyword-stuffed
    - Focus on value proposition

    Return as JSON with the fields above. No code blocks, just raw JSON.
    """

    try:
        system_message = f"""
{BRAND_CONTEXT}

---
You are generating SEO-optimized content for the company.
Follow the brand guidelines above strictly.
Always return valid JSON without markdown code blocks.
"""

        response = await anthropic_service._call_with_retry(
            anthropic_service.client.messages.create,
            model=anthropic_service.model,
            max_tokens=2048,
            system=system_message,
            messages=[
                {
                    "role": "user",
                    "content": generation_prompt
                }
            ]
        )

        content_text = response.content[0].text.strip()
        content_text = _clean_json_response(content_text)
        content = json.loads(content_text)

        logger.info(f"Generated SEO content for: {project_data.get('project_name', 'Unknown')}")

        return content

    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        raise

async def generate_url_slug(project_name: str, location: str) -> str:
    """
    Generate SEO-friendly URL slug.

    Args:
        project_name: Name of the project
        location: Location of the project

    Returns:
        URL slug
    """

    prompt = f"""
    Generate an SEO-friendly URL slug for:
    Project: {project_name}
    Location: {location}

    Requirements:
    - Lowercase, use hyphens
    - Include project name and location
    - 3-5 words maximum
    - No special characters

    Example: "damac-lagoons-dubai-land"

    Return only the slug, nothing else.
    """

    try:
        response = await anthropic_service._call_with_retry(
            anthropic_service.client.messages.create,
            model=anthropic_service.model,
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )

        slug = response.content[0].text.strip()
        logger.info(f"Generated slug: {slug}")

        return slug

    except Exception as e:
        logger.error(f"Slug generation failed: {e}")
        # Fallback to simple slugification
        import re
        combined = f"{project_name}-{location}"
        slug = re.sub(r'[^a-z0-9]+', '-', combined.lower()).strip('-')
        return slug

def _clean_json_response(text: str) -> str:
    """Clean JSON response from Claude (remove code blocks if present)"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        if lines and lines[0].strip().lower() == "json":
            lines = lines[1:]
        text = "\n".join(lines)
    return text.strip()
```

## Quality Assurance Validation

Validate extracted data for completeness and accuracy.

```python
# backend/app/services/qa_validation.py
import json
from typing import Dict, Any, List
from app.services.anthropic_client import anthropic_service
from app.core.logging import logger

async def validate_extracted_data(
    extracted_data: Dict[str, Any],
    original_text: str = None
) -> Dict[str, Any]:
    """
    Validate extracted data for completeness and accuracy.

    Args:
        extracted_data: Data extracted from PDF
        original_text: Original text content for cross-reference

    Returns:
        Validation report with issues and confidence score
    """

    validation_prompt = f"""
    Review this extracted real estate project data for quality issues:

    {json.dumps(extracted_data, indent=2)}

    Check for:
    1. Missing required fields (project_name, developer_name, location, starting_price)
    2. Incomplete or vague information
    3. Formatting inconsistencies
    4. Unrealistic values (e.g., price too low/high)
    5. Ambiguous bedroom configurations

    Return JSON with:
    {{
        "is_valid": true/false,
        "confidence_score": 0-100,
        "issues": [
            {{"field": "field_name", "issue": "description", "severity": "critical/warning/info"}}
        ],
        "suggestions": [
            "improvement suggestion 1",
            "improvement suggestion 2"
        ]
    }}

    Return only valid JSON without code blocks.
    """

    try:
        response = await anthropic_service._call_with_retry(
            anthropic_service.client.messages.create,
            model=anthropic_service.model,
            max_tokens=1024,
            system="You are a quality assurance expert for real estate data. Always return valid JSON.",
            messages=[
                {
                    "role": "user",
                    "content": validation_prompt
                }
            ]
        )

        result_text = response.content[0].text.strip()
        result_text = _clean_json_response(result_text)
        validation_report = json.loads(result_text)

        logger.info(f"Validation complete. Valid: {validation_report.get('is_valid')}, Score: {validation_report.get('confidence_score')}")

        return validation_report

    except Exception as e:
        logger.error(f"QA validation failed: {e}")
        return {
            "is_valid": False,
            "confidence_score": 0,
            "issues": [{"field": "general", "issue": "Validation error", "severity": "critical"}],
            "suggestions": []
        }

def _clean_json_response(text: str) -> str:
    """Clean JSON response from Claude"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        if lines and lines[0].strip().lower() == "json":
            lines = lines[1:]
        text = "\n".join(lines)
    return text.strip()
```

## Fallback Vision Extraction

When pymupdf4llm fails (scanned PDFs, image-heavy docs), fall back to Claude vision.

```python
# backend/app/services/pdf_vision_extraction.py
import base64
import json
from typing import Dict, Any
from pdf2image import convert_from_bytes
from io import BytesIO
from app.services.anthropic_client import anthropic_service
from app.core.logging import logger

async def extract_project_data_with_vision(
    pdf_bytes: bytes,
    max_pages: int = 10
) -> Dict[str, Any]:
    """
    FALLBACK: Extract project data using Claude vision when pymupdf4llm fails.

    Use this only when:
    - PDF is scanned/image-based
    - pymupdf4llm returns empty/minimal text
    - Complex layouts that break text extraction

    Cost: ~$0.10-0.30 per PDF (10x more than text extraction)

    Args:
        pdf_bytes: PDF file as bytes
        max_pages: Maximum number of pages to process

    Returns:
        Structured project data dictionary
    """

    logger.warning("Using vision fallback for PDF extraction (higher cost)")

    # Convert PDF pages to images
    images = convert_from_bytes(
        pdf_bytes,
        dpi=150,
        fmt='jpeg',
        first_page=1,
        last_page=max_pages
    )

    # Convert images to base64 content blocks
    image_content = []
    for i, img in enumerate(images[:max_pages]):
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=85)
        img_bytes = img_byte_arr.getvalue()
        base64_image = base64.standard_b64encode(img_bytes).decode('utf-8')

        image_content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": base64_image
            }
        })

    extraction_prompt = """
    Extract the following information from this property brochure PDF:

    Required Fields:
    1. project_name: Official project name
    2. developer_name: Developer/builder name
    3. location: Full location (area, city, country)
    4. starting_price: Starting price (extract number and currency)
    5. bedrooms: Available bedroom configurations (e.g., "1BR, 2BR, 3BR")
    6. project_type: Type of project (e.g., "Residential", "Commercial", "Mixed-use")
    7. completion_date: Expected completion date or year
    8. amenities: List of all amenities mentioned
    9. contact_info: Phone, email, website if available

    Optional Fields:
    10. area_range: Property sizes (in sq ft or sq m)
    11. payment_plan: Payment plan details if mentioned
    12. unique_features: Key unique selling points

    Return ONLY valid JSON without any markdown formatting or code blocks.
    """

    try:
        response = await anthropic_service._call_with_retry(
            anthropic_service.client.messages.create,
            model=anthropic_service.model,
            max_tokens=4096,
            system="You are a precise data extraction assistant. Return only valid JSON.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        *image_content,
                        {"type": "text", "text": extraction_prompt}
                    ]
                }
            ]
        )

        extracted_text = response.content[0].text
        extracted_text = _clean_json_response(extracted_text)
        extracted_data = json.loads(extracted_text)

        # Mark as vision-extracted for cost tracking
        extracted_data["_extraction_method"] = "claude_vision_fallback"
        extracted_data["_pages_processed"] = len(images)

        logger.info(f"Vision extraction complete for: {extracted_data.get('project_name', 'Unknown')}")

        return extracted_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        raise ValueError("Invalid JSON response from Claude")
    except Exception as e:
        logger.error(f"Vision PDF extraction failed: {e}")
        raise

def _clean_json_response(text: str) -> str:
    """Clean JSON response from Claude"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        if lines and lines[0].strip().lower() == "json":
            lines = lines[1:]
        text = "\n".join(lines)
    return text.strip()
```

## Complete Processing Pipeline

Orchestrate the hybrid extraction pipeline.

```python
# backend/app/services/pdf_processor.py
from typing import Dict, Any, List
from app.services.pdf_text_extraction import (
    extract_text_from_pdf,
    extract_images_from_pdf,
    parse_project_data_from_text
)
from app.services.pdf_vision_extraction import extract_project_data_with_vision
from app.services.image_classification import classify_images_batch
from app.services.watermark_detection import detect_watermark
from app.services.floor_plan_extraction import extract_floor_plan_data
from app.services.content_generation import generate_seo_content
from app.services.qa_validation import validate_extracted_data
from app.core.logging import logger
import asyncio

async def process_pdf_brochure(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Complete hybrid processing pipeline for PDF brochures.

    1. Extract text with pymupdf4llm (FREE)
    2. Extract images with PyMuPDF (FREE)
    3. If text extraction fails, fall back to vision (PAID)
    4. Classify images with Claude (PAID)
    5. Detect watermarks with Claude (PAID)
    6. Extract floor plan data with Claude (PAID)
    7. Generate SEO content with Claude (PAID)
    8. Validate with Claude (PAID)

    Args:
        pdf_bytes: PDF file as bytes

    Returns:
        Complete processed project data
    """

    result = {
        "extraction": {},
        "images": [],
        "floor_plans": [],
        "content": {},
        "validation": {},
        "costs": {
            "text_extraction": 0.0,
            "image_extraction": 0.0,
            "image_classification": 0.0,
            "watermark_detection": 0.0,
            "floor_plan_extraction": 0.0,
            "content_generation": 0.0,
            "validation": 0.0,
            "total": 0.0
        }
    }

    # Step 1: Extract text (FREE)
    logger.info("Step 1: Extracting text with pymupdf4llm...")
    text_result = extract_text_from_pdf(pdf_bytes)

    # Step 2: Parse project data from text (FREE)
    project_data = parse_project_data_from_text(text_result["text"])

    # Check if text extraction was successful
    min_required_fields = ["project_name", "starting_price"]
    has_required = all(project_data.get(f) for f in min_required_fields)

    if not has_required and len(text_result["text"]) < 500:
        # Fallback to vision extraction (PAID)
        logger.warning("Text extraction insufficient, using vision fallback...")
        project_data = await extract_project_data_with_vision(pdf_bytes)
        result["costs"]["text_extraction"] = 0.10  # Estimate

    result["extraction"] = project_data

    # Step 3: Extract images (FREE)
    logger.info("Step 2: Extracting images with PyMuPDF...")
    images = extract_images_from_pdf(pdf_bytes)

    # Step 4: Classify images (PAID - ~$0.003/image)
    logger.info("Step 3: Classifying images with Claude...")
    image_bytes_list = [img["bytes"] for img in images]
    categories = await classify_images_batch(image_bytes_list)

    for img, category in zip(images, categories):
        img["category"] = category

    result["images"] = images
    result["costs"]["image_classification"] = len(images) * 0.003

    # Step 5: Detect watermarks on selected images (PAID)
    logger.info("Step 4: Detecting watermarks...")
    images_to_check = [img for img in images if img["category"] in ["interior", "exterior", "amenity"]][:10]

    for img in images_to_check:
        watermark_result = await detect_watermark(img["bytes"])
        img["watermark"] = watermark_result

    result["costs"]["watermark_detection"] = len(images_to_check) * 0.003

    # Step 6: Extract floor plan data (PAID)
    logger.info("Step 5: Extracting floor plan data...")
    floor_plans = [img for img in images if img["category"] == "floor_plan"]

    for fp in floor_plans:
        fp_data = await extract_floor_plan_data(fp["bytes"])
        fp["extracted_data"] = fp_data

    result["floor_plans"] = floor_plans
    result["costs"]["floor_plan_extraction"] = len(floor_plans) * 0.01

    # Step 7: Generate SEO content (PAID)
    logger.info("Step 6: Generating SEO content...")
    content = await generate_seo_content(project_data)
    result["content"] = content
    result["costs"]["content_generation"] = 0.02

    # Step 8: Validate (PAID)
    logger.info("Step 7: Validating extracted data...")
    validation = await validate_extracted_data(project_data)
    result["validation"] = validation
    result["costs"]["validation"] = 0.01

    # Calculate total cost
    result["costs"]["total"] = sum(
        v for k, v in result["costs"].items() if k != "total"
    )

    logger.info(f"Processing complete. Total cost: ${result['costs']['total']:.4f}")

    return result
```

## Rate Limiting and Quotas

### Anthropic Rate Limits (Tier-Based)

| Tier | Requests/min | Input TPM | Output TPM |
|------|--------------|-----------|------------|
| Free | 5 | 20,000 | 4,000 |
| Build (Tier 1) | 50 | 40,000 | 8,000 |
| Build (Tier 2) | 1,000 | 80,000 | 16,000 |
| Scale | 4,000 | 400,000 | 80,000 |
| Enterprise | Custom | Custom | Custom |

### Rate Limiting Implementation

```python
# backend/app/services/rate_limiter.py
import asyncio
from datetime import datetime, timedelta
from collections import deque

class RateLimiter:
    """Token bucket rate limiter for Anthropic API calls"""

    def __init__(self, requests_per_minute: int = 50, tokens_per_minute: int = 40_000):
        self.rpm_limit = requests_per_minute
        self.tpm_limit = tokens_per_minute
        self.request_times = deque()
        self.token_usage = deque()
        self._lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int = 4000):
        """Wait until rate limit allows another request"""
        async with self._lock:
            now = datetime.now()
            one_minute_ago = now - timedelta(minutes=1)

            # Remove old entries
            while self.request_times and self.request_times[0] < one_minute_ago:
                self.request_times.popleft()

            while self.token_usage and self.token_usage[0][0] < one_minute_ago:
                self.token_usage.popleft()

            # Calculate current usage
            current_requests = len(self.request_times)
            current_tokens = sum(tokens for _, tokens in self.token_usage)

            # Wait if limits exceeded
            if current_requests >= self.rpm_limit or current_tokens + estimated_tokens > self.tpm_limit:
                wait_time = 60 - (now - self.request_times[0]).total_seconds()
                await asyncio.sleep(max(0, wait_time))
                return await self.acquire(estimated_tokens)

            # Record this request
            self.request_times.append(now)
            self.token_usage.append((now, estimated_tokens))

    def record_usage(self, actual_tokens: int):
        """Update with actual token usage after request"""
        if self.token_usage:
            timestamp, _ = self.token_usage[-1]
            self.token_usage[-1] = (timestamp, actual_tokens)

# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=50, tokens_per_minute=40_000)
```

## Cost Summary

| Component | Method | Cost per Project |
|-----------|--------|------------------|
| Text extraction | pymupdf4llm | FREE |
| Image extraction | PyMuPDF | FREE |
| Image classification | Claude Sonnet 4.5 | ~$0.03 (10 images) |
| Watermark detection | Claude Sonnet 4.5 | ~$0.03 (10 images) |
| Floor plan OCR | Claude Sonnet 4.5 | ~$0.03 (3 floor plans) |
| Content generation | Claude Sonnet 4.5 | ~$0.02 |
| QA validation | Claude Sonnet 4.5 | ~$0.01 |
| **Total (typical)** | Hybrid | **~$0.12-0.20** |

Vision-only approach would cost ~$1.00-2.00 per project (5-10x more).

## Error Handling

```python
# backend/app/services/error_handler.py
from anthropic import (
    RateLimitError,
    APIError,
    APITimeoutError,
    APIConnectionError,
    AuthenticationError,
    BadRequestError
)
import asyncio
from app.core.logging import logger

async def handle_anthropic_errors(func, *args, **kwargs):
    """Handle all Anthropic API errors with appropriate retry logic"""

    max_retries = 3
    base_delay = 60

    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)

        except AuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            raise

        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) * base_delay
            logger.warning(f"Rate limit hit, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(wait_time)

        except APITimeoutError as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Request timeout, retrying (attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(10)

        except APIConnectionError as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Connection error, retrying (attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(30)

        except BadRequestError as e:
            logger.error(f"Bad request: {e}")
            raise

        except APIError as e:
            if attempt == 0:
                logger.warning(f"API error, retrying once: {e}")
                await asyncio.sleep(30)
            else:
                logger.error(f"API error after retry: {e}")
                raise
```

## Security Considerations

1. **API Key Protection**
   - Store in Secret Manager only
   - Never log API keys
   - Rotate keys every 90 days

2. **Data Privacy**
   - Anthropic does not train on API data by default
   - Review Anthropic's data usage policy
   - Redact sensitive information before API calls

3. **Input Validation**
   - Validate file sizes before processing
   - Check file types (PDF, JPEG, PNG only)
   - Limit input length to prevent abuse

## Migration Notes from OpenAI

| Feature | OpenAI | Anthropic |
|---------|--------|-----------|
| Model selection | GPT-4 Turbo (text), GPT-4o (vision) | Claude Sonnet 4.5 (both) |
| Vision format | `image_url` with base64 data URL | `image` with separate source object |
| JSON mode | `response_format={"type": "json_object"}` | Instruct in prompt |
| System message | `messages[0].role = "system"` | Separate `system` parameter |
| Response access | `response.choices[0].message.content` | `response.content[0].text` |

## Next Steps

- Set up [Google Sheets Integration](GOOGLE_SHEETS_INTEGRATION.md) for content export
- Configure [Google Drive Integration](GOOGLE_DRIVE_INTEGRATION.md) for file sharing
- Review [PDF Text Extraction](../02-modules/PDF_TEXT_EXTRACTION.md) for pymupdf4llm details

## References

### External Documentation
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Claude Vision Guide](https://docs.anthropic.com/en/docs/vision)
- [pymupdf4llm Documentation](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)

### Internal Documentation
- [Content Generation Module](../02-modules/CONTENT_GENERATION.md)
- [Material Preparation Module](../02-modules/MATERIAL_PREPARATION.md)
- [Prompt Library](../02-modules/PROMPT_LIBRARY.md)
