# Phase 4: Pipeline Output Optimization Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 8 pipeline output issues identified during first test run to improve image extraction quality, folder organization, and data accessibility.

**Architecture:** Modifications to existing services (output_organizer.py, image_optimizer.py, drive_client.py, pdf_processor.py, floor_plan_extractor.py) with backward-compatible changes. No database schema changes required.

**Tech Stack:** Python 3.11, PyMuPDF, PIL/Pillow, Google Drive API

---

## Issue Summary

| # | Issue | Current State | Target State | Priority |
|---|-------|---------------|--------------|----------|
| 1 | Empty Source/Images folders | Drive creates but never populates | Remove or populate with purpose | Medium |
| 2 | ZIP only in Output folder | All assets zipped | Also store organized files | Medium |
| 3 | Full-page extraction bug | Some images extracted with entire page | Improve embedded extraction, skip page renders when embedded covers content | High |
| 4 | Generic image names | `category_001.webp` | `001-interior-modern-living-room.webp` | High |
| 5 | Logo extraction bug | Page with logo extracted as logo | Better logo detection: size, position, aspect ratio heuristics | High |
| 6 | Mixed original/optimized | Same folder contains both tiers | Separate `/original/` and `/optimized/` folders | High |
| 7 | Floor plan data-image disconnect | JSON separate from images | Embed image reference in JSON, or create consolidated file per floor plan | Critical |
| 8 | No raw text JSON output | pymupdf4llm text discarded after use | Save `extracted_text.json` for verification and reprocessing | Medium |

---

## Task 1: Save pymupdf4llm Extracted Text to JSON

**Files:**
- Modify: `backend/app/services/pdf_processor.py:102-104`
- Modify: `backend/app/services/output_organizer.py:198-213`
- Modify: `backend/app/utils/pdf_helpers.py` (ExtractionResult dataclass)
- Test: `backend/tests/test_pdf_processor.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_pdf_processor.py
@pytest.mark.asyncio
async def test_extraction_includes_text_map_in_result(sample_pdf_bytes):
    """Verify page_text_map is populated after extraction."""
    processor = PDFProcessor()
    result = await processor.extract_all(sample_pdf_bytes)

    assert result.page_text_map is not None
    assert len(result.page_text_map) > 0
    # Verify it's a dict mapping int page numbers to str text
    for page_num, text in result.page_text_map.items():
        assert isinstance(page_num, int)
        assert isinstance(text, str)
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_pdf_processor.py::test_extraction_includes_text_map_in_result -v`
Expected: PASS (already working - this validates current behavior)

**Step 3: Add extracted_text.json to output package**

Modify `output_organizer.py` after line 201:

```python
# Add extracted text from PDF if available
if hasattr(optimization_result, 'page_text_map') and optimization_result.page_text_map:
    text_json = json.dumps(
        {
            "pages": [
                {"page": k, "text": v}
                for k, v in sorted(optimization_result.page_text_map.items())
            ]
        },
        indent=2,
        ensure_ascii=False,
    )
    zf.writestr("extracted_text.json", text_json)
```

**Step 4: Update OutputOrganizer.create_package signature**

```python
def create_package(
    self,
    optimization_result: OptimizationResult,
    project_name: str = "",
    floor_plan_data: Optional[list] = None,
    page_text_map: Optional[dict[int, str]] = None,  # NEW
) -> tuple[bytes, OutputManifest]:
```

**Step 5: Write test for extracted_text.json in ZIP**

```python
# backend/tests/test_output_organizer.py
def test_create_package_includes_extracted_text():
    """Verify extracted_text.json is included when page_text_map provided."""
    organizer = OutputOrganizer()
    mock_result = OptimizationResult(images=[])
    page_text_map = {1: "Page one content", 2: "Page two content"}

    zip_bytes, manifest = organizer.create_package(
        mock_result,
        project_name="test",
        page_text_map=page_text_map,
    )

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        assert "extracted_text.json" in zf.namelist()
        text_data = json.loads(zf.read("extracted_text.json"))
        assert len(text_data["pages"]) == 2
```

**Step 6: Run test to verify it passes**

Run: `pytest backend/tests/test_output_organizer.py::test_create_package_includes_extracted_text -v`
Expected: PASS

**Step 7: Commit**

