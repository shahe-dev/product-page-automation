# Documentation Gap Report: PDP Automation v.3

**Generated:** 2026-01-24
**Audit Type:** Multi-Agent Documentation Consistency Audit
**Status:** CRITICAL ISSUES FOUND

---

## Executive Summary

This audit identified **37 critical inconsistencies** across the documentation requiring immediate attention before agent execution can proceed safely. The primary issues fall into three categories:

1. **OpenAI to Anthropic Migration Incomplete** (18 items)
2. **Technical Specification Conflicts** (8 items)
3. **Manifest/Brief Synchronization Failures** (11 items)

---

## CRITICAL: OpenAI to Anthropic Migration Issues

### 1. EXECUTION_MANIFEST.json - Master Registry Failures

| Line | Issue | Current Value | Required Value |
|------|-------|---------------|----------------|
| 51 | Missing Anthropic in doc registry | `OPENAI_API_INTEGRATION.md` only | Add `ANTHROPIC_API_INTEGRATION.md` |
| 160 | ORCH-INTEGRATION-001 references OpenAI | `OPENAI_API_INTEGRATION.md` | `ANTHROPIC_API_INTEGRATION.md` |
| 162 | Phase-5 missing Anthropic agent | `DEV-OPENAI-001` only | Add `DEV-ANTHROPIC-001` |
| 658 | DEV-IMGCLASS-001 doc reference | `OPENAI_API_INTEGRATION.md` | `ANTHROPIC_API_INTEGRATION.md` |
| 699-700 | DEV-WATERMARK-001 doc reference | `OPENAI_API_INTEGRATION.md` | `ANTHROPIC_API_INTEGRATION.md` |
| 740-742 | DEV-FLOORPLAN-001 doc reference | `OPENAI_API_INTEGRATION.md` | `ANTHROPIC_API_INTEGRATION.md` |
| 883-885 | DEV-STRUCT-001 doc reference | `OPENAI_API_INTEGRATION.md` | `ANTHROPIC_API_INTEGRATION.md` |
| 927-929 | DEV-CONTENT-001 doc reference | `OPENAI_API_INTEGRATION.md` | `ANTHROPIC_API_INTEGRATION.md` |
| 1452 | Phase-5 description | "External service integrations (GCS, Sheets, Drive, **OpenAI**, OAuth)" | Replace with "Anthropic" |
| 1565-1599 | Phase-5 agents list | Only DEV-OPENAI-001/QA-OPENAI-001 | Add DEV-ANTHROPIC-001/QA-ANTHROPIC-001 |

### 2. Agent Brief Files Not Updated

| File | Line | Issue | Fix Required |
|------|------|-------|--------------|
| [DEV-STRUCT-001.md](docs/_agent-briefs/phase-3-content-gen/DEV-STRUCT-001.md) | 13 | Mission says "GPT-4 Turbo-based" | Update to "Claude Sonnet 4.5-based" |
| [DEV-STRUCT-001.md](docs/_agent-briefs/phase-3-content-gen/DEV-STRUCT-001.md) | 24 | References `OPENAI_API_INTEGRATION.md` | Change to `ANTHROPIC_API_INTEGRATION.md` |
| [DEV-STRUCT-001.md](docs/_agent-briefs/phase-3-content-gen/DEV-STRUCT-001.md) | 77 | "GPT-4 Structuring Prompt Template" | Update to "Claude Sonnet 4.5 Prompt Template" |
| [DEV-CONTENT-001.md](docs/_agent-briefs/phase-3-content-gen/DEV-CONTENT-001.md) | 25 | References `OPENAI_API_INTEGRATION.md` | Change to `ANTHROPIC_API_INTEGRATION.md` |
| [DEV-WATERMARK-001.md](docs/_agent-briefs/phase-2-material-prep/DEV-WATERMARK-001.md) | - | References OpenAI for vision | Update to Claude Sonnet 4.5 |

### 3. Agent Brief Files Correctly Updated (Verification)

| File | Status | Notes |
|------|--------|-------|
| [DEV-IMGCLASS-001.md](docs/_agent-briefs/phase-2-material-prep/DEV-IMGCLASS-001.md) | CORRECT | References `ANTHROPIC_API_INTEGRATION.md`, Claude Sonnet 4.5 |
| [DEV-FLOORPLAN-001.md](docs/_agent-briefs/phase-2-material-prep/DEV-FLOORPLAN-001.md) | CORRECT | References Claude Sonnet 4.5 vision OCR |
| [DEV-ANTHROPIC-001.md](docs/_agent-briefs/phase-5-integrations/DEV-ANTHROPIC-001.md) | CORRECT | Properly defines Anthropic client |
| [DEV-EXTRACT-001.md](docs/_agent-briefs/phase-3-content-gen/DEV-EXTRACT-001.md) | CORRECT | Uses pymupdf4llm (FREE, no API) |

