# PDP Pipeline Optimization — Implementation Plan

**Baseline metrics:** ~$0.92/PDF · 2–7 min processing · 50–100 MB/job

---

## Phase 1: Quick Wins (<1 day each, no architecture changes)

### 1.1 Drop DPI from 300 to 200

- **What:** Reduce PyMuPDF render DPI from 300 to 200 for page rasters
- **Why:** 40–55% memory reduction per page render (~25 MB → ~11 MB buffers). Tier 1 target (2450px) only needs 288 DPI on 8.5" pages; Tier 2 (1568px) only needs 185 DPI. Rendering higher then downscaling wastes memory and CPU.
- **Where:** `backend/app/utils/pdf_helpers.py` (line 24, `RENDER_DPI`), `backend/app/services/pdf_processor.py`
- **How:**
  - Change `RENDER_DPI = 300` → `RENDER_DPI = 200`
  - Add `alpha=False` to `page.get_pixmap()` calls if not already set
  - Add `pymupdf.TOOLS.store_shrink(100)` after processing all pages to clear PyMuPDF's internal cache
  - Validate output quality on 5 sample brochures — difference is imperceptible for screen display
- **Dependencies:** None
- **Risk:** Low — revert is a one-line change. No visible quality loss above 200 DPI for photographs.

### 1.2 Drop dual-format output (WebP-only)