```bash
git add backend/app/services/output_organizer.py backend/tests/test_output_organizer.py
git commit -m "$(cat <<'EOF'
feat: save pymupdf4llm extracted text to extracted_text.json in output ZIP

Allows verification of extracted content against PDF brochure and enables
reprocessing without re-extracting from PDF.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Separate Original and Optimized Image Folders

**Files:**
- Modify: `backend/app/services/output_organizer.py:124-196`
- Test: `backend/tests/test_output_organizer.py`

**Current structure:**
```
/interiors/interior_001.webp
/interiors/interior_001.jpg
/llm/interiors/interior_001.webp
```

**Target structure:**
```
/original/interiors/interior_001.webp
/original/interiors/interior_001.jpg
/optimized/interiors/interior_001.webp    (LLM tier)
/optimized/interiors/interior_001.jpg
```

**Step 1: Write the failing test**

```python
# backend/tests/test_output_organizer.py
def test_create_package_separates_original_and_optimized():
    """Verify original and optimized images are in separate top-level folders."""
    organizer = OutputOrganizer()
    # Create mock OptimizedImage with all tiers
    mock_img = OptimizedImage(
        original_webp=b"webp_original",
        original_jpg=b"jpg_original",
        llm_webp=b"webp_llm",
        llm_jpg=b"jpg_llm",
        category="interior",
        file_name="interior_001",
        optimized_width=1000,
        optimized_height=800,
        llm_width=500,
        llm_height=400,
        alt_text="Test image",
    )
    mock_result = OptimizationResult(images=[mock_img])

    zip_bytes, _ = organizer.create_package(mock_result, project_name="test")

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        # Original tier in /original/
        assert "original/interiors/interior_001.webp" in names
        assert "original/interiors/interior_001.jpg" in names
        # Optimized tier in /optimized/
        assert "optimized/interiors/interior_001.webp" in names
        assert "optimized/interiors/interior_001.jpg" in names
        # Old paths should NOT exist
        assert "interiors/interior_001.webp" not in names
        assert "llm/interiors/interior_001.webp" not in names
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_output_organizer.py::test_create_package_separates_original_and_optimized -v`
Expected: FAIL - files are at old paths

**Step 3: Update path generation in output_organizer.py**

Replace lines 132-196 with:

```python
for img in optimization_result.images:
    cat_dir = CATEGORY_DIRS.get(img.category, "other")
    count = category_counts.get(img.category, 0)
    category_counts[img.category] = count + 1

    # Tier 1 (Original): /original/{category}/
    t1_webp_path = f"original/{cat_dir}/{img.file_name}.webp"
    zf.writestr(t1_webp_path, img.original_webp)
    manifest.entries.append(ManifestEntry(
        file_name=f"{img.file_name}.webp",
        category=img.category,
        directory=f"original/{cat_dir}",
        format="webp",
        tier="original",
        width=img.optimized_width,
        height=img.optimized_height,
        file_size=len(img.original_webp),
        alt_text=img.alt_text,
        quality_score=img.quality_score,
    ))
    manifest.tier1_count += 1

    t1_jpg_path = f"original/{cat_dir}/{img.file_name}.jpg"
    zf.writestr(t1_jpg_path, img.original_jpg)
    manifest.entries.append(ManifestEntry(
        file_name=f"{img.file_name}.jpg",
        category=img.category,
        directory=f"original/{cat_dir}",
        format="jpg",
        tier="original",
        width=img.optimized_width,
        height=img.optimized_height,
        file_size=len(img.original_jpg),
        alt_text=img.alt_text,
        quality_score=img.quality_score,
    ))
    manifest.tier1_count += 1

    # Tier 2 (LLM-Optimized): /optimized/{category}/
    t2_webp_path = f"optimized/{cat_dir}/{img.file_name}.webp"
    zf.writestr(t2_webp_path, img.llm_webp)
    manifest.entries.append(ManifestEntry(
        file_name=f"{img.file_name}.webp",
        category=img.category,
        directory=f"optimized/{cat_dir}",
        format="webp",
        tier="llm_optimized",
        width=img.llm_width,
        height=img.llm_height,
        file_size=len(img.llm_webp),
        alt_text=img.alt_text,
    ))
    manifest.tier2_count += 1

    t2_jpg_path = f"optimized/{cat_dir}/{img.file_name}.jpg"
    zf.writestr(t2_jpg_path, img.llm_jpg)
    manifest.entries.append(ManifestEntry(
        file_name=f"{img.file_name}.jpg",
        category=img.category,
        directory=f"optimized/{cat_dir}",
        format="jpg",
        tier="llm_optimized",
        width=img.llm_width,
        height=img.llm_height,
        file_size=len(img.llm_jpg),
        alt_text=img.alt_text,
    ))
    manifest.tier2_count += 1
