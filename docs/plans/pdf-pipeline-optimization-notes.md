# PDF Pipeline - Optimization Notes

Reference observations from initial pipeline analysis. These are not recommendations - just documented observations for investigation.

---

## 1. Classification Bottleneck

**Current State:** 50+ sequential Claude Vision calls (30-120s total)

**Observations:**
- Each image classified individually via separate API call
- No parallelization of API calls currently
- No pre-filtering before sending to API
- No caching mechanism for similar images across projects

---

## 2. Vision OCR Cost

**Current State:** ~$0.60 per PDF when triggered (40k tokens)

**Observations:**
- OCR runs on all pages when average chars/page < 100
- 4000 tokens allocated per page
- No selective OCR based on content regions
- PyMuPDF text extraction attempted first, Vision is fallback

---

## 3. Page Rendering Overhead

**Current State:** Full 300 DPI render of every page

**Observations:**
- All pages rendered regardless of embedded image coverage
- Same DPI used for classification and final output
- Text-only pages still get full renders
- Renders happen before classification decision

---

## 4. Deduplication Efficiency

**Current State:** Sequential perceptual hash comparison

**Observations:**
- pHash computed and compared sequentially
- 95% similarity threshold for all categories
- Cross-source dedup checks area coverage (>70%)
- No indexing structure for faster lookups

---

## 5. Memory Management

**Current State:** 50-100MB per job in pipeline context

**Observations:**
- All images held in memory throughout pipeline
- ZIP package built in memory before upload
- Cleanup only happens after full pipeline completion
- No streaming or lazy loading patterns

---

## 6. Content Generation

**Current State:** Sequential field generation with 0.5s delays

**Observations:**
- Each field generated via separate API call
- 0.5s inter-field delay for rate limiting
- 3 retries per field for character limit enforcement
- No batching of independent fields