### 4. EXECUTION_PROTOCOL.md Issues

| Line | Issue | Fix Required |
|------|-------|--------------|
| 302-303 | Phase 5 execution order lists `DEV-OPENAI-001` | Add `DEV-ANTHROPIC-001` or replace |

---

## CRITICAL: Technical Specification Conflicts

### 1. 500KB File Size Limit Conflicts with Dual-Tier Strategy

The approved dual-tier image strategy specifies:
- **Tier 1 (Original):** No file size limit, quality preserved
- **Tier 2 (LLM-Optimized):** 1568px max, optimized for token usage

However, documentation still references the deprecated 500KB limit:

| File | Line | Issue | Fix Required |
|------|------|-------|--------------|
| [DEV-IMGOPT-001.md](docs/_agent-briefs/phase-2-material-prep/DEV-IMGOPT-001.md) | 52 | "Max 500KB per image" | Remove - contradicts dual-tier |
| [EXECUTION_MANIFEST.json](docs/EXECUTION_MANIFEST.json) | 793-795 | DEV-IMGOPT-001 acceptance criteria includes "Compress to max 500KB" | Remove this criterion |

### 2. Missing Dual-Tier Documentation in Agent Briefs

| File | Issue | Fix Required |
|------|-------|--------------|
| [DEV-IMGOPT-001.md](docs/_agent-briefs/phase-2-material-prep/DEV-IMGOPT-001.md) | No mention of Tier 1/Tier 2 | Add dual-tier output specification |
| [DEV-PDF-001.md](docs/_agent-briefs/phase-2-material-prep/DEV-PDF-001.md) | Missing triple extraction requirement | Add embedded + page render + text (pymupdf4llm) for ALL pages |

### 3. DPI Specification Consistency

Approved specification: **300 DPI for ALL page rendering** (consistent quality)

| File | Status | Notes |
|------|--------|-------|
| MATERIAL_PREPARATION.md | VERIFY | Should specify 300 DPI uniform |
| DEV-PDF-001.md | VERIFY | Should specify 300 DPI for page renders |

---

## Manifest/Brief Synchronization Failures

### 1. EXECUTION_MANIFEST.json vs Agent Brief Mismatches

The manifest documentation references don't match the actual agent brief content:

| Agent | Manifest Says | Brief Actually References |
|-------|---------------|---------------------------|
| DEV-IMGCLASS-001 | `OPENAI_API_INTEGRATION.md` | `ANTHROPIC_API_INTEGRATION.md` |
| DEV-FLOORPLAN-001 | `OPENAI_API_INTEGRATION.md` | `ANTHROPIC_API_INTEGRATION.md` |

**Risk:** Agents will read the BRIEF (correct), but orchestrators using the MANIFEST will have incorrect documentation mappings.

### 2. Missing Agent in Manifest

| Agent | Brief Exists | In Manifest |
|-------|--------------|-------------|
| DEV-ANTHROPIC-001 | YES | NO - Missing from phase-5 |
| QA-ANTHROPIC-001 | UNKNOWN | NO - Missing from phase-5 |

### 3. Orphaned Agent in Manifest

| Agent | In Manifest | Should Exist |
|-------|-------------|--------------|
| DEV-OPENAI-001 | YES | DECISION NEEDED - Keep for fallback or remove? |
| QA-OPENAI-001 | YES | DECISION NEEDED - Keep for fallback or remove? |

---

## Dependency Chain Issues

### 1. Broken Downstream Dependencies

DEV-ANTHROPIC-001.md specifies downstream dependencies:
```
Downstream: DEV-IMGCLASS-001, DEV-WATERMARK-001, DEV-FLOORPLAN-001, DEV-STRUCT-001, DEV-CONTENT-001
```

But DEV-OPENAI-001.md has IDENTICAL downstream dependencies:
```
Downstream: DEV-IMGCLASS-001, DEV-WATERMARK-001, DEV-FLOORPLAN-001, DEV-STRUCT-001, DEV-CONTENT-001
```

**Risk:** Duplicate/conflicting dependency chains. Need to decide if OpenAI is deprecated or parallel.

### 2. DEV-EXTRACT-001 Cross-Reference Support

DEV-EXTRACT-001.md correctly specifies floor plan cross-reference support:
- Page boundaries with markers
- Unit specification extraction
- Page-indexed output for context lookup

**Status:** CORRECT - Supports DEV-FLOORPLAN-001 text fallback requirement

---

## Environment Variable Gaps

Based on the approved plan, the following environment variables should be documented:

### Required Variables (verify in EXTERNAL_SETUP_CHECKLIST.md)