```

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_output_organizer.py::test_create_package_separates_original_and_optimized -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/output_organizer.py backend/tests/test_output_organizer.py
git commit -m "$(cat <<'EOF'
refactor: separate original and optimized images into distinct folders

Changes ZIP structure from flat category folders to:
- /original/{category}/ for full-quality images
- /optimized/{category}/ for LLM-optimized versions

Makes it clear which images are for archival vs web/AI use.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Implement Semantic Image Naming

**Files:**
- Modify: `backend/app/services/image_optimizer.py:110-113`
- Modify: `backend/app/models/enums.py` (add helper if needed)
- Test: `backend/tests/test_image_optimizer.py`

**Current:** `category_001.webp`
**Target:** `001-interior-modern-living-room-with-floor-to-ceiling-windows.webp`

**Naming format:** `{sequence:03d}-{category}-{slug_from_alt_text}.{ext}`
- Max 80 characters for filename (excluding extension)
- Slugify alt_text: lowercase, hyphens, no special chars
- Truncate intelligently at word boundary

**Step 1: Write the failing test**

```python
# backend/tests/test_image_optimizer.py
def test_semantic_filename_generation():
    """Verify image filenames include semantic context from alt_text."""
    optimizer = ImageOptimizer()

    # Create simple test image bytes
    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    test_bytes = buf.getvalue()

    images = [
        (test_bytes, "interior", "Spacious living room with floor-to-ceiling windows"),
        (test_bytes, "exterior", "Modern building facade at sunset"),
    ]

    result = asyncio.run(optimizer.optimize_batch(images))

    assert result.images[0].file_name == "001-interior-spacious-living-room-with-floor-to-ceiling-windows"
    assert result.images[1].file_name == "001-exterior-modern-building-facade-at-sunset"
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_image_optimizer.py::test_semantic_filename_generation -v`
Expected: FAIL - file_name is "interior_001"

**Step 3: Add slugify helper function**

Add to `image_optimizer.py` after imports:

```python
import re
import unicodedata

def slugify_alt_text(text: str, max_length: int = 60) -> str:
    """
    Convert alt_text to URL-safe slug for filename.

    - Lowercase
    - Replace spaces and special chars with hyphens
    - Remove consecutive hyphens
    - Truncate at word boundary
    """
    if not text:
        return ""

    # Normalize unicode and lowercase
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()

    # Replace non-alphanumeric with hyphen
    text = re.sub(r"[^a-z0-9]+", "-", text)

    # Remove leading/trailing hyphens
    text = text.strip("-")

    # Truncate at word boundary
    if len(text) > max_length:
        truncated = text[:max_length]
        # Find last hyphen to avoid cutting mid-word
        last_hyphen = truncated.rfind("-")
        if last_hyphen > max_length // 2:
            text = truncated[:last_hyphen]
        else:
            text = truncated

    return text
```

**Step 4: Update filename generation**

Replace lines 110-113:

```python
# Generate semantic filename
count = category_counters.get(category, 0) + 1
category_counters[category] = count
slug = slugify_alt_text(alt_text)
if slug:
    file_name = f"{count:03d}-{category}-{slug}"
else:
    file_name = f"{count:03d}-{category}"

# Ensure total filename (without extension) <= 80 chars
if len(file_name) > 80:
    file_name = file_name[:80].rstrip("-")
```

**Step 5: Run test to verify it passes**

Run: `pytest backend/tests/test_image_optimizer.py::test_semantic_filename_generation -v`
Expected: PASS

**Step 6: Add edge case tests**

```python
def test_semantic_filename_truncation():
    """Verify long alt_text is truncated at word boundary."""
    slug = slugify_alt_text(
        "This is a very long description that exceeds the maximum allowed length for filenames",
        max_length=40
    )
    assert len(slug) <= 40
    assert not slug.endswith("-")

def test_semantic_filename_empty_alt_text():
    """Verify fallback when alt_text is empty."""
    optimizer = ImageOptimizer()
    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    result = asyncio.run(optimizer.optimize_batch([(buf.getvalue(), "logo", "")]))

    assert result.images[0].file_name == "001-logo"
