"""
Vision Extractor Service

Hybrid per-page text extraction from PDF page renders.

Text-rich pages (>= 200 chars of native text from PyMuPDF) use the native text
directly -- free, lossless, no OCR errors. Visual pages (< 200 chars) get
Vision OCR via Claude. This hybrid routing saves 50-80% of Vision API cost
and eliminates digit transposition errors on digital text.
"""

import asyncio
import logging
from dataclasses import dataclass, field

from app.integrations.anthropic_client import anthropic_service
from app.utils.pdf_helpers import ExtractedImage, create_llm_optimized
from app.utils.token_counter import calculate_cost

logger = logging.getLogger(__name__)

TEXT_RICH_THRESHOLD = 200  # chars -- pages above this use native text

OCR_PROMPT = """Read all TEXT CONTENT from this page of a real estate property brochure.

Include:
- Body text, headings, subheadings, and paragraphs
- Stylized/decorative text rendered as graphics
- Text overlaid on images (but NOT labels on maps or diagrams)
- Small print, footnotes, disclaimers, legal text
- Numbers in structured data (prices, areas, unit counts)
- Contact information, website URLs

IMPORTANT exclusions:
- Do NOT read labels from maps, satellite imagery, or cartographic illustrations
- Do NOT read hotel names, landmark names, or road names from map overlays
- Do NOT read navigation UI elements (zoom controls, compass, etc.)
- If a page is primarily a map/aerial view, extract ONLY the text labels that are
  part of the brochure design (e.g. proximity callouts like "5 min to X"), not
  every label visible on the map itself.

Output the text in reading order (top to bottom, left to right).
Preserve the original formatting where possible (line breaks between sections).
Read text EXACTLY as displayed -- do not paraphrase, correct spelling, or interpret.
If a section has no readable text, skip it.

Return ONLY the extracted text, nothing else."""


@dataclass
class PageExtractionResult:
    """Raw text extracted from a single PDF page via Vision OCR or native text."""

    page_number: int
    raw_text: str = ""
    token_usage: dict = field(default_factory=dict)
    cost: float = 0.0


class VisionExtractor:
    """
    Extracts raw text from PDF page renders using hybrid routing.

    Text-rich pages use native text from PyMuPDF (free, lossless).
    Visual pages get Vision OCR via Claude (parallel, semaphore-bounded).
    """

    MAX_CONCURRENT = 5
    MAX_PAGES = 30

    @staticmethod
    def classify_pages(
        page_char_counts: dict[int, int],
        threshold: int = TEXT_RICH_THRESHOLD,
    ) -> tuple[set[int], set[int]]:
        """Classify pages as text-rich or visual based on native text char count.

        Args:
            page_char_counts: {page_number: char_count} from PDFProcessor.
            threshold: Minimum chars for text-rich classification.

        Returns:
            (text_rich_pages, visual_pages) as sets of page numbers.
        """
        text_rich = set()
        visual = set()
        for page_num, count in page_char_counts.items():
            if count >= threshold:
                text_rich.add(page_num)
            else:
                visual.add(page_num)
        return text_rich, visual

    async def extract_pages(
        self,
        page_renders: list[ExtractedImage],
        template_type: str = "aggregators",
        page_text_map: dict[int, str] | None = None,
        page_char_counts: dict[int, int] | None = None,
    ) -> list[PageExtractionResult]:
        """Extract text from page renders with per-page routing.

        Text-rich pages use native text directly (no Vision API call).
        Visual pages get Vision OCR.

        Args:
            page_renders: List of page render images from PDFProcessor.
            template_type: Template type (reserved for future use).
            page_text_map: {page_number: native_text} from PDFProcessor.
            page_char_counts: {page_number: char_count} from PDFProcessor.

        Returns:
            List of PageExtractionResult, one per successfully processed page.
        """
        renders = page_renders[: self.MAX_PAGES]
        if not renders:
            return []

        # Classify pages
        text_rich_pages = set()
        if page_char_counts:
            text_rich_pages, _ = self.classify_pages(page_char_counts)

        results: list[PageExtractionResult] = []

        # Text-rich pages: use native text directly (free, lossless)
        visual_renders: list[ExtractedImage] = []
        for render in renders:
            pn = render.metadata.page_number
            if pn in text_rich_pages and page_text_map and pn in page_text_map:
                results.append(PageExtractionResult(
                    page_number=pn,
                    raw_text=page_text_map[pn],
                    token_usage={"input": 0, "output": 0},
                    cost=0.0,
                ))
            else:
                visual_renders.append(render)

        # Visual pages: Vision OCR (parallel with semaphore)
        if visual_renders:
            sem = asyncio.Semaphore(self.MAX_CONCURRENT)

            async def _extract_one(render: ExtractedImage) -> PageExtractionResult:
                async with sem:
                    return await self._extract_page(render)

            vision_results = await asyncio.gather(
                *[_extract_one(r) for r in visual_renders],
                return_exceptions=True,
            )

            for i, r in enumerate(vision_results):
                if isinstance(r, BaseException):
                    logger.error(
                        "Vision OCR failed for page %d: %s",
                        visual_renders[i].metadata.page_number, r,
                    )
                else:
                    results.append(r)

        text_rich_count = len(renders) - len(visual_renders)
        logger.info(
            "Page routing: %d text-rich (native), %d visual (Vision OCR), %d/%d succeeded",
            text_rich_count,
            len(visual_renders),
            len(results),
            len(renders),
        )
        return results

    async def _extract_page(self, render: ExtractedImage) -> PageExtractionResult:
        """Extract raw text from a single page image via Vision OCR."""
        # Use smaller optimization (768px) for text extraction -- saves ~44% input tokens
        image_bytes = (
            create_llm_optimized(
                render.image_bytes, max_dim=768, fmt="JPEG", quality=80
            )
            or render.llm_optimized_bytes
            or render.image_bytes
        )
        media_type = "image/jpeg"

        response = await anthropic_service.vision_completion(
            image_bytes=image_bytes,
            prompt=OCR_PROMPT,
            media_type=media_type,
            max_tokens=4096,
        )

        raw_text = response.content[0].text.strip()
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        return PageExtractionResult(
            page_number=render.metadata.page_number,
            raw_text=raw_text,
            token_usage={"input": input_tokens, "output": output_tokens},
            cost=calculate_cost(input_tokens, output_tokens),
        )

    @staticmethod
    def concatenate_page_text(page_results: list[PageExtractionResult]) -> str:
        """Concatenate raw text from all pages into a single document string.

        Args:
            page_results: Per-page OCR results from extract_pages().

        Returns:
            All page text joined with page separators.
        """
        if not page_results:
            return ""

        parts = []
        for pr in sorted(page_results, key=lambda r: r.page_number):
            if pr.raw_text.strip():
                parts.append(f"--- Page {pr.page_number} ---\n{pr.raw_text}")

        return "\n\n".join(parts)