- **What:** Stop generating JPG alongside WebP for every image
- **Why:** Eliminates 50% of encoding operations. WebP has 95.29% global browser support in 2025. JPG fallback only needed for Outlook email embeds (not this pipeline's use case).
- **Where:** `backend/app/services/image_optimizer.py` (lines ~126+, `optimize_batch`)
- **How:**
  - Remove JPG encoding path from `optimize_batch()`
  - Keep JPG capability behind a flag (`include_jpg=False` default) for future email use
  - Update `backend/app/services/output_organizer.py` to expect `.webp` only
  - Update manifest.json generation
- **Dependencies:** None
- **Risk:** Low — if a downstream consumer needs JPG, re-enable the flag. Check if Google Sheets or Drive preview has WebP issues.

### 1.3 Increase Drive upload concurrency from 5 to 10

- **What:** Raise the upload semaphore from 5 to 10–12 concurrent uploads
- **Why:** Google Drive allows 12,000 queries/60s. At 5 concurrent uploads of 3–5s each, you're using ~1–2 req/s. 30–40% upload time reduction expected.
- **Where:** `backend/app/integrations/drive_client.py`
- **How:**
  - Change semaphore from `asyncio.Semaphore(5)` to `asyncio.Semaphore(10)`
  - Monitor for 429s in staging — if none, you could push to 12
- **Dependencies:** None
- **Risk:** Low — revert is one number. Google's rate limits are generous.

### 1.4 Fix chunked upload penalty

- **What:** Use `chunksize=-1` for Drive resumable uploads to avoid the 9× slowdown from chunked uploads
- **Why:** Google's resumable chunked uploads are benchmarked at 20 Mbps vs 180 Mbps with single-chunk. 20–30% upload time improvement.
- **Where:** `backend/app/integrations/drive_client.py`
- **How:**
  - For files ≤5 MB: use `MediaFileUpload(path, resumable=False)` (simple upload)
  - For files >5 MB: use `MediaFileUpload(path, chunksize=-1, resumable=True)` (resumable, single-chunk)
  - Batch folder creation using Drive batch API (up to 100 folders per batch) before file uploads
- **Dependencies:** None
- **Risk:** Low — single-chunk resumable still supports resume on failure.

### 1.5 Remove 0.5s inter-field delay in content generation

- **What:** Remove the artificial `asyncio.sleep(0.5)` delay between content generation API calls
- **Why:** Saves 4.5s of pure wait time (9 delays × 0.5s). Rate limiting should be handled by retry logic, not pre-emptive delays.
- **Where:** `backend/app/services/content_generator.py` (line ~58, `generate_all`)
- **How:**
  - Remove `await asyncio.sleep(0.5)` between field generation calls
  - Ensure existing retry logic with `retry_after` header handling is solid (it already is per the report)
- **Dependencies:** None
- **Risk:** Low — if you hit rate limits, the existing 3-retry with backoff handles it.

### 1.6 Reduce LLM-tier WebP quality from 85 to 80

- **What:** Lower WebP quality for Tier 2 (LLM input) images
- **Why:** ML models don't need perceptually perfect images. Saves ~10–15% file size per image, reducing upload time and storage.
- **Where:** `backend/app/services/image_optimizer.py`
- **How:**
  - Add separate quality constant: `LLM_WEBP_QUALITY = 80`
  - Apply only to Tier 2 encoding path
- **Dependencies:** None
- **Risk:** Low — no impact on user-facing images.

### Phase 1 Cumulative Impact

| Metric | Before | After Phase 1 |
|--------|--------|---------------|
| Cost/PDF | ~$0.92 | ~$0.92 (no API changes yet) |
| Processing time | 2–7 min | ~1.5–5.5 min (−20–25%) |
| Memory/job | 50–100 MB | 30–60 MB (−40%) |

---

## Phase 2: Medium Effort (1–3 days each)

### 2.1 Batch image classification (2–3 days)

- **What:** Send 8–10 images per Claude Vision call using native multi-image content blocks instead of one call per image
- **Why:** Reduces API calls from 50+ to 6–7. Classification latency drops from 30–120s to 5–15s. ~35% cost reduction on classification ($0.23 → ~$0.10).
- **Where:** `backend/app/services/image_classifier.py` (lines 149+, `classify_extraction`; lines 282–345, per-image Vision call)
- **How:**
  - Group images into batches of 8–10 (resize to ≤1500px before batching to stay under 2000px multi-image limit)
  - Build multi-image content blocks with indexed text prompt: "Classify each of the N images by index..."
  - Use Anthropic structured outputs beta (`anthropic-beta: structured-outputs-2025-11-13`) with a Pydantic `BatchResult` schema for guaranteed-valid JSON
  - Preserve existing pHash deduplication — run dedup *before* batching to reduce call volume further
  - Keep single-image fallback for batches that fail parsing
- **Dependencies:** None
- **Risk:** Medium — accuracy may dip slightly above batch size 10. Test on 20 sample PDFs and compare to individual classification results. Keep batch size ≤10.

### 2.2 Concurrent API calls with semaphore (1 day)

- **What:** Run classification batches concurrently instead of sequentially
- **Why:** Even with batching, 6–7 calls sequentially still takes 10–15s. With 5–10 concurrent calls, drops to 3–5s.
- **Where:** `backend/app/services/image_classifier.py`, `backend/app/integrations/anthropic_client.py`
- **How:**
  - Add `asyncio.Semaphore(10)` for Anthropic calls (safe at Tier 2: 1,000 RPM)
  - Add `aiolimiter.AsyncLimiter` at 80% of RPM quota as safety margin
  - Use `asyncio.gather(*tasks, return_exceptions=True)` for parallel execution
  - Read `anthropic-ratelimit-requests-remaining` header and throttle proactively
  - Apply same pattern to content generation if not consolidated (see 2.3)
- **Dependencies:** 2.1 (batch classification) — concurrency is most effective when combined with batching
- **Risk:** Low — semaphore prevents overload. Existing retry logic handles 429s.

### 2.3 Consolidated content generation (1–2 days)

- **What:** Replace 10 sequential API calls (one per content field) with a single structured output call
- **Why:** 69% token reduction (12,500 → 3,900 tokens), 50% cost reduction ($0.08 → $0.04), latency from 30–60s to 5–8s.
- **Where:** `backend/app/services/content_generator.py` (line 58, `generate_all`)
- **How:**
  - Define a Pydantic `PropertyListing` model with all 10 fields (title, headline, description, features, neighborhood, seo_title, meta_description, keywords, target_buyer, call_to_action) with character limits as `Field(max_length=...)` constraints
  - Use `client.beta.messages.parse()` with `output_format=PropertyListing` for guaranteed-valid JSON
  - Send system prompt once (currently repeated 10x = ~7,500 wasted input tokens)
  - Keep a 2-call refinement fallback for premium listings if quality assessment fails
  - Update `_step_generate_content` in `backend/app/services/job_manager.py` (line 1075) to use single-call path
- **Dependencies:** None
- **Risk:** Medium — test output quality against current multi-call output for 20 sample properties. If quality degrades on specific fields, consider a 2-call split (metadata fields + creative fields).

### 2.4 Switch from Pillow to pyvips (2 days)

- **What:** Replace PIL/Pillow with pyvips for image resizing and encoding
- **Why:** 5× faster encoding, 4× less memory (1040 MB → 109 MB for batch operations). Combined with WebP-only (1.2), total image processing improvement is ~80%.
- **Where:** `backend/app/services/image_optimizer.py` (line 126, `optimize_batch`)
- **How:**
  - Install `pyvips` (requires libvips system dependency — add to Dockerfile)
  - Replace PIL resize + encode with pyvips equivalents: `pyvips.Image.new_from_buffer()` → `.resize()` → `.webpsave_buffer(Q=85)`
  - pyvips is thread-safe and GIL-releasing — use `ThreadPoolExecutor` for parallel encoding within async pipeline
  - Handle CMYK → RGB conversion in pyvips: `.colourspace('srgb')`
  - Keep Pillow as fallback import for edge cases (palette images, etc.)
- **Dependencies:** 1.2 (WebP-only) should be done first so you only implement one format in pyvips
- **Risk:** Medium — pyvips has a different API surface and requires system library. Test color space handling carefully. Add to Dockerfile/Cloud Run build.

### Phase 2 Cumulative Impact

| Metric | After Phase 1 | After Phase 2 |
|--------|---------------|---------------|
| Cost/PDF | ~$0.92 | ~$0.46 (−50%) |
| Processing time | 1.5–5.5 min | 0.8–3 min (−45%) |
| Memory/job | 30–60 MB | 20–40 MB (−30%) |

---

## Phase 3: Architecture Changes (3–7 days each)

### 3.1 Hybrid OCR integration (5–7 days)

- **What:** Replace Claude Vision OCR fallback with a 3-tier OCR strategy: PaddleOCR (free) → Google Document AI ($0.0015/page) → Claude Vision (last resort)
- **Why:** The single biggest cost driver: $0.60/PDF when OCR triggers. Hybrid approach reduces to $0.03–0.06/PDF (90–95% reduction).
- **Where:** `backend/app/services/pdf_processor.py` (line 40, `MIN_CHARS_PER_PAGE` trigger; OCR fallback logic), new file `backend/app/services/ocr_service.py`
- **How:**
  - Create `OCRService` class with 3-tier dispatch
  - **Tier 1 — PaddleOCR:** Install `paddleocr` with Arabic language support (`lang='ar'`). Run on all pages where PyMuPDF yields <100 chars. If confidence >0.75 and output >100 chars, accept.
  - **Tier 2 — Google Document AI:** For pages where PaddleOCR confidence is 0.5–0.75, call Document AI ($0.0015/page). Already in Google Cloud ecosystem.
  - **Tier 3 — Claude Vision:** Only for pages with confidence <0.5 from both preceding tiers (~10% of pages)
  - Add PaddleOCR to Dockerfile (significant: ~500 MB with models). Consider running PaddleOCR in a separate Cloud Run service to avoid bloating main image.
  - **Important:** Amazon Textract does NOT support Arabic — exclude entirely.
- **Dependencies:** None, but consider 3.3 (parallel pipeline split) to determine where OCR step lives
- **Risk:** High — PaddleOCR adds significant container size. Arabic/English mixed-language accuracy needs validation on 20+ sample brochures. Document AI requires API enablement and billing. Consider starting with just PaddleOCR + Claude Vision (skip Document AI) to reduce integration complexity.

### 3.2 Streaming pipeline with GCS-backed context (5–7 days)

- **What:** Replace in-memory `_pipeline_ctx` dict with GCS-backed lazy loading and process images one-at-a-time through classify → optimize → upload instead of holding all in memory
- **Why:** Decouples memory from job count. Reduces per-job footprint from 20–40 MB (post Phase 1–2) to 5–10 MB, enabling 3–4× more concurrent jobs per Cloud Run instance.
- **Where:** `backend/app/services/job_manager.py` (pipeline context management throughout), `backend/app/services/storage_service.py`
- **How:**
  - Replace `_pipeline_ctx[job_id]["pdf_bytes"]` and `["zip_bytes"]` with GCS refs: `gs://bucket/temp/{job_id}/input.pdf` — saves 10–30 MB per job
  - Use `gcloud-aio-storage` (NOT the official `google-cloud-storage` library, which blocks the event loop) for true async GCS operations
  - Implement streaming image processing: `async for image in extract_images_streaming()` → classify → optimize → upload → GC immediately
  - Use `asyncio.Queue(maxsize=2)` for backpressure between extraction and classification
  - Store only metadata + current image in memory, not all images
  - Add GCS temp cleanup in `_step_finalize` (or a TTL policy on the temp bucket prefix)
  - Latency tradeoff: adds ~20–50ms per GCS read, but eliminates OOM risk
- **Dependencies:** 2.4 (pyvips) helps since it uses less memory per image operation
- **Risk:** High — fundamental change to data flow. Every step that reads from `_pipeline_ctx` needs updating. Requires thorough testing of all 14 steps. Implement behind a feature flag.

### 3.3 Parallel pipeline split: image pipe + text pipe (5–7 days)

- **What:** After extraction (steps 1–2), fork into two independent parallel pipelines — an image pipeline and a text pipeline — that run concurrently as separate Cloud Tasks, converging at upload/finalize
- **Why:** The two biggest latency bottlenecks — classification (30–120s) and content generation (30–60s) — currently run back-to-back but have zero data dependency on each other. Running them in parallel means total time equals the *longer* branch, not the *sum*. The text pipe (47–105s) runs entirely within the image pipe's duration (95–245s), so you get content generation for free. This is a much larger time savings than the old 14→7 consolidation approach (which only saved ~3.5s of dispatch overhead).
- **Where:** `backend/app/services/job_manager.py` (pipeline orchestration, `execute_processing_pipeline`), `backend/app/background/task_queue.py` (dispatch logic), `backend/app/models/database.py` (Job model — new convergence fields)

- **Architecture:**
  ```
  SHARED: Upload + Extract (steps 1–2)
               |
        extracted text + images available
               |
       +-------+-------+
       |               |
   IMAGE PIPE       TEXT PIPE
   (Cloud Task A)   (Cloud Task B)
       |               |
   3. classify      9. extract_data
   4. watermark     10. structure_data
      detect        11. generate_content
   5. watermark     12. populate_sheet
      remove            |
   6. floor plans       |
   7. optimize          |
   8. package           |
       |               |
       +-------+-------+
               |
        CONVERGENCE
   13. upload_cloud
   14. finalize
  ```

- **How:**
  - After step 2 completes, dispatch two Cloud Tasks simultaneously instead of proceeding to step 3
  - **Task A (image pipe):** Receives `extraction.images` + `extraction.text` (text needed for floor plan context in step 6). Runs steps 3–8 sequentially within the task
  - **Task B (text pipe):** Receives `extraction.text` + page renders (for structure_data fallback). Runs steps 9–12 sequentially within the task
  - **Convergence mechanism (needs investigation — see options below):** When both tasks complete, dispatch the final upload + finalize task
  - Each branch writes its output to GCS (or the pipeline context store) independently
  - Upload step reads from both branches' outputs to build the final Drive folder structure

- **Convergence options to investigate:**
  1. **Atomic counter on Job record:** Add `parallel_branches_completed INT DEFAULT 0` to the Job model. Each branch atomically increments on completion (`UPDATE jobs SET parallel_branches_completed = parallel_branches_completed + 1 WHERE id = ? RETURNING parallel_branches_completed`). The branch that gets back `2` dispatches the convergence task. Simple, no new infrastructure. **Risk:** Requires true atomic DB increment — test under concurrent writes.
  2. **Completion flags with polling:** Each branch sets a flag (`image_pipe_done`, `text_pipe_done`) on the Job record. The finalize step is dispatched by whichever branch finishes second (check if the other flag is already set). Slightly more explicit than a counter. **Risk:** Race condition if both complete at the exact same millisecond — mitigate with a DB transaction or `SELECT FOR UPDATE`.
  3. **Cloud Tasks callback pattern:** Each branch dispatches a "branch-complete" task to a convergence queue. A convergence handler checks if all branches are done before proceeding. Adds a queue but keeps logic out of the processing tasks. **Risk:** Extra dispatch latency (~300ms).
  4. **Firestore/GCS marker files:** Each branch writes a marker file (e.g., `gs://bucket/temp/{job_id}/image_pipe_done`). The convergence check lists marker files. No DB changes needed. **Risk:** GCS eventual consistency (though strong consistency is default now for object creation).

- **Data dependencies to handle:**
  - Step 10 (`structure_data`) has a fallback using image `alt_text` when PDF text is empty. This only triggers on text-poor PDFs. **Mitigation:** Pass extracted text to text pipe at fork. If text is empty, text pipe can either (a) wait for classification to finish and read alt_texts from shared storage, or (b) proceed without alt_texts and let structure_data use Claude to infer from page renders. Option (b) is simpler and the fallback is rare.
  - Step 6 (`extract_floor_plans`) uses page text context. **Mitigation:** Text is already available from extraction — pass it at fork. No dependency on the text pipe.
  - Step 8 (`package_assets`) creates the ZIP. If streaming (3.2) is implemented, packaging can happen incrementally or be deferred to the convergence step.

- **Progress tracking changes:**
  - Current: linear 0–100% across 14 steps
  - New: two parallel progress bars, or a weighted combined progress where image pipe = 60% weight, text pipe = 40% weight
  - Each branch reports progress independently via `job.progress_message`
  - UI option: show "Processing images... (step 4/6)" and "Generating content... (step 2/4)" simultaneously

- **Error handling:**
  - If either branch fails, mark the Job as FAILED immediately — don't wait for the other branch
  - The still-running branch should check Job status periodically (or on each step transition) and abort if the Job is already FAILED
  - Retry granularity stays the same as current — each sub-step within a branch retries independently

- **Dependencies:** 3.2 (GCS-backed context) makes this cleaner since both branches write to GCS rather than sharing in-memory state. Can be implemented without 3.2 but shared `_pipeline_ctx` dict gets messy with concurrent writers.
- **Risk:** High — the convergence mechanism is the critical design decision. The parallel execution itself is straightforward (two Cloud Tasks instead of one), but ensuring exactly-once convergence under all failure modes (one branch fails, both finish simultaneously, cold start delays) requires careful implementation. **Recommend:** Start with option 1 (atomic counter) as the simplest approach, load test with 20 concurrent PDFs, and upgrade to option 3 (task callback) only if race conditions appear.

### 3.4 Local pre-filtering before classification (3–4 days)

- **What:** Add a 3-stage local filter pipeline to classify obvious images without API calls: entropy filtering → Hough line detection (floor plans) → CLIP zero-shot
- **Why:** Eliminates 35–50% of remaining Claude Vision calls after batching. Reduces classification cost further from ~$0.10 to ~$0.05.
- **Where:** New file `backend/app/services/local_classifier.py`, integrated into `backend/app/services/image_classifier.py`
- **How:**
  - **Stage 1 — Entropy filter:** Images with entropy <3.5 bits → classify as "other" directly (~0.01s/image)
  - **Stage 2 — Hough line detection:** High line density + low color saturation → "floor_plan" at 90–95% accuracy (~0.05s/image)
  - **Stage 3 — CLIP ViT-B/32:** Zero-shot classification of remaining ambiguous images. Only send to Claude Vision if CLIP confidence <0.85 (~0.02–0.05s/image on GPU, ~15s on CPU)
  - Run local classifier on all images first → split into "confident local" and "needs API" buckets → only batch-send the "needs API" bucket
  - CLIP model adds ~400 MB to container image — consider running on GPU-enabled Cloud Run or as separate service
- **Dependencies:** 2.1 (batch classification) — local filtering reduces the number of images sent to batch classification
- **Risk:** Medium — CLIP on CPU is too slow for production (15s for 50 images). Without GPU, skip CLIP and use only entropy + Hough (still eliminates 15–25% of calls). Model download on cold start adds latency.

### Phase 3 Cumulative Impact

| Metric | After Phase 2 | After Phase 3 |
|--------|---------------|---------------|
| Cost/PDF | ~$0.46 | ~$0.12–0.18 (−75–85% from baseline) |
| Processing time | 0.8–3 min | 0.5–1.5 min (−70–80% from baseline) |
| Memory/job | 20–40 MB | 5–10 MB (−90% from baseline) |

---

## Conflict Resolution

### DPI target: Doc 3 says 250, math says 200
Doc 3 recommends 200–250 DPI. For Tier 1 (2450px on 8.5" = 288 DPI), rendering at 200 then *not downscaling* means your rasters max out at ~1700px wide — below Tier 1 target. **Resolution:** Render at 250 DPI for pages where Tier 1 output is needed (gives 2125px — close enough with LANCZOS upscale to 2450). Render at 200 DPI for Tier 2 only pages. Or simpler: just use 250 DPI globally as a safe middle ground. The memory savings (30% vs 40–55%) are still substantial.

### CLIP on Cloud Run: feasible or not?
Doc 2 recommends CLIP for local pre-filtering. Doc 3 highlights Cloud Run memory constraints (512 MB–2 GB). CLIP ViT-B/32 requires ~400 MB RAM + model file. **Resolution:** Skip CLIP for Phase 3 MVP. Use only entropy + Hough line detection (zero model downloads, <1s total). Add CLIP later if running on GPU-enabled Cloud Run or as a separate microservice.

### Redis for context storage vs GCS
Doc 3 recommends Memorystore Redis for sub-millisecond context storage between steps. Doc 3 also recommends GCS for large binaries. **Resolution:** Use GCS for everything. Redis adds infrastructure complexity (provisioning, VPC connector, cost) for marginal latency gain. GCS same-region reads at 10–50ms are acceptable when you're saving 50+ MB of RAM per job. If processing volume exceeds 1000 PDFs/day, revisit Redis.

### Single Cloud Run Job vs Cloud Tasks
Doc 3 suggests Cloud Run Jobs for the entire pipeline (168h timeout, one cold start). **Resolution:** Stay with Cloud Tasks for now. Cloud Tasks give you per-step retry, progress tracking, and the ability to scale different steps independently. Cloud Run Jobs would require implementing your own checkpointing. Revisit at >100K executions/month.

### Grid composites vs native multi-image
Doc 2 explicitly advises against grid composites (accuracy degradation from compression). **Resolution:** Use native multi-image content blocks only. This is a clear win — no accuracy tradeoff.

---

## Deprioritized

| Recommendation | Source | Reason to skip |
|----------------|--------|----------------|
| AVIF encoding | Both | 10–100× slower encode than WebP for marginal 20–30% size reduction. Let CDN handle AVIF on-demand if needed. |
| GCS-to-Drive server-side transfer | Doc 3 | Doesn't actually exist — the Airflow operator just downloads and re-uploads. |
| ZIP upload + Apps Script extraction on Drive | Doc 3 | 6-min timeout, 50 MB limit, adds processing time. Current approach is better. |
| Memory-mapped files for PDF bytes | Doc 3 | GCS-backed lazy loading (3.2) is simpler and more effective for Cloud Run. |
| Responsive images (srcset with multiple sizes) | Doc 2 | Over-engineered for current use case. Two fixed tiers are sufficient. |
| Amazon Textract | Doc 2 | Does not support Arabic — disqualified for UAE market. |
| ProcessPoolExecutor for PyMuPDF | Doc 3 | Adds complexity and PyMuPDF has GIL issues with threading. Sequential extraction at 200 DPI is fast enough (5–15s). Revisit only if extraction becomes the bottleneck after other optimizations. |
| Smart cropping to standard aspect ratios | Doc 2 | Nice-to-have but not a pipeline bottleneck. Defer to frontend. |
| Pre-generating XLSX instead of Sheets API | Doc 2 | Sheets API is already fast enough (5–10s). XLSX approach loses real-time collaboration features. |

---

## Implementation Checklist

```
PHASE 1 (Week 1 — all quick wins)
[ ] 1.1  Change RENDER_DPI 300→200 in pdf_helpers.py, add store_shrink()
[ ] 1.2  Remove JPG encoding in image_optimizer.py, update output_organizer.py
[ ] 1.3  Semaphore 5→10 in drive_client.py
[ ] 1.4  chunksize=-1 in drive_client.py, batch folder creation
[ ] 1.5  Remove sleep(0.5) in content_generator.py
[ ] 1.6  LLM tier WebP quality 85→80 in image_optimizer.py

PHASE 2 (Weeks 2–3)
[ ] 2.1  Batch classification in image_classifier.py (8–10 images/call)
[ ] 2.2  Async semaphore + rate limiter in anthropic_client.py
[ ] 2.3  Single-call content gen with Pydantic schema in content_generator.py
[ ] 2.4  Replace Pillow with pyvips in image_optimizer.py + Dockerfile

PHASE 3 (Weeks 4–6)
[ ] 3.1  Hybrid OCR service (PaddleOCR + Document AI + Claude fallback)
[ ] 3.2  GCS-backed context + streaming image pipeline in job_manager.py
[ ] 3.3  Parallel pipeline split (image pipe + text pipe) in job_manager.py + task_queue.py
         [ ] 3.3a  Design convergence mechanism (start with atomic counter)
         [ ] 3.3b  Implement fork after extraction — dispatch two Cloud Tasks
         [ ] 3.3c  Implement image pipe (steps 3–8 in single task)
         [ ] 3.3d  Implement text pipe (steps 9–12 in single task)
         [ ] 3.3e  Implement convergence handler + upload/finalize
         [ ] 3.3f  Update progress tracking for parallel branches
         [ ] 3.3g  Load test with 20 concurrent PDFs
[ ] 3.4  Local pre-filtering (entropy + Hough) in new local_classifier.py
```