```

**Step 7: Run all optimizer tests**

Run: `pytest backend/tests/test_image_optimizer.py -v`
Expected: All PASS

**Step 8: Commit**

```bash
git add backend/app/services/image_optimizer.py backend/tests/test_image_optimizer.py
git commit -m "$(cat <<'EOF'
feat: implement semantic image naming using alt_text

Changes filename format from category_001 to:
001-{category}-{slugified-alt-text}

Slugifies alt_text to URL-safe format, truncates at word boundary.
Max 80 chars for filename. Falls back to sequence-category if no alt_text.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Fix Logo Extraction (Full-Page Issue)

**Files:**
- Modify: `backend/app/services/image_classifier.py:46-62` (prompt)
- Modify: `backend/app/services/image_classifier.py` (add logo validation)
- Test: `backend/tests/test_image_classifier.py`

**Problem:** Full pages containing logos are classified as "logo" instead of the extracted logo itself.

**Solution:** Add logo-specific validation based on:
1. Aspect ratio (logos are typically more square or horizontal, not page-shaped)
2. Size relative to page (logos are small; page renders are large)
3. Add explicit instruction to Claude prompt

**Step 1: Write the failing test**

```python
# backend/tests/test_image_classifier.py
@pytest.mark.asyncio
async def test_full_page_with_logo_not_classified_as_logo(mock_anthropic):
    """Verify full page renders are not misclassified as logos."""
    classifier = ImageClassifier()

    # Mock a page-sized image (portrait aspect ratio typical of PDF pages)
    page_img = Image.new("RGB", (2480, 3508), color="white")  # A4 at 300 DPI
    # Draw a small "logo" area
    from PIL import ImageDraw
    draw = ImageDraw.Draw(page_img)
    draw.rectangle([100, 100, 300, 200], fill="blue")  # Small logo area

    buf = io.BytesIO()
    page_img.save(buf, format="PNG")

    # Mock classification response
    mock_anthropic.return_value = Mock(
        content=[Mock(text='{"category": "logo", "confidence": 0.7, "reasoning": "Contains logo", "alt_text": "Logo"}')]
    )

    result = classifier._validate_logo_classification(
        buf.getvalue(),
        ClassificationResult(category=ImageCategory.LOGO, confidence=0.7)
    )

    # Should reject as logo due to page-like dimensions
    assert result.category != ImageCategory.LOGO
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_image_classifier.py::test_full_page_with_logo_not_classified_as_logo -v`
Expected: FAIL - method doesn't exist

**Step 3: Update classification prompt**

Replace `CLASSIFICATION_PROMPT` at line 46:

```python
CLASSIFICATION_PROMPT = """Classify this real estate image into one category:
- interior: Indoor spaces (bedrooms, living rooms, kitchens, bathrooms)
- exterior: Building facade, outdoor views, balconies
- amenity: Pool, gym, playground, common areas
- floor_plan: Architectural floor plans or unit layouts
- logo: Developer or project logos ONLY if the image IS the logo itself (not a page containing a logo)
- location_map: Maps showing location or nearby landmarks
- master_plan: Site plan or development layout
- other: Text-only, decorative, full document pages, or unclassifiable

IMPORTANT for logos:
- Only classify as "logo" if the image IS a logo graphic (compact, designed element)
- If this is a full page or document that happens to contain a logo, classify as "other"
- Logos are typically small, have transparent/simple backgrounds, aspect ratio close to 1:1 or 2:1

Return ONLY valid JSON (no markdown fences):
{
  "category": "interior",
  "confidence": 0.95,
  "reasoning": "Shows a modern living room with furniture",
  "alt_text": "Spacious living room with floor-to-ceiling windows"
}"""
```

**Step 4: Add logo validation method**

Add after `_parse_classification` method:

```python
def _validate_logo_classification(
    self, image_bytes: bytes, classification: ClassificationResult
) -> ClassificationResult:
    """
    Post-process logo classifications to filter false positives.

    Rejects logo classification if:
    - Image has page-like aspect ratio (close to A4/Letter: 1:1.4 or taller)
    - Image is very large (> 2000px in either dimension)
    """
    if classification.category != ImageCategory.LOGO:
        return classification

    try:
        img = Image.open(io.BytesIO(image_bytes))
        w, h = img.size
        aspect_ratio = w / h if h > 0 else 1.0

        # Page-like: taller than wide (portrait) or very tall landscape
        is_page_like = aspect_ratio < 0.9 or (h > 2000 and w > 1500)

        # Logos are typically small; page renders are large
        is_large = w > 2000 or h > 2000

        if is_page_like or is_large:
            logger.info(
                "Rejecting logo classification: page-like dimensions %dx%d (ratio=%.2f)",
                w, h, aspect_ratio
            )
            classification.category = ImageCategory.OTHER
            classification.reasoning = f"Rejected logo: page-like dimensions ({w}x{h})"

    except Exception as e:
        logger.warning("Logo validation failed: %s", e)

    return classification
```