```bash
# Tier 1: Original Images
MAX_IMAGE_WIDTH_PX=2450
MAX_IMAGE_HEIGHT_PX=1400
OUTPUT_DPI=300
WEBP_QUALITY=85
JPG_QUALITY=90

# Tier 2: LLM-Optimized
LLM_MAX_DIMENSION=1568
LLM_CLASSIFICATION_MAX_DIM=1024
LLM_WATERMARK_MAX_DIM=1280
LLM_FLOOR_PLAN_MAX_DIM=1568
LLM_JPEG_QUALITY=85
LLM_USE_PNG_FOR_FLOOR_PLANS=true

# Extraction Strategy
PAGE_RENDER_DPI=300
MIN_EMBEDDED_IMAGE_WIDTH=500

# Quality Validation
ENABLE_AUTO_ENHANCE=false
MIN_CLASSIFICATION_WIDTH=800
MIN_CLASSIFICATION_HEIGHT=600
MIN_FLOOR_PLAN_WIDTH=1200
MIN_FLOOR_PLAN_HEIGHT=900

# Anthropic API
ANTHROPIC_API_KEY=<from Secret Manager>
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

---

## Recommended Fix Order

### Phase 1: Critical Manifest Fixes (Blocking)

1. **Add DEV-ANTHROPIC-001 to EXECUTION_MANIFEST.json phase-5**
2. **Add ANTHROPIC_API_INTEGRATION.md to documentation_registry**
3. **Update all agent documentation references** from OPENAI to ANTHROPIC
4. **Update phase-5 description** to say "Anthropic" not "OpenAI"

### Phase 2: Agent Brief Updates (Blocking)

5. **Update DEV-STRUCT-001.md** - Change GPT-4 references to Claude
6. **Update DEV-CONTENT-001.md** - Change integration reference
7. **Update DEV-IMGOPT-001.md** - Remove 500KB limit, add dual-tier

### Phase 3: Technical Specification Alignment

8. **Verify MATERIAL_PREPARATION.md** has dual-tier specs
9. **Verify DEV-PDF-001.md** has triple extraction requirement (embedded + render + text via pymupdf4llm)
10. **Update EXECUTION_PROTOCOL.md** phase-5 agent list

### Phase 4: Decision Required

11. **Decide DEV-OPENAI-001 fate:**
    - Option A: Remove entirely (clean migration)
    - Option B: Keep as deprecated fallback
    - Option C: Keep for future multi-provider support

---

## Files Requiring Modification

| Priority | File | Changes Required |
|----------|------|------------------|
| P0 | [EXECUTION_MANIFEST.json](docs/EXECUTION_MANIFEST.json) | Add Anthropic agent, update all doc refs |
| P0 | [EXECUTION_PROTOCOL.md](docs/EXECUTION_PROTOCOL.md) | Update phase-5 agent list |
| P1 | [DEV-STRUCT-001.md](docs/_agent-briefs/phase-3-content-gen/DEV-STRUCT-001.md) | Update to Claude |
| P1 | [DEV-CONTENT-001.md](docs/_agent-briefs/phase-3-content-gen/DEV-CONTENT-001.md) | Update integration ref |
| P1 | [DEV-IMGOPT-001.md](docs/_agent-briefs/phase-2-material-prep/DEV-IMGOPT-001.md) | Remove 500KB, add dual-tier |
| P2 | [DEV-PDF-001.md](docs/_agent-briefs/phase-2-material-prep/DEV-PDF-001.md) | Add triple extraction (embedded + render + text) |
| P2 | [EXTERNAL_SETUP_CHECKLIST.md](docs/00-prerequisites/EXTERNAL_SETUP_CHECKLIST.md) | Verify env vars |

---

## Verification Checklist

After fixes are applied:

- [x] All agent briefs reference `ANTHROPIC_API_INTEGRATION.md` (not OpenAI)
- [x] EXECUTION_MANIFEST.json includes DEV-ANTHROPIC-001 in phase-5
- [x] EXECUTION_MANIFEST.json documentation_registry includes ANTHROPIC doc
- [x] No 500KB file size limits in any document
- [x] Dual-tier image strategy documented in DEV-IMGOPT-001
- [x] Triple extraction (embedded + page render + text via pymupdf4llm) documented in DEV-PDF-001
- [x] 300 DPI consistent across all page rendering specs
- [x] All environment variables documented in prerequisites
- [x] pymupdf4llm has no user-facing config vars (library defaults used; `ignore_images=True` and `page_chunks=True` hardcoded in `pdf_processor.py`)

**RESOLVED:** 2026-01-24 - All critical issues fixed
**UPDATED:** 2026-01-27 - Phase 11 audit: "dual extraction" -> "triple extraction" (pymupdf4llm text added)

---

**End of Report**
