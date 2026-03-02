"""
Watermark Detector Service (DEV-WATERMARK-001 - Detection)

Uses Claude Vision to detect watermarks in images and extract
bounding box coordinates for downstream removal.
"""

import base64
import io
import json
import logging
from dataclasses import dataclass
from typing import Optional

import anthropic
from PIL import Image

from app.config.settings import get_settings
from app.utils.pdf_helpers import create_llm_optimized

logger = logging.getLogger(__name__)

MAX_RETRIES = 3

WATERMARK_DETECTION_PROMPT = """Analyze this real estate image for watermarks.

A watermark is any overlaid text or logo not part of the original scene
(e.g., agency names, "SAMPLE", stock photo marks, copyright notices).

Return ONLY valid JSON (no markdown fences):
{
  "has_watermark": true,
  "confidence": 0.95,
  "watermarks": [
    {
      "text": "Agency Name",
      "x": 100,
      "y": 200,
      "width": 300,
      "height": 50,
      "type": "text"
    }
  ]
}

If no watermark is detected:
{
  "has_watermark": false,
  "confidence": 0.95,
  "watermarks": []
}

Coordinates are in pixels relative to the image dimensions.
Types: "text", "logo", "pattern", "border"."""


@dataclass
class WatermarkRegion:
    """Detected watermark bounding box."""
    x: int
    y: int
    width: int
    height: int
    text: str = ""
    region_type: str = "text"
    confidence: float = 0.0


@dataclass
class DetectionResult:
    """Result of watermark detection for a single image."""
    has_watermark: bool = False
    confidence: float = 0.0
    regions: list = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.regions is None:
            self.regions = []


class WatermarkDetector:
    """
    Detects watermarks in images using Claude Vision API.

    Analyzes images for overlaid text, logos, or patterns that are
    not part of the original scene content. Returns bounding box
    coordinates for each detected watermark region.
    """

    def __init__(self, api_key: Optional[str] = None,
                 model: Optional[str] = None):
        settings = get_settings()
        self._client = anthropic.AsyncAnthropic(
            api_key=api_key or settings.ANTHROPIC_API_KEY,
        )
        self._model = model or settings.ANTHROPIC_MODEL

    async def detect(self, image_bytes: bytes) -> DetectionResult:
        """
        Detect watermarks in an image.

        Args:
            image_bytes: Raw image bytes.

        Returns:
            DetectionResult with watermark locations.
        """
        # Create LLM-optimized version for token efficiency
        optimized = create_llm_optimized(image_bytes, max_dim=1024)
        img_bytes = optimized if optimized else image_bytes

        b64_image = base64.b64encode(img_bytes).decode("utf-8")
        media_type = self._detect_media_type(img_bytes)

        # Get original dimensions for coordinate scaling
        orig_w, orig_h = self._get_dimensions(image_bytes)
        opt_w, opt_h = self._get_dimensions(img_bytes)

        for attempt in range(MAX_RETRIES):
            try:
                response = await self._client.messages.create(
                    model=self._model,
                    max_tokens=500,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": b64_image,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": WATERMARK_DETECTION_PROMPT,
                                },
                            ],
                        }
                    ],
                )

                result = self._parse_response(response)

                # Scale coordinates from optimized dims back to original
                if opt_w > 0 and orig_w > 0 and opt_w != orig_w:
                    scale_x = orig_w / opt_w
                    scale_y = orig_h / opt_h
                    for region in result.regions:
                        region.x = int(region.x * scale_x)
                        region.y = int(region.y * scale_y)
                        region.width = int(region.width * scale_x)
                        region.height = int(region.height * scale_y)

                return result

            except anthropic.APIError as e:
                logger.warning(
                    "Watermark detection API error (attempt %d/%d): %s",
                    attempt + 1, MAX_RETRIES, e,
                )
                if attempt == MAX_RETRIES - 1:
                    return DetectionResult(
                        has_watermark=False,
                        confidence=0.0,
                        error=f"API error after {MAX_RETRIES} retries: {e}",
                    )

        return DetectionResult()

    async def detect_batch(
        self, images: list[bytes]
    ) -> list[DetectionResult]:
        """Detect watermarks in a batch of images."""
        results = []
        for img_bytes in images:
            result = await self.detect(img_bytes)
            results.append(result)
        return results

    def _parse_response(
        self, response: anthropic.types.Message
    ) -> DetectionResult:
        """Parse Claude's watermark detection response."""
        try:
            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            data = json.loads(text)

            regions = []
            for wm in data.get("watermarks", []):
                regions.append(WatermarkRegion(
                    x=int(wm.get("x", 0)),
                    y=int(wm.get("y", 0)),
                    width=int(wm.get("width", 0)),
                    height=int(wm.get("height", 0)),
                    text=wm.get("text", ""),
                    region_type=wm.get("type", "text"),
                    confidence=float(data.get("confidence", 0.0)),
                ))

            return DetectionResult(
                has_watermark=data.get("has_watermark", False),
                confidence=float(data.get("confidence", 0.0)),
                regions=regions,
            )

        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.warning("Failed to parse watermark detection response: %s", e)
            return DetectionResult(
                has_watermark=False,
                confidence=0.0,
                error=f"Parse error: {e}",
            )

    def _detect_media_type(self, image_bytes: bytes) -> str:
        """Detect MIME type from image bytes."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            fmt = (img.format or "jpeg").lower()
            if fmt == "jpg":
                fmt = "jpeg"
            return f"image/{fmt}"
        except Exception:
            return "image/jpeg"

    def _get_dimensions(self, image_bytes: bytes) -> tuple[int, int]:
        """Get image width and height."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            return img.size
        except Exception:
            return (0, 0)