**Step 5: Call validation in _classify_single**

After line 254 (return statement), wrap it:

```python
classification = self._parse_classification(response)
classification = self._validate_logo_classification(image.image_bytes, classification)
return classification
```

**Step 6: Run test to verify it passes**

Run: `pytest backend/tests/test_image_classifier.py::test_full_page_with_logo_not_classified_as_logo -v`
Expected: PASS

**Step 7: Commit**

```bash
git add backend/app/services/image_classifier.py backend/tests/test_image_classifier.py
git commit -m "$(cat <<'EOF'
fix: prevent full pages from being misclassified as logos

Adds post-classification validation that rejects logo classification when:
- Image has page-like aspect ratio (portrait or > 2000px)
- Image dimensions suggest a full document page

Also updates Claude prompt to explicitly instruct against classifying
pages containing logos as the logo category.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Fix Image Extraction (Full-Page Capture Bug)

**Files:**
- Modify: `backend/app/services/image_classifier.py:161-180` (page render logic)
- Modify: `backend/app/services/deduplication_service.py` (cross-source comparison)
- Test: `backend/tests/test_image_classifier.py`

**Problem:** Some images are extracted with the entire page when embedded extraction should have sufficed.

**Current behavior:**
1. Extract embedded images
2. Render full page at 300 DPI
3. Compare page render to embedded images from same page
4. If "different enough", keep both

**Issue:** The similarity check isn't catching cases where embedded image IS the main content of the page (with just margins/decorations around it).

**Solution:** Enhance `should_keep_page_render` to:
1. Compare structural similarity (not just hash)
2. Check if embedded image covers >70% of page render content area
3. Skip page render if embedded images fully represent the visual content

**Step 1: Write the failing test**

```python
# backend/tests/test_image_classifier.py
def test_skip_page_render_when_embedded_covers_content():
    """Verify page render is skipped when embedded image covers most of page."""
    # Create a page where embedded image IS the main content
    page_size = (2480, 3508)  # A4 at 300 DPI
    embedded_size = (2200, 3200)  # Image with small margins

    # Embedded image (most of the page)
    embedded = Image.new("RGB", embedded_size, color="blue")
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
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_image_classifier.py::test_skip_page_render_when_embedded_covers_content -v`
Expected: FAIL - currently returns True

**Step 3: Enhance should_keep_page_render**

Update in `deduplication_service.py`:

```python
def should_keep_page_render(
    page_render_bytes: bytes,
    embedded_images: list[bytes],
    similarity_threshold: float = 0.70,
    coverage_threshold: float = 0.70,
) -> bool:
    """
    Determine if a page render should be kept given embedded images from same page.

    Skip page render if:
    1. It's perceptually similar to any embedded image (hash match)
    2. Any embedded image covers >70% of the page render's content area

    Args:
        page_render_bytes: Full page render image bytes
        embedded_images: List of embedded image bytes from same page
        similarity_threshold: Hash similarity threshold (default 0.70)
        coverage_threshold: Minimum coverage ratio to skip page render

    Returns:
        True if page render should be kept, False if redundant
    """
    if not embedded_images:
        return True

    try:
        page_img = Image.open(io.BytesIO(page_render_bytes))
        page_w, page_h = page_img.size
        page_area = page_w * page_h

        for emb_bytes in embedded_images:
            emb_img = Image.open(io.BytesIO(emb_bytes))
            emb_w, emb_h = emb_img.size
            emb_area = emb_w * emb_h

            # Check 1: Size-based coverage
            coverage = emb_area / page_area if page_area > 0 else 0
            if coverage >= coverage_threshold:
                logger.debug(
                    "Skipping page render: embedded covers %.1f%% of page",
                    coverage * 100
                )
                return False

            # Check 2: Perceptual hash similarity
            page_hash = imagehash.phash(page_img)
            emb_hash = imagehash.phash(emb_img)
            similarity = 1 - (page_hash - emb_hash) / 64

            if similarity >= similarity_threshold:
                logger.debug(
                    "Skipping page render: %.1f%% similar to embedded",
                    similarity * 100
                )
                return False

    except Exception as e:
        logger.warning("Page render comparison failed: %s", e)

    return True
