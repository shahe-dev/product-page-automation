# Agent Brief: DEV-IMGCLASS-001

**Agent ID:** DEV-IMGCLASS-001
**Agent Name:** Image Classifier Agent
**Type:** Development
**Phase:** 2 - Material Preparation
**Context Budget:** 60,000 tokens

---

## Mission

Implement Claude Sonnet 4.5 vision-based image classification with:
1. **Triple extraction input** - Classify embedded images, page renders, and have access to per-page text context
2. **LLM optimization** - Use Tier 2 images (1024px max) to reduce tokens
3. **Deduplication** - Identify and remove overlapping content across extraction sources
4. Category classification, confidence scoring, and SEO alt-text generation

---

## Documentation to Read

### Primary
1. `docs/02-modules/MATERIAL_PREPARATION.md` - Classification requirements
2. `docs/05-integrations/ANTHROPIC_API_INTEGRATION.md` - Claude API integration

---

## Dependencies

**Upstream:** DEV-PDF-001
**Downstream:** DEV-WATERMARK-001, DEV-FLOORPLAN-001

---

## Outputs

### `backend/app/services/image_classifier.py`

---

## Acceptance Criteria

### Input Processing
1. **Triple extraction input:** Receive embedded images, page renders, and per-page text from DEV-PDF-001
2. **Classify ALL sources:** Process every image from both extraction methods
3. **LLM optimization:** Use `LLMImageOptimizer` with `task="classification"` (1024px max)

### Classification
4. **Categories:** interior, exterior, amenity, logo, floor_plan, location_map, master_plan, other
5. **Confidence scores:** 0.0-1.0 per classification
6. **Reasoning:** Brief explanation for each classification

### Deduplication
7. **Cross-source deduplication:** Compare embedded vs page render using perceptual hash
8. **Similarity threshold:** 90% - if render is >90% similar to embedded, skip render
9. **Keep unique renders:** Page renders capturing vector content not in embedded

### Batch Processing
10. **Batch size:** 5-10 images per batch
11. **Token efficiency:** ~400 tokens per image (vs ~1200 at full resolution)

### Output
12. **SEO alt-text:** Generated for each retained image
13. **Category limits enforcement:**
    - Interior: max 10
    - Exterior: max 10
    - Amenity: max 5
    - Logo: max 3
    - Other: discarded

### Error Handling
14. **Graceful fallback:** Return "other" on API failure
15. **Retry logic:** 3 retries with exponential backoff

---

## Implementation Notes

### LLM Optimization Pattern
```python
from app.services.llm_image_optimizer import llm_optimizer

async def classify_image(original_bytes: bytes) -> ClassificationResult:
    # Optimize for classification (1024px max, JPEG 80%)
    optimized, meta = llm_optimizer.optimize_for_llm(original_bytes, "classification")
    logger.info(f"Token savings: {meta['reduction_percent']}%")

    # Send optimized image to Claude
    result = await claude_classify(optimized)
    return result
```

### Deduplication Pattern
```python
import imagehash
from PIL import Image

def should_keep_page_render(render: bytes, embedded_on_page: List[bytes]) -> bool:
    render_hash = imagehash.phash(Image.open(io.BytesIO(render)))

    for emb in embedded_on_page:
        emb_hash = imagehash.phash(Image.open(io.BytesIO(emb)))
        similarity = 1 - (render_hash - emb_hash) / 64

        if similarity > 0.90:
            return False  # Too similar, skip render

    return True  # Unique content, keep render
```

## Claude Sonnet 4.5 Prompt Template

```
Classify this real estate image into one category:
- interior: Indoor spaces (bedrooms, living rooms, kitchens, bathrooms)
- exterior: Building facade, outdoor views, balconies
- amenity: Pool, gym, playground, common areas
- floor_plan: Architectural floor plans or unit layouts
- logo: Developer or project logos
- location_map: Maps showing location or nearby landmarks
- master_plan: Site plan or development layout
- other: Text-only, decorative, or unclassifiable

Return JSON:
{
  "category": "interior",
  "confidence": 0.95,
  "reasoning": "Shows a modern living room with furniture",
  "alt_text": "Spacious living room with floor-to-ceiling windows overlooking Dubai Marina"
}
```

### Token Usage Estimate
| Image Type | Original | LLM-Optimized | Savings |
|------------|----------|---------------|---------|
| Classification | ~1200 tokens | ~400 tokens | 67% |

---

## QA Pair: QA-IMGCLASS-001

---

**Begin execution.**