```

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_image_classifier.py::test_skip_page_render_when_embedded_covers_content -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/deduplication_service.py backend/tests/test_image_classifier.py
git commit -m "$(cat <<'EOF'
fix: skip page renders when embedded image covers >70% of page

Enhances should_keep_page_render to check:
1. If embedded image area covers 70%+ of page area
2. If perceptual hash similarity exceeds 70%

Prevents duplicate extraction of images that are the primary content
of their page with only margins/decorations around them.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Consolidate Floor Plan Data with Images

**Files:**
- Modify: `backend/app/services/floor_plan_extractor.py` (FloorPlanData dataclass)
- Modify: `backend/app/services/output_organizer.py:198-201`
- Test: `backend/tests/test_floor_plan_extractor.py`

**Problem:** Floor plan JSON data is in `floor_plan_data.json` while images are in `/floor_plans/`. User must manually correlate.

**Solution:** Create per-floor-plan JSON files alongside images, OR add image filename reference to each floor plan entry in the consolidated JSON.

**Approach:** Both - each floor plan image gets a sidecar `.json` file AND the consolidated file includes image references.

**Step 1: Update FloorPlanData to include image filename**

Add to dataclass:

```python
@dataclass
class FloorPlanData:
    # ... existing fields ...
    image_filename: str = ""  # Reference to associated image file
```

**Step 2: Write the failing test**

```python
# backend/tests/test_output_organizer.py
def test_floor_plan_sidecar_json_files():
    """Verify each floor plan image has a sidecar JSON file."""
    organizer = OutputOrganizer()

    floor_plan_data = [
        {
            "image_filename": "floor_plan_001.webp",
            "unit_type": "2BR",
            "bedrooms": 2,
            "total_sqft": 1250,
        },
        {
            "image_filename": "floor_plan_002.webp",
            "unit_type": "3BR",
            "bedrooms": 3,
            "total_sqft": 1800,
        },
    ]

    mock_result = OptimizationResult(images=[])
    zip_bytes, _ = organizer.create_package(
        mock_result,
        project_name="test",
        floor_plan_data=floor_plan_data,
    )

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        # Consolidated file
        assert "floor_plans/floor_plan_data.json" in names
        # Sidecar files
        assert "floor_plans/floor_plan_001.json" in names
        assert "floor_plans/floor_plan_002.json" in names

        # Verify sidecar content
        sidecar = json.loads(zf.read("floor_plans/floor_plan_001.json"))
        assert sidecar["unit_type"] == "2BR"
        assert sidecar["image_filename"] == "floor_plan_001.webp"
```

**Step 3: Run test to verify it fails**

Run: `pytest backend/tests/test_output_organizer.py::test_floor_plan_sidecar_json_files -v`
Expected: FAIL - sidecar files don't exist

**Step 4: Update output_organizer to create sidecar files**

Replace lines 198-201:

```python
# Add floor plan structured data if available
if floor_plan_data:
    # Consolidated JSON
    fp_json = json.dumps(floor_plan_data, indent=2, default=str)
    zf.writestr("floor_plans/floor_plan_data.json", fp_json)

    # Per-floor-plan sidecar JSON files
    for fp_entry in floor_plan_data:
        if "image_filename" in fp_entry:
            # Extract base name without extension
            img_name = fp_entry["image_filename"]
            base_name = img_name.rsplit(".", 1)[0] if "." in img_name else img_name
            sidecar_path = f"floor_plans/{base_name}.json"
            sidecar_json = json.dumps(fp_entry, indent=2, default=str)
            zf.writestr(sidecar_path, sidecar_json)
```

**Step 5: Update FloorPlanExtractor to set image_filename**

In `floor_plan_extractor.py`, after line 151:

```python
# Set image filename for correlation
vision_data.image_filename = f"floor_plan_{idx + 1:03d}"
```

**Step 6: Run test to verify it passes**

Run: `pytest backend/tests/test_output_organizer.py::test_floor_plan_sidecar_json_files -v`
Expected: PASS

**Step 7: Commit**

```bash
git add backend/app/services/output_organizer.py backend/app/services/floor_plan_extractor.py backend/tests/test_output_organizer.py
git commit -m "$(cat <<'EOF'
feat: create sidecar JSON files for each floor plan image

Each floor plan image now has a corresponding .json file with extracted
data (unit_type, bedrooms, sqft, etc.) in the same directory.

Consolidated floor_plan_data.json retained for bulk processing.
Each entry now includes image_filename for correlation.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Remove or Repurpose Empty Drive Folders

**Files:**
- Modify: `backend/app/integrations/drive_client.py:737-802`
- Test: `backend/tests/test_drive_client.py`

**Problem:** Source and Images folders are created but never populated.

**Options:**
1. Remove them (simplest)
2. Use Source for original PDF, Images for unzipped organized images

**Decision:** Option 2 - populate them:
- `Source/` - Upload original PDF brochure
- `Images/` - Upload organized images (unzipped, same structure as ZIP)
- `Output/` - Upload the ZIP file

**Step 1: Write the failing test**

```python
# backend/tests/test_drive_client.py
@pytest.mark.asyncio
async def test_upload_to_project_structure():
    """Verify files are uploaded to correct project subfolders."""
    client = DriveClient()
    mock_service = AsyncMock()
    client.service = mock_service

    # Test uploading PDF to Source folder
    await client.upload_to_folder(
        file_bytes=b"PDF content",
        filename="brochure.pdf",
        folder_type="source",
        project_folder_id="project123"
    )

    # Verify upload was called with correct parent
    mock_service.files().create.assert_called()
    call_args = mock_service.files().create.call_args
    assert call_args[1]["body"]["parents"][0] == "source_folder_id"
```

**Step 2: Add upload helper method to DriveClient**

```python
async def upload_to_project(
    self,
    project_structure: dict[str, str],
    source_pdf: Optional[bytes] = None,
    source_filename: str = "brochure.pdf",
    output_zip: Optional[bytes] = None,
    output_filename: str = "output.zip",
    organized_images: Optional[list[tuple[str, bytes]]] = None,
) -> dict[str, str]:
    """
    Upload files to project folder structure.

    Args:
        project_structure: Dict from create_project_structure with folder IDs
        source_pdf: Original PDF bytes for Source folder
        output_zip: ZIP file bytes for Output folder
        organized_images: List of (path, bytes) for Images folder

    Returns:
        Dict of uploaded file IDs: {"source_pdf": id, "output_zip": id, ...}
    """
    uploaded = {}

    if source_pdf:
        file_id = await self.upload_file(
            source_pdf,
            source_filename,
            parent_id=project_structure["source"],
            mime_type="application/pdf"
        )
        uploaded["source_pdf"] = file_id

    if output_zip:
        file_id = await self.upload_file(
            output_zip,
            output_filename,
            parent_id=project_structure["output"],
            mime_type="application/zip"
        )
        uploaded["output_zip"] = file_id

    if organized_images:
        images_folder_id = project_structure["images"]
        for path, img_bytes in organized_images:
            # Create subfolders as needed (e.g., "interiors/img.webp")
            parts = path.split("/")
            parent = images_folder_id
            for folder in parts[:-1]:
                parent = await self.get_folder_by_path(
                    folder, parent, create_if_missing=True
                )

            filename = parts[-1]
            await self.upload_file(
                img_bytes, filename, parent_id=parent
            )

    return uploaded
```

**Step 3: Commit**

```bash
git add backend/app/integrations/drive_client.py backend/tests/test_drive_client.py
git commit -m "$(cat <<'EOF'
feat: add upload_to_project method for Drive folder population

Populates previously empty folders:
- Source/ receives original PDF brochure
- Images/ receives organized images (unzipped structure)
- Output/ receives the ZIP file

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Integration Testing

**Files:**
- Create: `backend/tests/test_pipeline_integration.py`

**Step 1: Write end-to-end test**

```python
# backend/tests/test_pipeline_integration.py
"""
Integration tests for the full extraction pipeline.
Tests the complete flow from PDF input to organized output.
"""
import io
import json
import zipfile

import pytest
from PIL import Image

from app.services.pdf_processor import PDFProcessor
from app.services.image_classifier import ImageClassifier
from app.services.image_optimizer import ImageOptimizer
from app.services.output_organizer import OutputOrganizer
from app.services.floor_plan_extractor import FloorPlanExtractor


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pipeline_output_structure(sample_pdf_with_images):
    """Verify complete pipeline produces expected output structure."""
    # Stage 1: Extract
    processor = PDFProcessor()
    extraction = await processor.extract_all(sample_pdf_with_images)

    assert extraction.page_text_map, "Text extraction should produce page_text_map"

    # Stage 2: Classify
    classifier = ImageClassifier()
    classification = await classifier.classify_extraction(extraction)

    # Stage 3: Optimize with semantic naming
    optimizer = ImageOptimizer()
    images_for_optimization = [
        (img.image_bytes, result.category.value, result.alt_text)
        for img, result in classification.classified_images
    ]
    optimization = await optimizer.optimize_batch(images_for_optimization)

    # Verify semantic filenames
    for img in optimization.images:
        assert img.file_name.startswith(f"{img.file_name[:3]}-{img.category}")

    # Stage 4: Package
    organizer = OutputOrganizer()
    zip_bytes, manifest = organizer.create_package(
        optimization,
        project_name="integration_test",
        page_text_map=extraction.page_text_map,
    )

    # Verify output structure
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()

        # Required files
        assert "manifest.json" in names
        assert "extracted_text.json" in names

        # Folder structure
        has_original = any(n.startswith("original/") for n in names)
        has_optimized = any(n.startswith("optimized/") for n in names)
        assert has_original, "Should have /original/ folder"
        assert has_optimized, "Should have /optimized/ folder"

        # No old structure
        has_llm = any(n.startswith("llm/") for n in names)
        assert not has_llm, "Should not have old /llm/ folder"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_floor_plan_consolidation(sample_pdf_with_floor_plans):
    """Verify floor plan images have sidecar JSON files."""
    processor = PDFProcessor()
    extraction = await processor.extract_all(sample_pdf_with_floor_plans)

    classifier = ImageClassifier()
    classification = await classifier.classify_extraction(extraction)

    # Get floor plan images
    floor_plan_images = [
        img for img, result in classification.classified_images
        if result.category.value == "floor_plan"
    ]

    if not floor_plan_images:
        pytest.skip("No floor plans in sample PDF")

    extractor = FloorPlanExtractor()
    fp_result = await extractor.extract_floor_plans(
        floor_plan_images,
        extraction.page_text_map
    )

    # Convert to dict for output
    floor_plan_data = [
        {
            "image_filename": f"floor_plan_{i+1:03d}.webp",
            "unit_type": fp.unit_type,
            "bedrooms": fp.bedrooms,
            "total_sqft": fp.total_sqft,
        }
        for i, fp in enumerate(fp_result.floor_plans)
    ]

    # Optimize and package
    optimizer = ImageOptimizer()
    optimization = await optimizer.optimize_batch([
        (img.image_bytes, "floor_plan", "")
        for img in floor_plan_images
    ])

    organizer = OutputOrganizer()
    zip_bytes, _ = organizer.create_package(
        optimization,
        floor_plan_data=floor_plan_data,
    )

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()

        # Consolidated file
        assert "floor_plans/floor_plan_data.json" in names

        # Sidecar files for each floor plan
        for i in range(len(floor_plan_data)):
            sidecar = f"floor_plans/floor_plan_{i+1:03d}.json"
            assert sidecar in names, f"Missing sidecar: {sidecar}"
```

**Step 2: Run integration tests**

Run: `pytest backend/tests/test_pipeline_integration.py -v -m integration`
Expected: All PASS

**Step 3: Commit**

```bash
git add backend/tests/test_pipeline_integration.py
git commit -m "$(cat <<'EOF'
test: add integration tests for pipeline output structure

Verifies:
- Semantic filenames in optimizer output
- Original/optimized folder separation
- extracted_text.json inclusion
- Floor plan sidecar JSON files

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Summary

| Task | Description | Files Modified |
|------|-------------|----------------|
| 1 | Save extracted text JSON | output_organizer.py |
| 2 | Separate original/optimized folders | output_organizer.py |
| 3 | Semantic image naming | image_optimizer.py |
| 4 | Fix logo false positives | image_classifier.py |
| 5 | Fix full-page extraction bug | deduplication_service.py |
| 6 | Floor plan sidecar JSONs | output_organizer.py, floor_plan_extractor.py |
| 7 | Populate Drive folders | drive_client.py |
| 8 | Integration tests | test_pipeline_integration.py |

**Estimated test count:** 12 new tests

---

Plan complete and saved to `docs/plans/2026-02-03-phase4-optimization-plan.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
